import type { Metadata } from "next";
import { Archivo, IBM_Plex_Mono } from "next/font/google";
import { SorguSaglayici } from "@/components/sorgu-saglayici";
import { Kabuk } from "@/components/kabuk";
import "./globals.css";

const arayuz = Archivo({
  variable: "--font-arayuz-src",
  subsets: ["latin", "latin-ext"],
  display: "swap",
});

const sayi = IBM_Plex_Mono({
  variable: "--font-sayi-src",
  subsets: ["latin", "latin-ext"],
  weight: ["400", "500"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Radar",
  description: "Kıyı Medya aday tarama ve denetim paneli",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="tr">
      <body className={`${arayuz.variable} ${sayi.variable}`}>
        <SorguSaglayici>
          <Kabuk>{children}</Kabuk>
        </SorguSaglayici>
      </body>
    </html>
  );
}
