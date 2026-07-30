import type { Bulgu } from "@/lib/api/tipler";
import { kritikMi, ONEM_ETIKET, onemeSirali } from "@/lib/onem";

/**
 * Denetim bulguları — öneme göre sıralı, kritik üstte (SPEC §5).
 *
 * Her bulgu iki ayrı katman taşır (sözleşme `Finding`): `detail` deterministik
 * tetiktir (ölçülen değer + eşik, LLM'siz, daima dolu); `message` LLM'in ajans
 * diline çevirisidir (null olabilir — sentez öncesi). İkisi ayrı gösterilir ki
 * neyin ölçülüp neyin yazıya döküldüğü karışmasın; LLM bulgu icat etmez.
 *
 * Renk: yalnızca kritik önem oksit alır (DESIGN §1). Kalan üç seviye sıra ve
 * önem etiketiyle ayrışır; kromatik kodlama yok.
 */
export function BulguListesi({ bulgular }: { bulgular: readonly Bulgu[] }) {
  if (bulgular.length === 0) {
    return (
      <p className="text-metin-2">
        Hiçbir kural tetiklenmedi — bu hesapta ölçülen bir eksik bulunmadı.
      </p>
    );
  }

  const sirali = onemeSirali(bulgular);

  return (
    <ul className="flex flex-col">
      {sirali.map((b) => (
        <li key={b.rule} className="border-t border-ayrac py-3 first:border-t-0">
          <div className="flex items-baseline justify-between gap-4">
            <span
              className={
                "text-orta " + (kritikMi(b.severity) ? "text-uyari" : "")
              }
            >
              {b.title}
            </span>
            <span
              className={
                "shrink-0 text-mikro uppercase " +
                (kritikMi(b.severity) ? "text-uyari" : "text-metin-2")
              }
            >
              {ONEM_ETIKET[b.severity]}
            </span>
          </div>
          {/* Deterministik tetik — daima dolu. */}
          <p className="mt-1 text-metin-2">{b.detail}</p>
          {/* LLM ajans-dili metni — yalnız üretildiyse; yokluğu hata değildir. */}
          {b.message !== null && b.message.trim() !== "" && (
            <p className="mt-2">{b.message}</p>
          )}
        </li>
      ))}
    </ul>
  );
}
