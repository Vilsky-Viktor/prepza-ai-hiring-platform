const NAMES = new Intl.DisplayNames(["en"], {
  type: "language",
  languageDisplay: "standard",
})

/** A language's name in English ("Arabic", "Filipino"), so anyone can find their own whatever
 * the page's language is; Chinese names its script, as the site's is Simplified. */
export function englishLanguageName(locale: string) {
  return NAMES.of(locale === "zh" ? "zh-Hans" : locale) ?? locale
}
