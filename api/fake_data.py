"""Faz 1 sahte verisi + saf filtre/sayfalama mantığı.

Veri henüz DB'den gelmiyor (Faz 3'te bağlanacak). Ama yanıt modelleri ve
`select_businesses` imzası gerçek: DB'ye geçerken HTTP yüzeyi değişmeyecek.

`select_businesses` saf bir fonksiyondur — httpx/SQLAlchemy dokunmaz, liste alır
liste döndürür — böylece filtre/sayfalama mantığı DB olmadan test edilebilir
(CLAUDE.md mimari kuralı).
"""

from datetime import UTC, datetime

from api.schemas import Business, Stats, TriageStatus


def _dt(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=UTC)


# Samsun işletmelerinden temsili bir küme. Durum/skor/kategori çeşitliliği bilinçli:
# filtrelerin gerçekten daralttığını ve boş-durumun mümkün olduğunu gösterir.
FAKE_BUSINESSES: list[Business] = [
    Business(
        id=1,
        place_id="ChIJ_atakum_dis",
        name="Atakum Diş Kliniği",
        category="klinik",
        address="Atakum, Samsun",
        phone="+90 362 000 0001",
        website="https://atakumdis.example",
        ig_handle="atakumdisklinigi",
        rating_count=214,
        discovered_at=_dt(2026, 7, 10),
        score=82.4,
        status=TriageStatus.QUALIFIED,
    ),
    Business(
        id=2,
        place_id="ChIJ_elmas_kuyum",
        name="Elmas Kuyumculuk",
        category="kuyumcu",
        address="İlkadım, Samsun",
        phone="+90 362 000 0002",
        website="https://elmaskuyum.example",
        ig_handle="elmaskuyumculuk",
        rating_count=97,
        discovered_at=_dt(2026, 7, 11),
        score=74.1,
        status=TriageStatus.QUALIFIED,
    ),
    Business(
        id=3,
        place_id="ChIJ_karadeniz_oto",
        name="Karadeniz Oto Galeri",
        category="oto galeri",
        address="Canik, Samsun",
        phone="+90 362 000 0003",
        website=None,
        ig_handle="karadenizotogaleri",
        rating_count=41,
        discovered_at=_dt(2026, 7, 12),
        score=58.0,
        status=TriageStatus.WATCH,
    ),
    Business(
        id=4,
        place_id="ChIJ_bahcelievler_emlak",
        name="Bahçelievler Emlak",
        category="emlak",
        address="İlkadım, Samsun",
        phone="+90 362 000 0004",
        website="https://bahcelievleremlak.example",
        ig_handle="bahcelievleremlak",
        rating_count=63,
        discovered_at=_dt(2026, 7, 12),
        score=61.5,
        status=TriageStatus.WATCH,
    ),
    Business(
        id=5,
        place_id="ChIJ_sahil_kafe",
        name="Sahil Kafe",
        category="kafe",
        address="Atakum, Samsun",
        phone="+90 362 000 0005",
        website=None,
        ig_handle="sahilkafesamsun",
        rating_count=302,
        discovered_at=_dt(2026, 7, 13),
        score=31.2,
        status=TriageStatus.REJECTED,
    ),
    Business(
        id=6,
        place_id="ChIJ_nostalji_kuafor",
        name="Nostalji Kuaför",
        category="kuaför",
        address="Canik, Samsun",
        phone=None,
        website=None,
        ig_handle="nostaljikuafor",
        rating_count=18,
        discovered_at=_dt(2026, 7, 14),
        score=22.8,
        status=TriageStatus.REJECTED,
    ),
    # Kohort 5 hesabın altında → potansiyel hesaplanamadı, skor yok, hesap watch
    # (SPEC §4). Skoru null ama durumu var: panelde "—" + status etiketi.
    Business(
        id=7,
        place_id="ChIJ_piano_cafe",
        name="Piano Cafe",
        category="kafe",
        address="Atakum, Samsun",
        phone="+90 362 000 0007",
        website=None,
        ig_handle="pianocafesamsun",
        rating_count=12,
        discovered_at=_dt(2026, 7, 15),
        score=None,
        status=TriageStatus.WATCH,
    ),
    # Henüz triyajlanmamış: skor ve durum null, IG eşlemesi de yok.
    Business(
        id=8,
        place_id="ChIJ_yeni_pastane",
        name="Yeni Açılan Pastane",
        category="pastane",
        address="İlkadım, Samsun",
        phone="+90 362 000 0008",
        website=None,
        ig_handle=None,
        rating_count=None,
        discovered_at=_dt(2026, 7, 20),
        score=None,
        status=None,
    ),
]


def _matches(
    business: Business,
    *,
    status: TriageStatus | None,
    category: str | None,
    min_score: float | None,
) -> bool:
    if status is not None and business.status != status:
        return False
    if category is not None and business.category != category:
        return False
    # Skoru olmayan kayıt bir eşikle karşılaştırılamaz → elenir (sözleşme: "Skoru
    # olmayan kayıtlar da elenir").
    return min_score is None or (business.score is not None and business.score >= min_score)


def select_businesses(
    items: list[Business],
    *,
    status: TriageStatus | None = None,
    category: str | None = None,
    min_score: float | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Business], int]:
    """Filtreler, sonra sayfalar. `(sayfa, filtrelenmiş_toplam)` döndürür.

    `total` sayfalama öncesi filtrelenmiş toplamdır — sözleşme böyle tanımlıyor.
    """
    filtered = [
        b for b in items if _matches(b, status=status, category=category, min_score=min_score)
    ]
    page = filtered[offset : offset + limit]
    return page, len(filtered)


def build_stats(items: list[Business]) -> Stats:
    """Sahte panel sayaçları. `scanned`/`qualified` sahte listeyle tutarlı türetilir;
    `reports` ve `monthly_cost_usd` Faz 1'de sabit yer tutucu (rapor/LLM katmanı yok).
    """
    scanned = sum(1 for b in items if b.status is not None)
    qualified = sum(1 for b in items if b.status is TriageStatus.QUALIFIED)
    return Stats(
        scanned=scanned,
        qualified=qualified,
        reports=3,
        monthly_cost_usd=4.62,
    )
