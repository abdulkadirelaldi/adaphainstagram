"""SEC-5 entegrasyon testleri için sahte HTTP client'ları ve çağrı sayacı.

BE-9'un `api/discover_demo.py`'daki desenini yansıtır: adaptörlere fixture yanıtı
veren `httpx.MockTransport` client'ları. **Canlı çağrı yok** (CLAUDE.md kural 6) —
`conftest.py` ağ muhafızı altında da geçer, çünkü MockTransport soket açmaz.

Çağrı sayacı cache denetiminin çekirdeğidir: ikinci koşuda profil client'ının
sayacı 0 kalmalı (dış çağrı yapılmadı).
"""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

# BD adaptörü Graph API `fields` parametresine `business_discovery.username(<handle>)`
# gömer; sahte client handle'ı buradan çıkarıp doğru profili döndürür.
_USERNAME_RE = re.compile(r"username\(([^)]+)\)")


class CallCounter:
    """Bir sahte client'a giden istekleri sayar."""

    def __init__(self) -> None:
        self.count = 0

    def reset(self) -> None:
        self.count = 0


def places_client(raw: dict[str, Any], counter: CallCounter) -> httpx.AsyncClient:
    """Her POST'ta aynı ham Places yanıtını döndürür."""

    def handler(_: httpx.Request) -> httpx.Response:
        counter.count += 1
        return httpx.Response(200, json=raw)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def bd_client(profiles: dict[str, Any], counter: CallCounter) -> httpx.AsyncClient:
    """`fields` param'ından handle çıkarır; `profiles[handle]` döndürür (yoksa `{}`)."""

    def handler(request: httpx.Request) -> httpx.Response:
        counter.count += 1
        match = _USERNAME_RE.search(request.url.params.get("fields", ""))
        handle = match.group(1) if match else ""
        # Boş {} → normalize ProfileUnavailableError → fallback (SPEC §2).
        return httpx.Response(200, json=profiles.get(handle, {}))

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def bd_error_client(status_code: int, counter: CallCounter) -> httpx.AsyncClient:
    """Her istekte HTTP hata durum kodu döndürür (ağ/servis hatasını taklit eder)."""

    def handler(_: httpx.Request) -> httpx.Response:
        counter.count += 1
        return httpx.Response(status_code, json={"error": "sahte sunucu hatası"})

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def apify_client(profiles: dict[str, Any], counter: CallCounter) -> httpx.AsyncClient:
    """POST gövdesindeki `usernames[0]`'a göre profil döndürür (yoksa boş liste)."""

    def handler(request: httpx.Request) -> httpx.Response:
        counter.count += 1
        payload = json.loads(request.content)
        handle = payload["usernames"][0]
        item = profiles.get(handle)
        return httpx.Response(200, json=[item] if item is not None else [])

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))
