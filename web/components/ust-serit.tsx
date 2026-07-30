import { para, sayi, YOK } from "@/lib/bicim";
import type { Istatistik } from "@/lib/api/tipler";

/**
 * Üst şerit — SPEC §7 `/stats`: taranan, nitelikli, rapor, aylık maliyet.
 *
 * Dört istatistik **kartı**: beyaz yüzey, yumuşak gölge, yuvarlak köşe, büyük
 * okunur sayı. Veri gelmediğinde rakam yerine yarım tire durur — kart asla
 * kaybolmaz, yeri korunur ki yükleme sırasında düzen zıplamasın.
 *
 * Maliyet alarmı (SPEC §8): aylık maliyet yapılandırılmış eşiği aştıysa
 * `monthly_cost_alarm` true olur ve maliyet kartı görünür bir uyarı taşır.
 * Renk TEK taşıyıcı değildir — "Eşik aşıldı" metni uyarıyı sözle de söyler
 * (bkz. docs/DESIGN.md § maliyet alarmı).
 */
export function UstSerit({ istatistik }: { istatistik?: Istatistik }) {
  const alarm = istatistik?.monthly_cost_alarm === true;

  const olculer = [
    { etiket: "Taranan", deger: istatistik ? sayi(istatistik.scanned) : YOK },
    { etiket: "Nitelikli", deger: istatistik ? sayi(istatistik.qualified) : YOK },
    { etiket: "Rapor", deger: istatistik ? sayi(istatistik.reports) : YOK },
    {
      etiket: "Aylık maliyet",
      deger: istatistik ? para(istatistik.monthly_cost_usd) : YOK,
      alarm,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {olculer.map((olcu) => (
        <div
          key={olcu.etiket}
          className={
            "flex flex-col gap-2 rounded-kart border bg-yuzey px-5 py-4 shadow-kart " +
            (olcu.alarm ? "border-uyari" : "border-ayrac")
          }
        >
          <span className="text-mikro font-semibold text-metin-2 uppercase">
            {olcu.etiket}
          </span>
          <span
            className={
              "sayi text-rakam font-bold tabular-nums " +
              (olcu.alarm ? "text-uyari" : "text-metin")
            }
          >
            {olcu.deger}
          </span>
          {olcu.alarm && (
            <span className="text-kucuk font-semibold text-uyari">
              Eşik aşıldı
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
