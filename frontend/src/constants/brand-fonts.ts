import {
  DM_Sans,
  Fira_Sans,
  IBM_Plex_Sans,
  Inter,
  Lato,
  Lora,
  Manrope,
  Merriweather,
  Montserrat,
  Mulish,
  Noto_Sans,
  Nunito,
  Open_Sans,
  Outfit,
  PT_Sans,
  Playfair_Display,
  Plus_Jakarta_Sans,
  Raleway,
  Roboto,
  Rubik,
  Source_Sans_3,
  Ubuntu,
  Work_Sans,
} from "next/font/google"

import { SITE_FONTS } from "@/constants/fonts"

// The fonts a company can pick for its candidates' pages (services/companies constants/brand.py
// lists the same): prepza's pair, Poppins titles over Geist text (the default, which changes
// nothing; the two only together), and single fonts for all the text: the most used web fonts,
// bundled with the site and not preloaded, so a page downloads only the one it uses. Each falls
// back to Geist for letters it lacks. next/font reads its options literally, so each repeats
// them.
const inter = Inter({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})
const roboto = Roboto({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})
const openSans = Open_Sans({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})
const lato = Lato({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
  weight: ["300", "400", "700"],
})
const montserrat = Montserrat({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})
const nunito = Nunito({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})
const raleway = Raleway({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})
const workSans = Work_Sans({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})
const sourceSans3 = Source_Sans_3({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})
const notoSans = Noto_Sans({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})
const ptSans = PT_Sans({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
  weight: ["400", "700"],
})
const ubuntu = Ubuntu({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
  weight: ["300", "400", "500", "700"],
})
const rubik = Rubik({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})
const manrope = Manrope({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})
const dmSans = DM_Sans({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})
const ibmPlexSans = IBM_Plex_Sans({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
  weight: ["300", "400", "500", "600"],
})
const mulish = Mulish({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})
const firaSans = Fira_Sans({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
  weight: ["300", "400", "500", "600"],
})
const plusJakartaSans = Plus_Jakarta_Sans({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})
const outfit = Outfit({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})
const merriweather = Merriweather({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})
const lora = Lora({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})
const playfairDisplay = Playfair_Display({
  preload: false,
  display: "swap",
  subsets: ["latin", "latin-ext"],
})

const fallback = SITE_FONTS.geist

/** By id: prepza's pair first, then the others by name. `family` is what all the text is set in,
 * none for the pair, which draws its name in Poppins. */
export const BRAND_FONTS: Record<string, { label: string; family?: string }> = {
  poppins_geist: { label: "Poppins & Geist" },
  inter: { label: "Inter", family: `${inter.style.fontFamily}, ${fallback}` },
  roboto: {
    label: "Roboto",
    family: `${roboto.style.fontFamily}, ${fallback}`,
  },
  open_sans: {
    label: "Open Sans",
    family: `${openSans.style.fontFamily}, ${fallback}`,
  },
  lato: { label: "Lato", family: `${lato.style.fontFamily}, ${fallback}` },
  montserrat: {
    label: "Montserrat",
    family: `${montserrat.style.fontFamily}, ${fallback}`,
  },
  nunito: {
    label: "Nunito",
    family: `${nunito.style.fontFamily}, ${fallback}`,
  },
  raleway: {
    label: "Raleway",
    family: `${raleway.style.fontFamily}, ${fallback}`,
  },
  work_sans: {
    label: "Work Sans",
    family: `${workSans.style.fontFamily}, ${fallback}`,
  },
  source_sans_3: {
    label: "Source Sans 3",
    family: `${sourceSans3.style.fontFamily}, ${fallback}`,
  },
  noto_sans: {
    label: "Noto Sans",
    family: `${notoSans.style.fontFamily}, ${fallback}`,
  },
  pt_sans: {
    label: "PT Sans",
    family: `${ptSans.style.fontFamily}, ${fallback}`,
  },
  ubuntu: {
    label: "Ubuntu",
    family: `${ubuntu.style.fontFamily}, ${fallback}`,
  },
  rubik: { label: "Rubik", family: `${rubik.style.fontFamily}, ${fallback}` },
  manrope: {
    label: "Manrope",
    family: `${manrope.style.fontFamily}, ${fallback}`,
  },
  dm_sans: {
    label: "DM Sans",
    family: `${dmSans.style.fontFamily}, ${fallback}`,
  },
  ibm_plex_sans: {
    label: "IBM Plex Sans",
    family: `${ibmPlexSans.style.fontFamily}, ${fallback}`,
  },
  mulish: {
    label: "Mulish",
    family: `${mulish.style.fontFamily}, ${fallback}`,
  },
  fira_sans: {
    label: "Fira Sans",
    family: `${firaSans.style.fontFamily}, ${fallback}`,
  },
  plus_jakarta_sans: {
    label: "Plus Jakarta Sans",
    family: `${plusJakartaSans.style.fontFamily}, ${fallback}`,
  },
  outfit: {
    label: "Outfit",
    family: `${outfit.style.fontFamily}, ${fallback}`,
  },
  merriweather: {
    label: "Merriweather",
    family: `${merriweather.style.fontFamily}, ${fallback}`,
  },
  lora: { label: "Lora", family: `${lora.style.fontFamily}, ${fallback}` },
  playfair_display: {
    label: "Playfair Display",
    family: `${playfairDisplay.style.fontFamily}, ${fallback}`,
  },
}
