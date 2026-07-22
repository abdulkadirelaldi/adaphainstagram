// FE-3'te üretilen tiplerle değiştirilecek.
//
// Bu dosya FE-2'nin GEÇİCİ veri kaynağıdır. Yerel tipler `docs/openapi.yaml`'daki
// `Business`, `Stats`, `BusinessList` şemalarının şeklini taşır ama elle üretilmiş
// SÖZLEŞME DEĞİLDİR — FE-3'te openapi-typescript çıktısıyla tek yerden sökülür.
// Bileşenler yalnızca bu dosyanın dışa verdiği tipleri ve sorguyu tüketir; gerçek
// istek gelince yalnızca burası değişir.
//
// CLAUDE.md kural 7: erişim, gösterim, kaydetme, profil ziyareti, demografi
// alanları burada YOKTUR ve eklenmez.

import type { TriageStatus } from "@/lib/skor";

/** openapi `Business` — alan adları birebir aynı. */
export type Isletme = {
  id: number;
  place_id: string;
  name: string;
  category: string | null;
  address: string | null;
  phone: string | null;
  website: string | null;
  ig_handle: string | null;
  rating_count: number | null;
  discovered_at: string;
  score: number | null;
  status: TriageStatus | null;
};

/** openapi `Stats`. */
export type Istatistik = {
  scanned: number;
  qualified: number;
  reports: number;
  monthly_cost_usd: number;
};

/** openapi `BusinessList`. */
export type IsletmeListesi = {
  items: Isletme[];
  total: number;
};

/** openapi `/businesses` sorgu parametreleri — adlar ve değer kümeleri birebir. */
export type IsletmeSorgusu = {
  status?: TriageStatus;
  category?: string;
  min_score?: number;
  limit: number;
  offset: number;
};

// --- sabit mock kayıtları --------------------------------------------------
//
// Kategoriler SPEC §4 kapasite ağırlığından seçildi (klinik, kuyumcu, oto galeri,
// emlak). Emlak kohortu bilinçli olarak 5'in altında tutuldu ki kohort yetersizliği
// edge case'i panelde görünsün (SPEC §4: kohort < 5 → potansiyel hesaplanmaz, watch).

