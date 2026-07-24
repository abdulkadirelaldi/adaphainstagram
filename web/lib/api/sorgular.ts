import { useEffect } from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  getAudit,
  getBusinesses,
  getJob,
  getStats,
  runAudit,
  runDiscovery,
  type IsletmeSorgusu,
} from "@/lib/api/istemci";
import type { KesifIstegi } from "@/lib/api/tipler";

/** openapi `limit` üst sınırı — kohort kaynağı bu kadar kaydı kapsar. */
const KOHORT_LIMITI = 200;

/** Üst şerit sayaçları — `/stats`. */
export function useStats() {
  return useQuery({
    queryKey: ["stats"],
    queryFn: ({ signal }) => getStats(signal),
  });
}

/** Filtreli, sayfalı aday listesi — `/businesses`. */
export function useBusinesses(sorgu: IsletmeSorgusu) {
  return useQuery({
    queryKey: ["businesses", sorgu],
    queryFn: ({ signal }) => getBusinesses(sorgu, signal),
    // Sayfa değişiminde tablo boşalıp yeniden dolmasın; eski veri yeni gelene
    // dek durur (TanStack v5 `placeholderData` ile önceki sonucu tutar).
    placeholderData: (onceki) => onceki,
  });
}

/**
 * Kohort kaynağı — filtresiz tüm liste, yalnızca kohort rayının dağılımı için.
 * Ana listeden ayrı tutulur ki filtre uygulansa bile ray tüm kohortu göstersin
 * ve görece konum bozulmasın. Tek istek, 30s cache.
 *
 * Sınır: `KOHORT_LIMITI` kaydı aşan bir kohort kaynağı eksik kalır — Faz 1 sahte
 * verisinde sorun değil. Kalıcı çözüm için kategori-dağılım ucu gerekir; bkz.
 * docs/TASKS.md ## Bloke (FE-3 notu).
 */
export function useKohortKaynagi() {
  return useQuery({
    queryKey: ["kohort-kaynagi"],
    queryFn: ({ signal }) =>
      getBusinesses({ limit: KOHORT_LIMITI, offset: 0 }, signal),
    staleTime: 30_000,
  });
}

/** İş bittiğinde tazelenecek liste sorguları. */
const VERI_ANAHTARLARI = [["businesses"], ["stats"], ["kohort-kaynagi"]] as const;

/** Keşif taramasını başlatır (mutation). Başarıda `job_id` döner. */
export function useRunDiscovery() {
  return useMutation({
    mutationFn: (govde: KesifIstegi) => runDiscovery(govde),
  });
}

/**
 * Derin denetimi başlatır (mutation). Başarıda `job_id` döner; iş `useJob` ile
 * yoklanır, `done`'da `result.audit_id` ile denetim çekilir. Nitelikli olmayan
 * hesapta uç 409 döner (UI düğmeyi zaten pasif tutar; bu son savunma).
 */
export function useRunAudit() {
  return useMutation({
    mutationFn: (businessId: number) => runAudit(businessId),
  });
}

/** Denetim sonucu — `audit_id` gelince çekilir. */
export function useAudit(auditId: number | null) {
  return useQuery({
    queryKey: ["audit", auditId],
    queryFn: ({ signal }) => getAudit(auditId as number, signal),
    enabled: auditId !== null,
  });
}

/** İşin durumunu yoklama aralığı — poll bitince duracak sınır. */
const POLL_MS = 1500;

/**
 * `job_id` verildiğinde `/jobs/{id}`'i yoklar. İş `done` ya da `error` olunca
 * `refetchInterval` false döner ve **poll durur** — süresiz istek yok. İş `done`
 * olduğunda liste sorguları tazelenir, tablo/üst şerit yeni DB verisini çeker.
 */
export function useJob(jobId: string | null) {
  const qc = useQueryClient();
  const sorgu = useQuery({
    queryKey: ["job", jobId],
    queryFn: ({ signal }) => getJob(jobId as string, signal),
    enabled: jobId !== null,
    // done/error → false: poll durur, süresiz istek yok.
    refetchInterval: (q) => {
      const hal = q.state.data?.status;
      return hal === "done" || hal === "error" ? false : POLL_MS;
    },
  });

  // İş bittiğinde liste sorgularını bir kez tazele; tablo yeni DB verisini çeker.
  const bitti = sorgu.data?.status === "done";
  useEffect(() => {
    if (!bitti) return;
    for (const anahtar of VERI_ANAHTARLARI) {
      void qc.invalidateQueries({ queryKey: anahtar });
    }
  }, [bitti, qc]);

  return sorgu;
}
