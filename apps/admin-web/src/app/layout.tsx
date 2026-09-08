import type { Metadata } from "next";
import { Amiri_Quran, IBM_Plex_Mono, IBM_Plex_Sans_Arabic, Noto_Kufi_Arabic } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const plexAr = IBM_Plex_Sans_Arabic({ subsets: ["arabic", "latin"], weight: ["400", "500", "600"], variable: "--font-plex-ar", display: "swap" });
const kufi = Noto_Kufi_Arabic({ subsets: ["arabic"], weight: ["500", "600", "700"], variable: "--font-kufi", display: "swap" });
const amiriQuran = Amiri_Quran({ subsets: ["arabic"], weight: "400", variable: "--font-amiri-quran", display: "swap" });
const plexMono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-plex-mono", display: "swap" });

export const metadata: Metadata = { title: "تَلَقِّي — Talaqqi", description: "Open-source operating system for Quran education" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl" className={`${plexAr.variable} ${kufi.variable} ${amiriQuran.variable} ${plexMono.variable}`} suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
