import type { Locale } from "@/config/i18n"

export const SITE_NAME = "prepza."

// Private areas: signed-in pages and personal links. They're served with "noindex" (proxy.ts),
// so they stay out of search results even when a link to one is public (a job ad's link).
export const PRIVATE_PATHS = [
  "/api/",
  "/apply",
  "/companies",
  "/connect",
  "/embedded",
  "/generate",
  "/invite",
  "/join",
  "/monitoring",
  "/practice/history",
  "/practice/rounds",
  "/practice/*/start",
  "/sessions",
  "/settings",
  "/superadmin",
  "/top-up",
  "/unsubscribe",
]

// Not crawled at all: the API and Sentry's tunnel aren't pages.
export const UNCRAWLED_PATHS = ["/api/", "/monitoring"]

// Public pages listed in the sitemap.
export const PUBLIC_PATHS = [
  "/",
  "/features",
  "/pricing",
  "/privacy",
  "/terms",
  "/dpa",
  "/documents",
  "/api-docs",
  "/faq",
  "/about",
  "/contact",
  "/accessibility",
  "/trust",
  "/news",
  "/practice",
]

// Public pages also served in every other language under its prefix (/de/pricing), linked to
// each other with hreflang. Other pages have one address and follow the visitor's language.
export const LOCALIZED_PATHS = [
  "/",
  "/features",
  "/pricing",
  "/faq",
  "/about",
  "/contact",
  "/accessibility",
  "/trust",
  "/documents",
  "/practice",
  "/tests",
  "/compare",
  "/guides",
  "/pre-employment-testing",
  "/ai-interviews",
  "/news",
]

// Articles also have an address in every language: in a language without a translation yet they
// show the English text, and name only their real translations for hreflang.
export const LOCALIZED_ARTICLE = /^\/(compare|guides)\/[a-z0-9-]+$/

// A template's pages (its role test page and its free practice test) have an address in the
// template's language besides English (/de/tests/<slug> for a German template); the page itself
// answers "not found" in any other language.
export const TEMPLATE_PAGE = /^\/(tests|practice)\/[a-z0-9-]+$/

// The news page's RSS feed, also served in every other language under its prefix
// (/de/news/rss.xml); not a page, so it isn't in the sitemap.
export const NEWS_FEED = "/news/rss.xml"

// Set by proxy.ts on a request that came in under a language prefix: that language, which the
// page then renders in and names as its canonical address.
export const LOCALE_HEADER = "x-prepza-locale"

// Set by proxy.ts on the plain address of a page that has language versions (/pricing): it is
// the English page whatever language the visitor chose before, as its canonical and hreflang say.
export const PLAIN_ADDRESS_HEADER = "x-prepza-plain"

// hreflang codes where a language's own code isn't the one search engines read: Filipino has no
// two-letter code (Tagalog's stands for it), and Chinese names its script. Addresses keep their
// own prefix (/fil/, /zh/).
export const HREFLANG_CODES: Partial<Record<Locale, string>> = {
  fil: "tl",
  zh: "zh-Hans",
}
