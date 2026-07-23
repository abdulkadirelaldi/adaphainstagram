"""Servis katmanı — birden çok adaptörü/persist'i koordine eden kullanım senaryoları.

Adaptörler tek kaynağı bilir, persist tek tabloyu; orkestrasyon (ör. profil çekiminde
Business Discovery → Apify fallback) buraya düşer.
"""

from api.services.profile import fetch_profile

__all__ = ["fetch_profile"]
