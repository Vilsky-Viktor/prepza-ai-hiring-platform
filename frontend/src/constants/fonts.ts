import {
  Geist,
  Geist_Mono,
  Noto_Sans,
  Noto_Sans_Arabic,
  Noto_Sans_Devanagari,
  Noto_Sans_Hebrew,
  Noto_Sans_Thai,
  Poppins,
} from "next/font/google"

// The site's fonts. Geist and Poppins carry the design; the Noto fonts cover the scripts they
// lack, for the languages the site speaks (Arabic and Persian, Hebrew, Hindi, Thai, Vietnamese;
// Japanese, Chinese and Korean are in cjk-fonts.ts). Each font's files download only for pages
// with characters in its script, and the script fonts aren't preloaded, so an English page loads
// nothing extra.

const geist = Geist({
  subsets: ["latin", "latin-ext", "cyrillic"],
  variable: "--font-geist",
})

// Code and the API docs only, never on a first screen: not preloaded.
const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  preload: false,
})

// latin-ext for Polish, Turkish and Estonian headings; Vietnamese's letters fall back to Noto.
const poppins = Poppins({
  subsets: ["latin", "latin-ext"],
  weight: ["500", "600"],
  variable: "--font-poppins",
})

// next/font reads its options literally, so each script font repeats them: not preloaded.
const vietnamese = Noto_Sans({
  preload: false,
  display: "swap",
  subsets: ["vietnamese"],
  variable: "--font-vietnamese",
})
const arabic = Noto_Sans_Arabic({
  preload: false,
  display: "swap",
  subsets: ["arabic"],
  variable: "--font-arabic",
})
const hebrew = Noto_Sans_Hebrew({
  preload: false,
  display: "swap",
  subsets: ["hebrew"],
  variable: "--font-hebrew",
})
const devanagari = Noto_Sans_Devanagari({
  preload: false,
  display: "swap",
  subsets: ["devanagari"],
  variable: "--font-devanagari",
})
const thai = Noto_Sans_Thai({
  preload: false,
  display: "swap",
  subsets: ["thai"],
  variable: "--font-thai",
})
// The class names that define every font's CSS variable, for <html>.
export const FONT_VARIABLES = [
  geist,
  geistMono,
  poppins,
  vietnamese,
  arabic,
  hebrew,
  devanagari,
  thai,
].map((font) => font.variable)

// The site's text font by name: what a company's own font falls back to (brand-fonts.ts).
export const SITE_FONTS = { geist: geist.style.fontFamily }
