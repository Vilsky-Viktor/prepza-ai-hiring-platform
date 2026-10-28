import type { BrandColors } from "@/types/company"

// A company's colors on its candidates' pages, in groups like a theme's: each a background and
// the text on it (services/companies constants/brand.py checks they read).
export const BRAND_GROUPS = [
  { id: "page", colors: ["background", "foreground"] },
  { id: "primary", colors: ["primary", "primary_foreground"] },
  { id: "secondary", colors: ["muted", "muted_foreground"] },
  { id: "dialogs", colors: ["card", "card_foreground"] },
  { id: "borders", colors: ["border"] },
] as const satisfies readonly {
  id: string
  colors: readonly (keyof BrandColors)[]
}[]

// The site's theme variables each color sets, so every component on those pages takes them.
export const BRAND_VARIABLES: Record<keyof BrandColors, string[]> = {
  background: ["--background"],
  foreground: ["--foreground", "--secondary-foreground", "--accent-foreground"],
  card: ["--card", "--popover"],
  card_foreground: ["--card-foreground", "--popover-foreground"],
  primary: ["--primary", "--ring"],
  primary_foreground: ["--primary-foreground"],
  muted: ["--muted", "--secondary", "--accent", "--surface"],
  muted_foreground: ["--muted-foreground"],
  border: ["--border", "--input"],
}

// A whole color code, as companies takes it.
export const HEX_COLOR = /^#[0-9a-fA-F]{6}$/
