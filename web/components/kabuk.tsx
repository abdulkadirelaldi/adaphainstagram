import Link from "next/link";

/**
 * Uygulama kabuğu: ince sol ray + tam genişlik içerik alanı.
 * Kart yok, gölge yok. Ayrım tek bir saç teli çizgiyle yapılır.
 */
export function Kabuk({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <nav
        aria-label="Bölümler"
        className="flex shrink-0 flex-col border-r border-cizgi"
        style={{ width: "var(--olcu-sol-ray)" }}
      >
        <div className="border-b border-cizgi px-6 py-4">
          <span className="text-orta font-medium tracking-tight">Radar</span>
          <span className="ml-2 text-mikro text-kursun uppercase">
            Kıyı Medya
          </span>
        </div>

        {/* Faz 1'de tek bölüm var. Ölü bağlantı koymuyoruz; bölümler
            gerçekten inşa edildikçe buraya eklenir. */}
        <ul className="flex flex-col py-2">
          <li>
            <Link
              href="/"
              aria-current="page"
              className="block px-6 py-2 text-govde font-medium"
            >
              Adaylar
            </Link>
          </li>
        </ul>
      </nav>

      <main className="min-w-0 flex-1">{children}</main>
    </div>
  );
}
