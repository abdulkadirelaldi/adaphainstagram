import type { Metadata } from "next";
import { Manrope } from "next/font/google";
import { SorguSaglayici } from "@/components/sorgu-saglayici";
import { Kabuk } from "@/components/kabuk";
import "./globals.css";

// Manrope — modern, ferah, humanist grotesk; kurumsal ve okunaklı, jenerik
// system/Inter/Roboto klişesinden uzak. Türkçe için latin-ext.
const arayuz = Manrope({
  variable: "--font-arayuz-src",
  subsets: ["latin", "latin-ext"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Radar",
  description: "Kıyı Medya aday tarama ve denetim paneli",
};

// Tema, ilk boyadan önce <html>'e uygulanır ki tema flaşı (FOUC) olmasın.
// Kullanıcı seçimi localStorage'da; yoksa sistem tercihi (prefers-color-scheme,
// tokens.css tarafından) geçerlidir.
const temaInit = `(function(){try{var t=localStorage.getItem('radar-tema');if(t==='koyu')document.documentElement.classList.add('tema-koyu');else if(t==='acik')document.documentElement.classList.add('tema-acik');}catch(e){}})();`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="tr" className={arayuz.variable} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: temaInit }} />
      </head>
      <body>
        <SorguSaglayici>
          <Kabuk>{children}</Kabuk>
        </SorguSaglayici>
      </body>
    </html>
  );
}
