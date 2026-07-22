"""Persist katmanı — normalize çıktıyı veritabanına yazar.

Adaptörler dış dünyayı (HTTP + normalize) bilir ama SQLAlchemy'yi bilmez; bu katman
tersidir: `Normalized*` Pydantic modellerini alır, ORM modellerine yazar. Ayrım
sayesinde normalize mantığı DB olmadan, persist mantığı HTTP olmadan test edilir.
"""

from api.persistence.businesses import upsert_businesses

__all__ = ["upsert_businesses"]
