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
from api.services.retention import PurgeSummary, purge_old_candidates

__all__ = [
    "DiscoverySummary",
    "NotAuditableError",
    "PurgeSummary",
    "assert_auditable",
    "fetch_profile",
    "purge_old_candidates",
    "run_audit",
    "run_discovery",
]
