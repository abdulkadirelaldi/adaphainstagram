"""Alan değer kümeleri — SPEC §3.

`StrEnum` bilinçli: değerler veritabanında düz metin olarak durur (native PG enum
değil, CHECK constraint ile — bkz. `tables.py`), Python tarafında da string gibi
karşılaştırılabilir olsun.
"""

from enum import StrEnum


class TriageStatus(StrEnum):
    """Triyaj sonucu. Değerler SPEC §3 ve `docs/openapi.yaml` ile birebir aynı."""

    QUALIFIED = "qualified"
    WATCH = "watch"
    REJECTED = "rejected"


class OutreachStatus(StrEnum):
    """Erişim kaydının durumu. `draft` başlangıç durumudur.

    CLAUDE.md hukuki sınırlar: sistem hiçbir koşulda otomatik mesaj göndermez;
    kayıt `draft` doğar, ileri durumlara yalnızca insan kararıyla geçer.
    """

    DRAFT = "draft"
    SENT = "sent"
    OPENED = "opened"
    REPLIED = "replied"
    MEETING = "meeting"
    WON = "won"
    LOST = "lost"
