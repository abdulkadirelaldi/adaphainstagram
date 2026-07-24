"""SPEC §3 veri modeli — altı tablo.

SQLAlchemy 2.0 modern stil: `Mapped[]` + `mapped_column()`. Legacy `Column()` yok.

Tasarım kararları:
- `status` alanları veritabanı seviyesinde **CHECK constraint** ile zorlanır
  (`Enum(..., native_enum=False)`), native PG ENUM tipiyle değil. Gerekçe `tables.py`
  altındaki `docs/TASKS.md` kapanış notunda; özeti: CHECK, autogenerate ve downgrade'de
  ayrı bir tip nesnesi bırakmadığı için geri alınabilirliği temiz tutar, Python tarafında
  `Mapped[TriageStatus]` tiplemesini yine de korur.
- Para (`audits.llm_cost_usd`) ve skorlar `Numeric`; kayan nokta yuvarlama hatası
  maliyet ve skor karşılaştırmalarını kirletmesin.
- Tüm zaman damgaları `TIMESTAMP WITH TIME ZONE`, veritabanı `now()` varsayılanıyla.
- Yasak metrik yok (CLAUDE.md kural 7): `posts` yalnızca SPEC §3'teki `like_count`,
  `comment_count`, `view_count` alanlarını taşır. Erişim/gösterim/kaydetme/profil
  ziyareti/demografi ne burada ne başka tabloda.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base
from api.models.enums import OutreachStatus, TriageStatus

# 0–100 skorları için ortak tip: 0.00–100.00.
Score = Numeric(5, 2)


def _status_enum(enum_cls: type[StrEnum], name: str) -> Enum:
    """CHECK-constraint'li enum kolonu (native PG tipi değil).

    `values_callable` kritik: onsuz SQLAlchemy üye **adını** ('DRAFT') saklar; biz
    SPEC §3 ve `docs/openapi.yaml`'daki küçük harf **değeri** ('draft') istiyoruz.
    Aksi halde `server_default='draft'` CHECK'i ihlal ederdi.
    """
    return Enum(
        enum_cls,
        native_enum=False,
        length=16,
        name=name,
        values_callable=lambda e: [member.value for member in e],
    )


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    place_id: Mapped[str] = mapped_column(String(128), unique=True)
    name: Mapped[str] = mapped_column(String(512))
    category: Mapped[str | None] = mapped_column(String(256))
    address: Mapped[str | None] = mapped_column(String(1024))
    phone: Mapped[str | None] = mapped_column(String(64))
    website: Mapped[str | None] = mapped_column(String(1024))
    # ig_handle sonradan eşlenir (SPEC §1); eşlenene kadar null. Eşlendiğinde benzersiz.
    ig_handle: Mapped[str | None] = mapped_column(String(128), unique=True)
    rating_count: Mapped[int | None] = mapped_column(Integer)
    # 180 günlük silme (CLAUDE.md, Faz 6 cron) bu alana dayanır — indeksli.
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    snapshots: Mapped[list["Snapshot"]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )
    triage_scores: Mapped[list["TriageScore"]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )
    audits: Mapped[list["Audit"]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("businesses.id", ondelete="CASCADE"), index=True
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Hangi adaptörden geldi: places | business_discovery | apify (SPEC §2). Kaynak
    # kümesi Faz 2'de genişleyebileceğinden veritabanı seviyesinde kısıtlanmadı.
    source: Mapped[str] = mapped_column(String(64))
    followers: Mapped[int | None] = mapped_column(Integer)
    follows: Mapped[int | None] = mapped_column(Integer)
    media_count: Mapped[int | None] = mapped_column(Integer)
    biography: Mapped[str | None] = mapped_column(Text)
    external_url: Mapped[str | None] = mapped_column(String(1024))
    is_professional: Mapped[bool | None] = mapped_column(Boolean)
    # Adaptörün ham yanıtı; normalize edilmemiş kaynak. Denetim izi için saklanır.
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB)

    business: Mapped["Business"] = relationship(back_populates="snapshots")
    posts: Mapped[list["Post"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("snapshots.id", ondelete="CASCADE"), index=True
    )
    ig_id: Mapped[str] = mapped_column(String(128))
    media_type: Mapped[str | None] = mapped_column(String(32))
    caption: Mapped[str | None] = mapped_column(Text)
    like_count: Mapped[int | None] = mapped_column(Integer)
    comment_count: Mapped[int | None] = mapped_column(Integer)
    # view_count yalnızca videolarda dolar; diğer medyada null.
    view_count: Mapped[int | None] = mapped_column(Integer)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    permalink: Mapped[str | None] = mapped_column(String(1024))
    thumb_url: Mapped[str | None] = mapped_column(String(1024))

    snapshot: Mapped["Snapshot"] = relationship(back_populates="posts")


class TriageScore(Base):
    __tablename__ = "triage_scores"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("businesses.id", ondelete="CASCADE"), index=True
    )
    # Hangi snapshot skorlandı — skor izlenebilir olsun.
    snapshot_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("snapshots.id", ondelete="CASCADE")
    )
    # Alt skorlar SPEC §4. activity ve capacity daima hesaplanır.
    activity: Mapped[float] = mapped_column(Score)
    capacity: Mapped[float] = mapped_column(Score)
    # Kohort 5 hesabın altındaysa potansiyel hesaplanmaz (SPEC §4) → null, hesap watch.
    potential: Mapped[float | None] = mapped_column(Score)
    # Birleşik skor ağırlıklı çarpım (SPEC §4); potansiyel null ise hesaplanamaz → null.
    score: Mapped[float | None] = mapped_column(Score)
    status: Mapped[TriageStatus] = mapped_column(_status_enum(TriageStatus, "triage_status"))
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    business: Mapped["Business"] = relationship(back_populates="triage_scores")


class Audit(Base):
    __tablename__ = "audits"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("businesses.id", ondelete="CASCADE"), index=True
    )
    visibility_score: Mapped[float] = mapped_column(Score)
    # Deterministik kurallardan doğan bulgu **listesi** (SPEC §5). LLM bulgu icat etmez.
    findings: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    pdf_path: Mapped[str | None] = mapped_column(String(1024))
    # CLAUDE.md maliyet disiplini: bu alan boş kalamaz. NOT NULL, Numeric (Float değil);
    # mikro-dolar hassasiyeti için ölçek 6.
    llm_cost_usd: Mapped[float] = mapped_column(Numeric(10, 6))
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    business: Mapped["Business"] = relationship(back_populates="audits")
    outreach: Mapped[list["Outreach"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )


class Outreach(Base):
    __tablename__ = "outreach"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    audit_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("audits.id", ondelete="CASCADE"), index=True
    )
    channel: Mapped[str] = mapped_column(String(64))
    # Üretilen mesaj taslağının metni.
    draft: Mapped[str] = mapped_column(Text)
    # CLAUDE.md hukuki sınırlar: kayıt daima `draft` doğar. Bu bir VERİTABANI
    # varsayılanı — durum verilmeden eklenen satır otomatik `draft` olur, kod yolu
    # atlansa bile.
    status: Mapped[OutreachStatus] = mapped_column(
        _status_enum(OutreachStatus, "outreach_status"),
        server_default=OutreachStatus.DRAFT.value,
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    audit: Mapped["Audit"] = relationship(back_populates="outreach")
