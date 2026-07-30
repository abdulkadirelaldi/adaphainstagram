import Link from "next/link";
import { TemaToggle } from "@/components/tema-toggle";

/**
 * Uygulama kabuğu: yüzey renginde sol gezinme + zemin renginde içerik alanı.
 * Kurumsal dashboard düzeni — ferah boşluk, yumuşak ayraç, tema anahtarı.
 */
export function Kabuk({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <nav
        aria-label="Bölümler"
        className="flex shrink-0 flex-col border-r border-ayrac bg-yuzey"
        style={{ width: "var(--olcu-sol-ray)" }}
      >
        <div className="flex items-center justify-between px-5 py-5">
          <div className="flex flex-col">
            <span className="text-orta font-bold tracking-tight text-metin">
              Radar
            </span>
            <span className="text-mikro font-medium text-metin-2 uppercase">
              Kıyı Medya
            </span>
          </div>
          <TemaToggle />
        </div>

        {/* Faz 1'de tek gerçek bölüm var; ölü bağlantı konmaz. */}
        <ul className="flex flex-col gap-1 px-3 py-2">
          <li>
            <Link
              href="/"
              aria-current="page"
              className="block rounded-buton bg-marka-yumusak px-3 py-2 text-govde font-semibold text-marka"
            >
              Adaylar
            </Link>
          </li>
        </ul>
      </nav>

      <main className="min-w-0 flex-1 bg-zemin">{children}</main>
    </div>
  );
}
