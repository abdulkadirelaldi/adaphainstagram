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

export type KesifIstegi = components["schemas"]["DiscoveryRequest"];
export type IsKabul = components["schemas"]["JobAccepted"];
export type IsDurumu = components["schemas"]["JobStatus"];
export type IsHali = components["schemas"]["JobState"];
export type IsIlerleme = components["schemas"]["JobProgress"];
export type IsSonuc = components["schemas"]["JobResult"];
