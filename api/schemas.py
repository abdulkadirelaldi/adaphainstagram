"""HTTP yanıt şemaları.

Bu modül `docs/openapi.yaml` sözleşmesinin Python karşılığıdır. Sözleşme kaynaktır:
buradaki bir alan değişecekse önce o dosya güncellenir (CLAUDE.md kural 3).
"""

from datetime import datetime
from enum import Enum, StrEnum

from pydantic import BaseModel, ConfigDict, Field

# Enum'lar tek kaynaktan gelir: değer kümeleri hem veritabanı modelinde hem burada
# aynı olmalı. `api.models.enums` yalnızca StrEnum'a dayanır (SQLAlchemy çekmez), bu
# yüzden HTTP katmanına güvenle import edilir.
from api.models.enums import OutreachStatus, Severity, TriageStatus

__all__ = [
    "Audit",
    "Business",
    "BusinessList",
    "CategoryCohort",
    "CategoryCohortList",
    "ComponentStatus",
    "DiscoveryRequest",
    "Finding",
    "Health",
    "JobAccepted",
    "JobProgress",
    "JobResult",
    "JobState",
    "JobStatus",
    "Outreach",
    "OutreachDraft",
    "OutreachStatus",
    "OutreachUpdate",
    "Severity",
    "Stats",
    "TriageStatus",
]


class ComponentStatus(str, Enum):
    """Tek bir bileşenin sağlık durumu."""

    OK = "ok"
    ERROR = "error"


class Health(BaseModel):
    """`GET /health` yanıtı."""

    model_config = ConfigDict(extra="forbid")

    status: ComponentStatus
    db: ComponentStatus
    redis: ComponentStatus

    @property
    def is_healthy(self) -> bool:
        return self.status is ComponentStatus.OK


class Stats(BaseModel):
    """`GET /stats` yanıtı — panel üst şeridi (SPEC §7)."""

    model_config = ConfigDict(extra="forbid")

    scanned: int = Field(ge=0, description="Triyajı yapılmış işletme sayısı.")
    qualified: int = Field(ge=0, description="Durumu `qualified` olan işletme sayısı.")
    reports: int = Field(ge=0, description="Üretilmiş denetim raporu sayısı.")
    monthly_cost_usd: float = Field(
        ge=0,
        description="İçinde bulunulan takvim ayının gerçekleşen LLM maliyeti (USD).",
    )
    # Faz 6 maliyet alarmı. Opsiyonel + varsayılanlı → geriye uyumlu (BE-21 sözleşmesi).
    monthly_cost_alarm: bool = Field(
        default=False, description="Aylık maliyet eşiği aşıldı mı (SPEC §8)."
    )
    monthly_cost_limit_usd: float | None = Field(
        default=None, ge=0, description="Yapılandırılmış aylık maliyet eşiği (USD); yoksa null."
    )


class CategoryCohort(BaseModel):
    """Tek kategori için kohort istatistiği (SPEC §4). Yalnız skor/etkileşim dağılımı."""

    model_config = ConfigDict(extra="forbid")

    category: str
    scanned: int = Field(ge=0, description="Kategoride skorlanmış hesap sayısı.")
    score_median: float | None = Field(ge=0, le=100)
    score_q1: float | None = Field(ge=0, le=100)
    score_q3: float | None = Field(ge=0, le=100)
    engagement_median: float | None = Field(
        ge=0, description="Etkileşim kohort medyanı (SPEC §4); kohort<5 → null."
    )


class CategoryCohortList(BaseModel):
    """`GET /stats/categories` yanıtı."""

    model_config = ConfigDict(extra="forbid")

    items: list[CategoryCohort]


class Business(BaseModel):
    """`businesses` tablosundan türer + son triyajın `score`/`status` alanları.

    Alanlar `docs/openapi.yaml` `Business` şemasıyla birebir; nullable olanlar açıkça
    `| None`, hepsi zorunlu (Pydantic'te varsayılan verilmediği için required kalır).
    """

    model_config = ConfigDict(extra="forbid")

    id: int
    place_id: str
    name: str
    category: str | None
    address: str | None
    phone: str | None
    website: str | None
    ig_handle: str | None
    # Field(...) default vermez → alan required kalır (sözleşmedeki required listesiyle
    # birebir), ama yine de null olabilir. Sayısal kısıt yalnızca non-null değere uygulanır.
    rating_count: int | None = Field(ge=0)
    discovered_at: datetime
    score: float | None = Field(ge=0, le=100)
    status: TriageStatus | None


