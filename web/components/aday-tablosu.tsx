import { RayAnahtari } from "@/components/ray-anahtari";

/**
 * Aday tablosu kabuğu — tam genişlik, kenarlıklı yoğun satırlar.
 *
 * FE-1'de veri yok: başlık çizilir, gövde boş durum ya da yükleniyor
 * satırlarıyla dolar. Sütun genişlikleri sabittir; veri geldiğinde başlık
 * kaymaz.
 *
 * Ölçmediğimiz hiçbir şey burada sütun olamaz — erişim, gösterim, kaydetme,
 * profil ziyareti, demografi (CLAUDE.md kural 7).
 */

const SUTUNLAR = [
  { anahtar: "isletme", etiket: "İşletme", genislik: "auto" },
  { anahtar: "kategori", etiket: "Kategori", genislik: "180px" },
  { anahtar: "takipci", etiket: "Takipçi", genislik: "112px" },
  { anahtar: "gonderi", etiket: "Son gönderi", genislik: "128px" },
  { anahtar: "skor", etiket: "Triyaj skoru", genislik: "212px" },
] as const;

export function AdayTablosu({
  durum = "bos",
}: {
  durum?: "bos" | "yukleniyor";
}) {
  return (
    <table className="w-full border-collapse text-govde">
      <caption className="sr-only">
        Taranan işletmeler ve triyaj skorları. Skor yükseldikçe aday güçlenir.
      </caption>
      <thead>
        <tr className="border-b border-cizgi">
          {SUTUNLAR.map((sutun) => (
            <th
              key={sutun.anahtar}
              scope="col"
              className="px-6 py-3 text-left align-bottom text-mikro font-medium text-kursun uppercase"
              style={{ width: sutun.genislik }}
            >
              {sutun.anahtar === "skor" ? (
                <div className="flex flex-col gap-2">
                  <span>{sutun.etiket}</span>
                  <RayAnahtari />
                </div>
              ) : (
                sutun.etiket
              )}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {durum === "yukleniyor" ? (
          <YukleniyorSatirlari />
        ) : (
          <tr>
            <td colSpan={SUTUNLAR.length} className="px-6 py-16">
              <BosDurum />
            </td>
          </tr>
        )}
      </tbody>
    </table>
  );
}

/**
 * Yükleniyor: dönen çark yok. Tablo iskeletini korur, satır yerlerini boş
 * raylarla tutar. Alet yüklenirken de aletin biçimindedir.
 */
function YukleniyorSatirlari() {
  return (
    <>
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <tr key={i} className="border-b border-cizgi">
          <td colSpan={4} className="px-6" style={{ height: "var(--olcu-satir)" }}>
            <span className="sr-only">Yükleniyor</span>
          </td>
          <td className="px-6">
            <svg
              viewBox="0 0 100 20"
              preserveAspectRatio="none"
              aria-hidden="true"
              style={{
                width: "var(--olcu-ray-genislik)",
                height: "var(--olcu-ray-yukseklik)",
              }}
            >
              <line
                x1={0}
                y1={19}
                x2={100}
                y2={19}
                className="stroke-ray-yol"
                strokeWidth={1}
                vectorEffect="non-scaling-stroke"
              />
            </svg>
          </td>
        </tr>
      ))}
    </>
  );
}

/** Boş ekran özür dilemez, davet eder. */
function BosDurum() {
  return (
    <div className="flex max-w-md flex-col gap-2">
      <p className="text-orta">Liste henüz boş.</p>
      <p className="text-kursun">
        Keşif çalıştığında Samsun&apos;daki işletmeler taranır ve skorlarıyla
        buraya düşer. Nitelikli olanlar rayın sağ ucunda toplanır.
      </p>
    </div>
  );
}
