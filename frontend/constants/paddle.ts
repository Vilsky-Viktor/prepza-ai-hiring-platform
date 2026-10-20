// Paddle's checkout comes in en, de, es, fr, it, ja, ko, nl, sv, no, da, pl, pt, ru, zh-Hans,
// zh-Hant, ar and tr: the site's languages it has, by Paddle's code ("zh" is Simplified
// Chinese). Any other language opens it in English.
export const PADDLE_LOCALES: Record<string, string> = {
  ar: "ar",
  de: "de",
  en: "en",
  es: "es",
  fr: "fr",
  it: "it",
  ja: "ja",
  ko: "ko",
  nl: "nl",
  pl: "pl",
  pt: "pt",
  ru: "ru",
  tr: "tr",
  zh: "zh-Hans",
}
export const PADDLE_FALLBACK_LOCALE = "en"
