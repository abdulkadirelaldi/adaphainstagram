import {
  ASGARI_KOHORT,
  BANT_ETIKET,
  kelepcele,
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
 *   konum      → skorun büyüklüğü (sürekli) · `score`
 *   yükseklik  → bant (elendi kısa · izlemede orta · nitelikli tam)
 *   renk       → bant (tek hue, üç koyuluk durağı)
 *
 * Bant DAİMA `status`'tan gelir (SkorHucresi türetir), `score`'dan değil — kohort<5
 * durumunda skor eşiği yanıltıcıdır (SPEC §4).
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
  bant,
  kohort,
}: {
  /** Raydaki konum. null ise dolu çentik çizilmez (henüz skorlanmadı). */
  skor: number | null;
  /** Görsel bant — statustan türer. null ise nötr işaret. */
  bant: SkorBandi | null;
  /** Aynı kategoride taranmış tüm hesapların skorları. */
  kohort: readonly number[];
}) {
  const yeterliKohort = kohort.length >= ASGARI_KOHORT;
  const konum = skor === null ? null : kelepcele(skor);

  const etiket =
    konum === null
      ? "Skorlanmadı."
      : yeterliKohort
        ? `${bant ? BANT_ETIKET[bant] : "Skor"}. Kohortta ${kohort.length} hesap arasında.`
        : `${bant ? BANT_ETIKET[bant] : "Skor"}. Kohort ${ASGARI_KOHORT} hesabın altında, karşılaştırma yapılmadı.`;

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

      {/* Bu satırın skoru. Konum yoksa (skor null) çizilmez. */}
      {konum !== null && (
        <line
          x1={konum}
          y1={TABAN - (bant ? RAY_YUKSEKLIK[bant] : 13)}
          x2={konum}
          y2={TABAN}
          className={bant ? RAY_RENK[bant] : "stroke-murekkep"}
          strokeWidth={2}
          vectorEffect="non-scaling-stroke"
        />
      )}
    </svg>
  );
}