const _mock_isletmeler: Isletme[] = [
  // Diş kliniği — 6 taranmış hesap, kohort dolu
  {
    id: 1,
    place_id: "ChIJd_samsun_001",
    name: "Atakum Ağız ve Diş Sağlığı",
    category: "Diş kliniği",
    address: "Atakum, Samsun",
    phone: "+90 362 000 0001",
    website: "https://atakumdis.example",
    ig_handle: "atakumdis",
    rating_count: 214,
    discovered_at: "2026-07-18T09:12:00Z",
    score: 82,
    status: "qualified",
  },
  {
    id: 2,
    place_id: "ChIJd_samsun_002",
    name: "İlkadım Diş Polikliniği",
    category: "Diş kliniği",
    address: "İlkadım, Samsun",
    phone: "+90 362 000 0002",
    website: "https://ilkadimdis.example",
    ig_handle: "ilkadimdis",
    rating_count: 96,
    discovered_at: "2026-07-18T10:03:00Z",
    score: 74,
    status: "qualified",
  },
  {
    id: 3,
    place_id: "ChIJd_samsun_003",
    name: "Bulvar Diş Estetik",
    category: "Diş kliniği",
    address: "Canik, Samsun",
    phone: "+90 362 000 0003",
    website: null,
    ig_handle: "bulvardisestetik",
    rating_count: 61,
    discovered_at: "2026-07-19T08:20:00Z",
    score: 58,
    status: "watch",
  },
  {
    id: 4,
    place_id: "ChIJd_samsun_004",
    name: "Karadeniz Ortodonti",
    category: "Diş kliniği",
    address: "Atakum, Samsun",
    phone: "+90 362 000 0004",
    website: "https://kdortodonti.example",
    ig_handle: "kdortodonti",
    rating_count: 143,
    discovered_at: "2026-07-19T11:45:00Z",
    score: 47,
    status: "watch",
  },
  {
    id: 5,
    place_id: "ChIJd_samsun_005",
    name: "Selin Diş",
    category: "Diş kliniği",
    address: "Tekkeköy, Samsun",
    phone: null,
    website: null,
    ig_handle: "selindisklinik",
    rating_count: 12,
    discovered_at: "2026-07-20T07:30:00Z",
    score: 29,
    status: "rejected",
  },
  {
    id: 6,
    place_id: "ChIJd_samsun_006",
    name: "Denta Vega",
    category: "Diş kliniği",
    address: "İlkadım, Samsun",
    phone: "+90 362 000 0006",
    website: "https://dentavega.example",
    ig_handle: "dentavega",
    rating_count: 188,
    discovered_at: "2026-07-20T09:10:00Z",
    score: 91,
    status: "qualified",
  },

  // Kuyumcu — 5 taranmış hesap, kohort tam sınırda dolu
  {
    id: 7,
    place_id: "ChIJd_samsun_007",
    name: "Çarşı Altın Kuyumculuk",
    category: "Kuyumcu",
    address: "İlkadım, Samsun",
    phone: "+90 362 000 0007",
    website: null,
    ig_handle: "carsialtin",
    rating_count: 74,
    discovered_at: "2026-07-17T12:00:00Z",
    score: 66,
    status: "watch",
  },
  {
    id: 8,
    place_id: "ChIJd_samsun_008",
    name: "Has Kuyumcu",
    category: "Kuyumcu",
    address: "Atakum, Samsun",
    phone: "+90 362 000 0008",
    website: "https://haskuyumcu.example",
    ig_handle: "haskuyumcusamsun",
    rating_count: 121,
    discovered_at: "2026-07-17T13:22:00Z",
    score: 78,
    status: "qualified",
  },
  {
    id: 9,
    place_id: "ChIJd_samsun_009",
    name: "Elmas Pırlanta Evi",
    category: "Kuyumcu",
    address: "Canik, Samsun",
    phone: "+90 362 000 0009",
    website: null,
    ig_handle: "elmaspirlanta",
    rating_count: 33,
    discovered_at: "2026-07-18T15:40:00Z",
    score: 41,
    status: "watch",
  },
  {
    id: 10,
    place_id: "ChIJd_samsun_010",
    name: "Gümüş Dünyası",
    category: "Kuyumcu",
    address: "Bafra, Samsun",
    phone: null,
    website: null,
    ig_handle: "gumusdunyasi",
    rating_count: 8,
    discovered_at: "2026-07-19T16:05:00Z",
    score: 24,
    status: "rejected",
  },
  {
    id: 11,
    place_id: "ChIJd_samsun_011",
    name: "Nur Kuyumculuk",
    category: "Kuyumcu",
    address: "İlkadım, Samsun",
    phone: "+90 362 000 0011",
    website: "https://nurkuyum.example",
    ig_handle: "nurkuyumculuk",
    rating_count: 57,
    discovered_at: "2026-07-20T10:50:00Z",
    score: 84,
    status: "qualified",
  },

  // Oto galeri — 6 taranmış hesap
  {
    id: 12,
    place_id: "ChIJd_samsun_012",
    name: "Karadeniz Oto Galeri",
    category: "Oto galeri",
    address: "Tekkeköy, Samsun",
    phone: "+90 362 000 0012",
    website: "https://kdoto.example",
    ig_handle: "kdotogaleri",
    rating_count: 45,
    discovered_at: "2026-07-16T09:00:00Z",
    score: 72,
    status: "qualified",
  },
  {
    id: 13,
    place_id: "ChIJd_samsun_013",
    name: "Prestij Motors",
    category: "Oto galeri",
    address: "Atakum, Samsun",
    phone: "+90 362 000 0013",
    website: "https://prestijmotors.example",
    ig_handle: "prestijmotorssamsun",
    rating_count: 89,
    discovered_at: "2026-07-16T11:15:00Z",
    score: 63,
    status: "watch",
  },
  {
    id: 14,
    place_id: "ChIJd_samsun_014",
    name: "Yıldız Oto",
    category: "Oto galeri",
    address: "Canik, Samsun",
    phone: null,
    website: null,
    ig_handle: "yildizoto55",
    rating_count: 17,
    discovered_at: "2026-07-17T14:30:00Z",
    score: 38,
    status: "rejected",
  },
  {
    id: 15,
    place_id: "ChIJd_samsun_015",
    name: "Elit Car Samsun",
    category: "Oto galeri",
    address: "İlkadım, Samsun",
    phone: "+90 362 000 0015",
    website: "https://elitcar.example",
    ig_handle: "elitcarsamsun",
    rating_count: 52,
    discovered_at: "2026-07-18T16:20:00Z",
    score: 88,
    status: "qualified",
  },
  {
    id: 16,
    place_id: "ChIJd_samsun_016",
    name: "Bafra Oto Center",
    category: "Oto galeri",
    address: "Bafra, Samsun",
    phone: "+90 362 000 0016",
    website: null,
    ig_handle: "bafraotocenter",
    rating_count: 23,
    discovered_at: "2026-07-19T09:45:00Z",
    score: 51,
    status: "watch",
  },
  {
    id: 17,
    place_id: "ChIJd_samsun_017",
    name: "Şahin Galeri",
    category: "Oto galeri",
    address: "Tekkeköy, Samsun",
    phone: null,
    website: null,
    ig_handle: "sahingaleri",
    rating_count: 6,
    discovered_at: "2026-07-20T12:10:00Z",
    score: 19,
    status: "rejected",
  },

  // Emlak — yalnızca 2 taranmış hesap: kohort < 5, potansiyel hesaplanamaz, watch
  {
    id: 18,
    place_id: "ChIJd_samsun_018",
    name: "Sahil Gayrimenkul",
    category: "Emlak",
    address: "Atakum, Samsun",
    phone: "+90 362 000 0018",
    website: "https://sahilgm.example",
    ig_handle: "sahilgayrimenkul",
    rating_count: 41,
    discovered_at: "2026-07-19T13:00:00Z",
    score: null,
    status: "watch",
  },
  {
    id: 19,
    place_id: "ChIJd_samsun_019",
    name: "Anahtar Emlak",
    category: "Emlak",
    address: "İlkadım, Samsun",
    phone: "+90 362 000 0019",
    website: null,
    ig_handle: "anahtaremlak55",
    rating_count: 15,
    discovered_at: "2026-07-20T14:25:00Z",
    score: null,
    status: "watch",
  },

  // Henüz taranmamış — score ve status null (openapi: taranmamışsa ikisi de null)
  {
    id: 20,
    place_id: "ChIJd_samsun_020",
    name: "Liman Kafe",
    category: "Kafe",
    address: "İlkadım, Samsun",
    phone: "+90 362 000 0020",
    website: null,
    ig_handle: "limankafesamsun",
    rating_count: 302,
    discovered_at: "2026-07-21T08:00:00Z",
    score: null,
    status: null,
  },
  {
    id: 21,
    place_id: "ChIJd_samsun_021",
    name: "Meydan Eczanesi",
    category: "Eczane",
    address: "Atakum, Samsun",
    phone: "+90 362 000 0021",
    website: null,
    ig_handle: null,
    rating_count: null,
    discovered_at: "2026-07-21T09:30:00Z",
    score: null,
    status: null,
  },
];

