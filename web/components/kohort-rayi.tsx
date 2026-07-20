import {
  ASGARI_KOHORT,
  BANT_ETIKET,
  kelepcele,
  skorBandi,
  type SkorBandi,
} from "@/lib/skor";

/**
 * İMZA ÖĞESİ — kohort rayı.
 *
 * Skor hücresi çıplak bir sayı ya da rozet değildir. Her hücrede sabit bir 0–100
 * yatay ray durur: taranmış tüm kohortun skorları bu rayda soluk çentikler, o
 * satırın skoru dolu çentiktir. Böylece hiçbir skor tek başına okunmaz, daima
 * kohortun içindeki yeriyle okunur.
 *
 * Bu SPEC §4'ün merkezindeki ilkenin görselleştirilmesidir: mutlak eşik
 * yanıltıcıdır, anlamlı olan görece konumdur.
 *
 * Üç eksende kodlama yapılır — hiçbiri tek başına yeterli değildir:
 *   konum      → skorun büyüklüğü (sürekli)
 *   yükseklik  → bant (elendi kısa · izlemede orta · nitelikli tam)
 *   renk       → bant (tek hue, üç koyuluk durağı)
 */

const RAY_RENK: Record<SkorBandi, string> = {
  elendi: "stroke-skor-elendi",
  izlemede: "stroke-skor-izlemede",
  nitelikli: "stroke-skor-nitelikli",
};

/** Çentik yüksekliği (px). Taban çizgisinden yukarı doğru. */
const RAY_YUKSEKLIK: Record<SkorBandi, number> = {
  elendi: 8,
  izlemede: 13,
  nitelikli: 18,
};

const TABAN = 19;

export function KohortRayi({
  skor,
  kohort,
}: {
  skor: number;
  /** Aynı kategoride taranmış tüm hesapların skorları. */
  kohort: readonly number[];
}) {
  const bant = skorBandi(skor);
  const x = kelepcele(skor);
  const yeterliKohort = kohort.length >= ASGARI_KOHORT;

  return (
    <svg
      viewBox="0 0 100 20"
      preserveAspectRatio="none"
      role="img"
      aria-label={
        yeterliKohort
          ? `${BANT_ETIKET[bant]}. Kohortta ${kohort.length} hesap arasında.`
          : `${BANT_ETIKET[bant]}. Kohort ${ASGARI_KOHORT} hesabın altında, karşılaştırma yapılmadı.`
      }
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

      {/* Kohort çentikleri — tek tek okunmaz, küme olarak dağılımı gösterir. */}
      {yeterliKohort &&
        kohort.map((k, i) => (
          <line
            key={`${k}-${i}`}
            x1={kelepcele(k)}
            y1={TABAN - 6}
            x2={kelepcele(k)}
            y2={TABAN}
            className="stroke-ray-kohort"
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
          />
        ))}

      {/* Bu satırın skoru. */}
      <line
        x1={x}
        y1={TABAN - RAY_YUKSEKLIK[bant]}
        x2={x}
        y2={TABAN}
        className={RAY_RENK[bant]}
        strokeWidth={2}
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
