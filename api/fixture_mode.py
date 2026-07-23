"""Fixture modu — worker/demo için sahte HTTP client'lı adaptörler.

`RADAR_FIXTURE_MODE` açıkken worker keşif job'unu canlı Places/IG/Apify yerine
`tests/fixtures/` yanıtlarıyla yürütür (kural 6). Böylece gerçek anahtar olmadan,
gerçek arq worker + durum makinesi (queued→running→done) fixture'la uçtan uca test
edilir. Fixture'lar **tek kaynak** `tests/fixtures/`; bu modül yalnız **okur**.

MockTransport client'ları bellekte çalışır — ağ yok, kural 6 garanti.
"""

import json
import re
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx

from api.adapters.apify import ApifyAdapter
from api.adapters.business_discovery import BusinessDiscoveryAdapter
from api.adapters.places import PlacesAdapter

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
_USERNAME_RE = re.compile(r"username\(([^)]+)\)")

# Çağrı kancası: her sahte istekte çağrılır (demo çağrı sayacı için). None ise yok.
OnCall = Callable[[], None] | None


def load_fixture(name: str) -> Any:
    """`tests/fixtures/{name}` JSON'unu okur."""
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def make_places_client(raw: dict[str, Any], on_call: OnCall = None) -> httpx.AsyncClient:
    def handler(_: httpx.Request) -> httpx.Response:
        if on_call is not None:
            on_call()
        return httpx.Response(200, json=raw)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def make_bd_client(profiles: dict[str, Any], on_call: OnCall = None) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if on_call is not None:
            on_call()
        match = _USERNAME_RE.search(request.url.params.get("fields", ""))
        handle = match.group(1) if match else ""
        # profiles[handle] boş {} olabilir → normalize ProfileUnavailableError → fallback.
        return httpx.Response(200, json=profiles.get(handle, {}))

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def make_apify_client(profiles: dict[str, Any], on_call: OnCall = None) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if on_call is not None:
            on_call()
        payload = json.loads(request.content)
        handle = payload["usernames"][0]
        item = profiles.get(handle)
        return httpx.Response(200, json=[item] if item is not None else [])

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@asynccontextmanager
async def fixture_adapters() -> AsyncIterator[
    tuple[PlacesAdapter, BusinessDiscoveryAdapter, ApifyAdapter]
]:
    """Fixture-besleyen üç adaptörü verir; çıkışta sahte client'ları kapatır.

    Worker fixture modunda bunu `run_discovery`'ye geçer — akış canlı yolla birebir,
    yalnız HTTP kaynağı fixture.
    """
    places_raw = load_fixture("places_response.json")
    bd_profiles = load_fixture("ig_business_discovery.json")["profiles"]
    apify_profiles = load_fixture("apify_profile.json")["profiles"]

    places_client = make_places_client(places_raw)
    bd_client = make_bd_client(bd_profiles)
    apify_client = make_apify_client(apify_profiles)
    try:
        yield (
            PlacesAdapter(client=places_client),
            BusinessDiscoveryAdapter(client=bd_client),
            ApifyAdapter(client=apify_client),
        )
    finally:
        await places_client.aclose()
        await bd_client.aclose()
        await apify_client.aclose()
