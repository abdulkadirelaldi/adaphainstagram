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
    "ComponentStatus",
    "DiscoveryRequest",
    "Finding",
    "Health",
    "JobAccepted",
    "JobProgress",
    "JobResult",
    "JobState",
    "JobStatus",
    "OutreachDraft",
    "OutreachStatus",
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