/**
 * Tek düğme: mock kaynağını boşaltmak için bunu `[]` yap. Panel çökmemeli, boş
 * durumu çizmeli — Faz 1'in çıkış kriteri budur.
 */
export const MOCK_ISLETMELER: readonly Isletme[] = _mock_isletmeler;

export const MOCK_ISTATISTIK: Istatistik = {
  scanned: MOCK_ISLETMELER.filter((i) => i.score !== null).length,
  qualified: MOCK_ISLETMELER.filter((i) => i.status === "qualified").length,
  reports: 4,
  monthly_cost_usd: 3.87,
};

/**
 * Bir işletmenin kohortu: AYNI kategorideki taranmış (skoru olan) tüm hesapların
 * skorları. Kohort rayının soluk çentikleri budur. SPEC §4: karşılaştırma daima
 * aynı kategorideki taranmış hesapların dağılımına göre yapılır.
 */
export function kategoriKohortu(
  kategori: string | null,
  kaynak: readonly Isletme[] = MOCK_ISLETMELER,
): number[] {
  if (kategori === null) return [];
  return kaynak
    .filter((i) => i.category === kategori && i.score !== null)
    .map((i) => i.score as number);
}

/**
 * openapi `/businesses` semantiğinin istemci tarafı taklidi. FE-3'te bu fonksiyon
 * yerini gerçek isteğe bırakır; imzası (sorgu → liste + total) aynı kalır.
 */
export function sorgula(
  sorgu: IsletmeSorgusu,
  kaynak: readonly Isletme[] = MOCK_ISLETMELER,
): IsletmeListesi {
  const suzulmus = kaynak.filter((i) => {
    if (sorgu.status !== undefined && i.status !== sorgu.status) return false;
    if (sorgu.category !== undefined && i.category !== sorgu.category)
      return false;
    // min_score: bu değerin altındaki VE skoru olmayan kayıtlar elenir (openapi).
    if (sorgu.min_score !== undefined) {
      if (i.score === null || i.score < sorgu.min_score) return false;
    }
    return true;
  });

  const items = suzulmus.slice(sorgu.offset, sorgu.offset + sorgu.limit);
  return { items, total: suzulmus.length };
}
