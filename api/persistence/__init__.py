"""Persist katmanı — normalize çıktıyı veritabanına yazar.

Adaptörler dış dünyayı (HTTP + normalize) bilir ama SQLAlchemy'yi bilmez; bu katman
tersidir: `Normalized*` Pydantic modellerini alır, ORM modellerine yazar. Ayrım
sayesinde normalize mantığı DB olmadan, persist mantığı HTTP olmadan test edilir.
"""

from api.persistence.audits import get_audit, persist_audit
from api.persistence.businesses import (
    place_id_to_id,
    set_ig_handle,
    upsert_businesses,
)
from api.persistence.profiles import persist_profile

__all__ = [
    "get_audit",
    "persist_audit",
    "persist_profile",
    "place_id_to_id",
    "set_ig_handle",
    "upsert_businesses",
]
