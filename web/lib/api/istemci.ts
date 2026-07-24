import type {
  Denetim,
  IsDurumu,
  IsKabul,
  IsletmeListesi,
  Istatistik,
  KesifIstegi,
} from "@/lib/api/tipler";

/**
 * REST istemcisi. Taban URL ortam değişkeninden okunur; sabit kodlama yok.
 * `NEXT_PUBLIC_API_URL` verilmezse yerel geliştirme varsayılanına düşer
 * (openapi `servers` ile aynı: http://localhost:8000).
 */
const TABAN =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

/** Panelin `/businesses` sorgusu — openapi query parametreleriyle birebir. */
export type IsletmeSorgusu = {
  status?: string;
  category?: string;
  min_score?: number;
  limit: number;
  offset: number;
};

export class ApiHatasi extends Error {
  constructor(
    public durum: number,
    mesaj: string,
  ) {
    super(mesaj);
    this.name = "ApiHatasi";
  }
}

type Secenekler = { imza?: AbortSignal; metod?: string; govde?: unknown };

async function istek<T>(yol: string, s: Secenekler = {}): Promise<T> {
  let yanit: Response;
  try {
    yanit = await fetch(`${TABAN}${yol}`, {
      method: s.metod ?? "GET",
      headers: {
        accept: "application/json",
        ...(s.govde !== undefined
          ? { "content-type": "application/json" }
          : {}),
      },
      body: s.govde !== undefined ? JSON.stringify(s.govde) : undefined,
      signal: s.imza,
    });
  } catch {
    // Ağ/CORS/DNS — sunucuya hiç ulaşılamadı.
    throw new ApiHatasi(0, "Sunucuya ulaşılamadı.");
  }
  if (!yanit.ok) {
    throw new ApiHatasi(yanit.status, `İstek ${yanit.status} döndü.`);
  }
  return (await yanit.json()) as T;
}

function sorguDizesi(sorgu: IsletmeSorgusu): string {
  const p = new URLSearchParams();
  if (sorgu.status !== undefined) p.set("status", sorgu.status);
  if (sorgu.category !== undefined) p.set("category", sorgu.category);
  if (sorgu.min_score !== undefined) p.set("min_score", String(sorgu.min_score));
  p.set("limit", String(sorgu.limit));
  p.set("offset", String(sorgu.offset));
  return p.toString();
}

export function getStats(imza?: AbortSignal): Promise<Istatistik> {
  return istek<Istatistik>("/stats", { imza });
}

export function getBusinesses(
  sorgu: IsletmeSorgusu,
  imza?: AbortSignal,
): Promise<IsletmeListesi> {
  return istek<IsletmeListesi>(`/businesses?${sorguDizesi(sorgu)}`, { imza });
}

/** Keşif taramasını kuyruğa alır; anında `job_id` döner (senkron scraping yok). */
export function runDiscovery(
  govde: KesifIstegi,
  imza?: AbortSignal,
): Promise<IsKabul> {
  return istek<IsKabul>("/discovery/run", { metod: "POST", govde, imza });
}

/** Kuyruk işinin güncel durumu. Bilinmeyen/süresi dolmuş id → 404 (ApiHatasi 404). */
export function getJob(id: string, imza?: AbortSignal): Promise<IsDurumu> {
  return istek<IsDurumu>(`/jobs/${encodeURIComponent(id)}`, { imza });
}

/**
 * Nitelikli bir işletme için derin denetimi kuyruğa alır. Anında `job_id` döner.
 * Nitelikli değil → 409, işletme yok → 404 (ikisi de ApiHatasi ilgili durumla).
 */
export function runAudit(
  businessId: number,
  imza?: AbortSignal,
): Promise<IsKabul> {
  return istek<IsKabul>(`/businesses/${businessId}/audit`, {
    metod: "POST",
    imza,
  });
}

/** Denetim sonucu: görünürlük skoru + bulgular + (varsa) rapor metni + taslak. */
export function getAudit(id: number, imza?: AbortSignal): Promise<Denetim> {
  return istek<Denetim>(`/audits/${id}`, { imza });
}