class BusinessList(BaseModel):
    """`GET /businesses` yanıtı — sayfalanmış liste."""

    model_config = ConfigDict(extra="forbid")

    items: list[Business]
    total: int = Field(ge=0, description="Filtreye uyan, sayfalama öncesi toplam kayıt.")


class DiscoveryRequest(BaseModel):
    """`POST /discovery/run` istek gövdesi."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, description="Places arama sorgusu.")
    region: str = Field(default="Samsun", min_length=1, description="Aranan bölge.")
    limit: int | None = Field(default=None, ge=1, le=200, description="En fazla işletme.")


class JobAccepted(BaseModel):
    """`POST /discovery/run` yanıtı — kuyruğa alınan işin kimliği."""

    model_config = ConfigDict(extra="forbid")

    job_id: str


class JobState(StrEnum):
    """Kuyruk işinin yaşam döngüsü (sözleşme `JobState`)."""

    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class JobProgress(BaseModel):
    """İşin ilerleme sayaçları."""

    model_config = ConfigDict(extra="forbid")

    processed: int = Field(ge=0, description="İşlenen öğe sayısı.")
    total: int | None = Field(ge=0, description="Beklenen toplam; bilinmiyorsa null.")


class JobResult(BaseModel):
    """İş tamamlandığında yazılanların özeti."""

    model_config = ConfigDict(extra="forbid")

    businesses: int = Field(ge=0, description="Yazılan/güncellenen işletme sayısı (keşif).")
    snapshots: int = Field(ge=0, description="Alınan snapshot sayısı (keşif).")
    audit_id: int | None = Field(
        description="Üretilen denetim kimliği (denetim işi); keşifte null."
    )


class JobStatus(BaseModel):
    """`GET /jobs/{id}` yanıtı."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: JobState
    progress: JobProgress | None
    result: JobResult | None
    error: str | None


class Finding(BaseModel):
    """Deterministik denetim bulgusu (SPEC §5). `message` LLM'e ait (BE-16)."""

    model_config = ConfigDict(extra="forbid")

    rule: str = Field(description="Kural makine kimliği, ör. `reels_yok`.")
    title: str = Field(description="Kuralın insan okunur adı.")
    severity: Severity
    detail: str = Field(description="Deterministik tetik açıklaması (ölçülen değer + eşik).")
    message: str | None = Field(description="LLM'in ürettiği ajans-dili metni; sentez öncesi null.")


class OutreachDraft(BaseModel):
    """Denetime bağlı erişim mesajı taslağının özeti (SPEC §3 `outreach`)."""

    model_config = ConfigDict(extra="forbid")

    id: int
    channel: str = Field(description="İletişim kanalı, ör. `instagram_dm`.")
    draft: str = Field(description="Üretilen mesaj taslağının metni.")
    status: OutreachStatus


class Outreach(BaseModel):
    """`PATCH /outreach/{id}` yanıtı — tam erişim kaydı (SPEC §3). Eylem/gönderme alanı yok."""

    model_config = ConfigDict(extra="forbid")

    id: int
    audit_id: int
    channel: str = Field(description="İletişim kanalı, ör. `instagram_dm`.")
    draft: str = Field(description="Üretilen mesaj taslağının metni (BE-16).")
    status: OutreachStatus
    sent_at: datetime | None = Field(description="`sent`'e geçince damgalanır; öncesinde null.")
    replied_at: datetime | None = Field(
        description="`replied`'a geçince damgalanır; öncesinde null."
    )


class OutreachUpdate(BaseModel):
    """`PATCH /outreach/{id}` istek gövdesi — YALNIZCA yeni durum.

    Gönderme/kanal-tetikleme alanı bilinçle yok; `extra="forbid"` bunu yapısal
    garanti eder. Bu uç mesaj göndermez, insan kararını kaydeder (CLAUDE.md hukuki sınır).
    """

    model_config = ConfigDict(extra="forbid")

    status: OutreachStatus


class Audit(BaseModel):
    """`GET /audits/{id}` yanıtı — bir derin denetimin sonucu (SPEC §3 `audits` + §5)."""

    model_config = ConfigDict(extra="forbid")

    id: int
    business_id: int
    visibility_score: float = Field(ge=0, le=100)
    findings: list[Finding]
    report_text: str | None = Field(description="LLM rapor metni; sentez tamamlanana kadar null.")
    pdf_path: str | None = Field(description="PDF raporunun yolu; PDF Faz 5, o zamana kadar null.")
    llm_cost_usd: float = Field(ge=0, description="Denetimin gerçek LLM maliyeti (USD).")
    generated_at: datetime
    outreach: OutreachDraft | None = Field(description="Erişim taslağı; üretilene kadar null.")
