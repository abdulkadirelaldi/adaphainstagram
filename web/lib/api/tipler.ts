import type { components } from "@/lib/api/schema";

/**
 * Sözleşme tiplerine temiz isimler. Tek doğruluk kaynağı `docs/openapi.yaml`;
 * `npm run gen:api` ile `schema.ts` üretilir, buradaki alias'lar onun derin
 * yollarını bileşenlerden gizler. Elle alan eklenmez — sözleşme değişince
 * yeniden üretilir (CLAUDE.md kural 3).
 */

export type Isletme = components["schemas"]["Business"];
export type IsletmeListesi = components["schemas"]["BusinessList"];
export type Istatistik = components["schemas"]["Stats"];
export type TriageStatus = components["schemas"]["TriageStatus"];
export type KategoriKohort = components["schemas"]["CategoryCohort"];
export type KategoriKohortListesi = components["schemas"]["CategoryCohortList"];

export type KesifIstegi = components["schemas"]["DiscoveryRequest"];
export type IsKabul = components["schemas"]["JobAccepted"];
export type IsDurumu = components["schemas"]["JobStatus"];
export type IsHali = components["schemas"]["JobState"];
export type IsIlerleme = components["schemas"]["JobProgress"];
export type IsSonuc = components["schemas"]["JobResult"];

export type Denetim = components["schemas"]["Audit"];
export type Bulgu = components["schemas"]["Finding"];
export type Onem = components["schemas"]["Severity"];
export type ErisimTaslagi = components["schemas"]["OutreachDraft"];
export type ErisimDurumu = components["schemas"]["OutreachStatus"];
export type ErisimKaydi = components["schemas"]["Outreach"];
export type ErisimGuncelleme = components["schemas"]["OutreachUpdate"];
