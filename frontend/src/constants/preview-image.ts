import type { Locale } from "@/constants/i18n"

// The link preview images (lib/preview-image.tsx): the size link previews expect, and the site's
// dark theme (globals.css .dark): background, logo, muted text for the title and the blue dot.
export const PREVIEW_SIZE = { width: 1200, height: 630 }
export const PREVIEW_COLORS = {
  background: "#0a0a0a",
  logo: "#fafafa",
  title: "#a1a1a1",
  dot: "#4c99f8",
}

// The longest title a preview draws: three lines at most.
export const PREVIEW_TITLE_MAX = 90

// Hex characters of a preview's signature (lib/preview-signature.ts): enough that guessing one
// is hopeless, short enough for a tidy address.
export const PREVIEW_SIGNATURE_LENGTH = 32

// Languages the image renderer can't lay out: Arabic and Persian (joined letters), Hebrew
// (right to left) and Hindi (stacked letters). Their pages show the site's own preview.
export const PREVIEW_UNSUPPORTED: readonly Locale[] = ["ar", "fa", "he", "hi"]

// The Google font with the letters Poppins lacks, per language; Noto Sans covers Cyrillic,
// Vietnamese and accented Latin for the rest.
export const PREVIEW_SCRIPT_FONTS: Partial<Record<Locale, string>> = {
  th: "Noto Sans Thai",
  ja: "Noto Sans JP",
  ko: "Noto Sans KR",
  zh: "Noto Sans SC",
}
export const PREVIEW_FALLBACK_FONT = "Noto Sans"
