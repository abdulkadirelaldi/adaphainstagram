/**
 * Biçimlendiriciler. Buradan çıkan her değer mono yüzle dizilir (`.sayi`).
 * Veri yokken tek bir işaret kullanılır: yarım tire. "0" ile "bilinmiyor"
 * asla aynı görünmez.
 */

export const YOK = "—";

const sayiBicimi = new Intl.NumberFormat("tr-TR");
const paraBicimi = new Intl.NumberFormat("tr-TR", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});
const tarihBicimi = new Intl.DateTimeFormat("tr-TR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

export function sayi(deger: number | null | undefined): string {
  return deger == null ? YOK : sayiBicimi.format(deger);
}

export function para(deger: number | null | undefined): string {
  return deger == null ? YOK : paraBicimi.format(deger);
}

export function tarih(deger: string | Date | null | undefined): string {
  if (deger == null) return YOK;
  const d = typeof deger === "string" ? new Date(deger) : deger;
  return Number.isNaN(d.getTime()) ? YOK : tarihBicimi.format(d);
}
