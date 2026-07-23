"""Saf iş mantığı katmanı.

CLAUDE.md mimari kuralı: bu katman httpx veya SQLAlchemy import etmez — sözlük/
dataclass alır, sözlük/dataclass döndürür. DB'ye dokunmadan test edilebilir.
"""

from api.core.handle import extract_ig_handle

__all__ = ["extract_ig_handle"]
