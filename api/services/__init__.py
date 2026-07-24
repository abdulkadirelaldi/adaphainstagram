"""Servis katmanı — birden çok adaptörü/persist'i koordine eden kullanım senaryoları.

Adaptörler tek kaynağı bilir, persist tek tabloyu; orkestrasyon (ör. profil çekiminde
Business Discovery → Apify fallback) buraya düşer.
"""

from api.services.audit import (
    NotAuditableError,
    assert_auditable,
    run_audit,
)
from api.services.discovery import DiscoverySummary, run_discovery
from api.services.profile import fetch_profile

__all__ = [
    "DiscoverySummary",
    "NotAuditableError",
    "assert_auditable",
    "fetch_profile",
    "run_audit",
    "run_discovery",
]
