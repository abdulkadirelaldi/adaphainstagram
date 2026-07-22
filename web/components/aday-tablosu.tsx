import { RayAnahtari } from "@/components/ray-anahtari";
import { SkorHucresi } from "@/components/skor-hucresi";
import type { Isletme } from "@/lib/api/tipler";
import { sayi, tarih, YOK } from "@/lib/bicim";
import { kategoriKohortu } from "@/lib/kohort";

/**
 * Aday tablosu — tam genişlik, kenarlıklı yoğun satırlar.
 *
 * Sütunların hepsi `docs/openapi.yaml` `Business` şemasının gerçek alanlarıdır.
 * Takipçi, gösterim, erişim, son gönderi tarihi Business'ta YOKTUR (snapshots /
 * posts tablolarında) ve buraya girmez (CLAUDE.md kural 7 + sözleşme sınırı).
 *
 * Üç durum: yükleniyor (skeleton), hata, hazır. Hazırken liste boşsa boş durum
 * çizilir — Faz 1'in çıkış kriteri budur, baştan savma değil birinci sınıf tasarlı.
 */

type Durum =
  | { tip: "yukleniyor" }
  | { tip: "hata"; mesaj?: string; yeniden?: () => void }
  | { tip: "hazir"; kayitlar: readonly Isletme[] };

const SUTUNLAR = [
  { anahtar: "isletme", etiket: "İşletme", genislik: "auto" },
  { anahtar: "kategori", etiket: "Kategori", genislik: "168px" },
  { anahtar: "rating", etiket: "Değerlendirme", genislik: "132px" },
  { anahtar: "kesif", etiket: "Keşfedildi", genislik: "120px" },
  { anahtar: "skor", etiket: "Triyaj skoru", genislik: "212px" },
] as const;

export function AdayTablosu({
  durum,
  kohortKaynagi = [],
}: {
  durum: Durum;
  /** Kohort rayının filtresiz dağılım kaynağı (bkz. useKohortKaynagi). */
  kohortKaynagi?: readonly Isletme[];
}) {
  return (
    <table className="w-full border-collapse text-govde">
      <caption className="sr-only">
        Taranan işletmeler ve triyaj skorları. Skor yükseldikçe aday güçlenir.
      </caption>
      <colgroup>
        {SUTUNLAR.map((s) => (
          <col key={s.anahtar} style={{ width: s.genislik }} />
        ))}
      </colgroup>
      <thead>
        <tr className="border-b border-cizgi">
          {SUTUNLAR.map((sutun) => (
            <th
              key={sutun.anahtar}
              scope="col"
              className={
                "px-6 py-3 align-bottom text-mikro font-medium text-kursun uppercase " +
                (sutun.anahtar === "rating" ? "text-right" : "text-left")
              }
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
        {durum.tip === "yukleniyor" && <YukleniyorSatirlari />}
        {durum.tip === "hata" && (
          <tr>
            <td colSpan={SUTUNLAR.length} className="px-6 py-16">
              <HataDurumu mesaj={durum.mesaj} yeniden={durum.yeniden} />
            </td>
          </tr>
        )}
        {durum.tip === "hazir" &&
          (durum.kayitlar.length === 0 ? (
            <tr>
              <td colSpan={SUTUNLAR.length} className="px-6 py-16">
                <BosDurum />
              </td>
            </tr>
          ) : (
            durum.kayitlar.map((k) => (
              <Satir key={k.id} isletme={k} kohortKaynagi={kohortKaynagi} />
            ))
          ))}
      </tbody>
    </table>
  );
}

function Satir({
  isletme,
  kohortKaynagi,
}: {
  isletme: Isletme;
  kohortKaynagi: readonly Isletme[];
}) {
  const kohort = kategoriKohortu(isletme.category, kohortKaynagi);
  return (
    <tr className="border-b border-cizgi align-middle" style={{ height: "var(--olcu-satir)" }}>
      <td className="px-6">
        <div className="flex flex-col">
          <span className="truncate">{isletme.name}</span>
          {isletme.ig_handle ? (
            <span className="sayi text-kucuk text-kursun">@{isletme.ig_handle}</span>
          ) : (
            <span className="text-kucuk text-kursun">handle eşlenmedi</span>
          )}
        </div>
      </td>
      <td className="px-6 text-kursun">{isletme.category ?? YOK}</td>
      <td className="sayi px-6 text-right tabular-nums">
        {sayi(isletme.rating_count)}
      </td>
      <td className="sayi px-6 tabular-nums text-kursun">
        {tarih(isletme.discovered_at)}
      </td>
      <td className="px-6">
        <SkorHucresi skor={isletme.score} status={isletme.status} kohort={kohort} />
      </td>
    </tr>
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
        <tr key={i} className="border-b border-cizgi" style={{ height: "var(--olcu-satir)" }}>
          <td colSpan={4} className="px-6">
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
      <p className="text-orta">Bu filtreye uyan aday yok.</p>
      <p className="text-kursun">
        Filtreleri gevşetin ya da temizleyin. Keşif çalıştığında Samsun&apos;daki
        işletmeler taranır ve skorlarıyla buraya düşer; nitelikli olanlar rayın sağ
        ucunda toplanır.
      </p>
    </div>
  );
}

/** Hata ne olduğunu ve ne yapılacağını söyler; kod tek başına gösterilmez. */
function HataDurumu({
  mesaj,
  yeniden,
}: {
  mesaj?: string;
  yeniden?: () => void;
}) {
  return (
    <div className="flex max-w-md flex-col gap-2">
      <p className="text-orta">Liste yüklenemedi.</p>
      <p className="text-kursun">
        {mesaj ?? "Sunucuya ulaşılamadı. Bağlantıyı kontrol edip yeniden deneyin."}
      </p>
      {yeniden && (
        <button
          type="button"
          onClick={yeniden}
          className="mt-2 self-start border border-cizgi px-3 py-1 text-govde"
        >
          Yeniden dene
        </button>
      )}
    </div>
  );
}
