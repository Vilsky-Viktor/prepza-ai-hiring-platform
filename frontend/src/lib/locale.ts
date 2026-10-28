import {
  LOCALE_COOKIE,
  LOCALE_COOKIE_MAX_AGE,
  LOCALES,
  RTL_LOCALES,
  type Locale,
} from "@/constants/i18n"

export function isLocale(value: string): value is Locale {
  return (LOCALES as readonly string[]).includes(value)
}

/** The way a language is written: right to left for Arabic, Hebrew and Persian. */
export function textDirection(language: string) {
  return RTL_LOCALES.includes(language as Locale) ? "rtl" : "ltr"
}

/** The `lang` and `dir` attributes of text written in `language` (a language's own name, an
 * interview's questions), or none when it isn't known. */
export function languageOf(language: string | null | undefined) {
  return language ? { lang: language, dir: textDirection(language) } : {}
}

export function readLocaleCookie() {
  return document.cookie
    .split("; ")
    .find((item) => item.startsWith(`${LOCALE_COOKIE}=`))
    ?.split("=")[1]
}

export function writeLocaleCookie(locale: Locale) {
  const secure = location.protocol === "https:" ? "; secure" : ""
  document.cookie = `${LOCALE_COOKIE}=${locale}; path=/; max-age=${LOCALE_COOKIE_MAX_AGE}; samesite=lax${secure}`
}

// Traditional Chinese (Taiwan's, Hong Kong's, Macau's, or the Hant script): never given the
// Simplified Chinese that "zh" is.
const TRADITIONAL_CHINESE = /^zh-(?:tw|hk|mo|hant)\b/

/** The first supported language in an Accept-Language header, by preference ("uk-UA,
 * ru;q=0.8" gives uk), or none; Traditional Chinese is not supported. */
export function preferredLocale(header: string | null) {
  const tags = (header ?? "").split(",").map((part) => {
    const [tag, ...params] = part.trim().split(";")
    const quality = params.find((param) => param.trim().startsWith("q="))
    const lower = tag.toLowerCase()

    return {
      code: TRADITIONAL_CHINESE.test(lower) ? lower : lower.split("-")[0],
      quality: quality ? Number(quality.trim().slice(2)) : 1,
    }
  })

  return tags
    .filter((item) => item.quality > 0)
    .sort((a, b) => b.quality - a.quality)
    .map((item) => item.code)
    .find(isLocale)
}
