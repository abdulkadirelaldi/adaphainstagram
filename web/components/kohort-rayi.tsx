import { kelepcele, type SkorBandi } from "@/lib/skor";
import type { KategoriKohort } from "@/lib/api/tipler";

/**
 * İMZA ÖĞESİ — kohort rayı.
 *
 * Skor hücresi çıplak bir sayı ya da rozet değildir. Her hücrede sabit bir 0–100
 * yatay ray durur: o kategorinin skor DAĞILIMI (çeyrekler) rayda soluk bir bant,
 * o satırın skoru dolu çentiktir. Böylece hiçbir skor tek başına okunmaz, daima
 * kohortun içindeki yeriyle okunur.
 *
 * Bu SPEC §4'ün merkezindeki ilkenin görselleştirilmesidir: mutlak eşik
 * yanıltıcıdır, anlamlı olan görece konumdur.
 *
 * Dağılım kaynağı `GET /stats/categories` (BE-23): medyan + Q1 + Q3. FE-3'ün tek
 * tek skorları çizen "soluk çentik" yaklaşımı bununla değişti — çeyrek bandı 200+
 * hesapta da üç sayıyla ölçeklenir, gürültüsüzdür ve dağılımı nicel gösterir
 * (Q1–Q3 arası orta %50, medyan tam ortası). Görece konum daha okunur oldu.
 *
 * Üç eksende kodlama — hiçbiri tek başına yeterli değil:
 *   konum      → skorun büyüklüğü (sürekli) · `score`
 *   yükseklik  → bant (elendi kısa · izlemede orta · nitelikli tam)
 *   renk       → bant (tek hue, üç koyuluk durağı) · `status`'tan türer
 */

const RAY_RENK: Record<SkorBandi, string> = {
  elendi: "stroke-skor-elendi",
  izlemede: "stroke-skor-izlemede",
  nitelikli: "stroke-skor-nitelikli",
};

const RAY_YUKSEKLIK: Record<SkorBandi, number> = {
  elendi: 8,
  izlemede: 13,
  nitelikli: 18,
};

const TABAN = 19;

export function KohortRayi({
  skor,
  bant,
  kohort,
}: {
  /** Raydaki konum. null ise dolu çentik çizilmez (henüz skorlanmadı). */
  skor: number | null;
  /** Görsel bant — statustan türer. null ise nötr işaret. */
  bant: SkorBandi | null;
  /** Kategori kohort dağılımı (medyan + çeyrekler). Kohort<5 ise null çeyrekler. */
  kohort: KategoriKohort | null;
}) {
  const konum = skor === null ? null : kelepcele(skor);

  // SPEC §4: kohort<5 → dağılım hesaplanmaz (medyan null). Bant çizilmez.
  const dagilim =
    kohort &&
    kohort.score_median !== null &&
    kohort.score_q1 !== null &&
    kohort.score_q3 !== null
      ? {
          medyan: kelepcele(kohort.score_median),
          q1: kelepcele(kohort.score_q1),
          q3: kelepcele(kohort.score_q3),
        }
      : null;

  const etiket = etiketMetni(konum, dagilim);

  return (
    <svg
      viewBox="0 0 100 20"
      preserveAspectRatio="none"
      role="img"
      aria-label={etiket}
      style={{
        width: "var(--olcu-ray-genislik)",
        height: "var(--olcu-ray-yukseklik)",
      }}
    >
      {/* Taşıyıcı — sabit 0–100. Ray asla veriye göre ölçeklenmez. */}
      <line
        x1={0}
        y1={TABAN}
        x2={100}
        y2={TABAN}
        className="stroke-ray-yol"
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />

      {/* Kohort çeyrek bandı (Q1–Q3, orta %50) + medyan. Küme olarak dağılımı gösterir. */}
      {dagilim && (
        <>
          <rect
            x={Math.min(dagilim.q1, dagilim.q3)}
            y={TABAN - 6}
            width={Math.max(0.5, Math.abs(dagilim.q3 - dagilim.q1))}
            height={6}
            className="fill-ray-kohort"
          />
          <line
            x1={dagilim.medyan}
            y1={TABAN - 8}
            x2={dagilim.medyan}
            y2={TABAN}
            className="stroke-ray-kohort"
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
          />
        </>
      )}

      {/* Bu satırın skoru. Konum yoksa (skor null) çizilmez. */}
      {konum !== null && (
        <line
          x1={konum}
          y1={TABAN - (bant ? RAY_YUKSEKLIK[bant] : 13)}
          x2={konum}
          y2={TABAN}
          className={bant ? RAY_RENK[bant] : "stroke-metin"}
          strokeWidth={2}
          vectorEffect="non-scaling-stroke"
        />
      )}
    </svg>
  );
}

function etiketMetni(
  konum: number | null,
  dagilim: { medyan: number; q1: number; q3: number } | null,
): string {
  if (konum === null) return "Skorlanmadı.";
  if (!dagilim) return "Kohort 5 hesabın altında, karşılaştırma yapılmadı.";
  const yer =
    konum < dagilim.q1
      ? "kohortun alt çeyreğinde"
      : konum > dagilim.q3
        ? "kohortun üst çeyreğinde"
        : "kohortun orta yarısında";
  return `Skor ${Math.floor(konum)}, ${yer} (medyan ${Math.floor(dagilim.medyan)}).`;
}
