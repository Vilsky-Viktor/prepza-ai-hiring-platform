---
paths:
  - "frontend/src/app/**"
  - "frontend/content/**"
  - "frontend/src/lib/site.ts"
  - "frontend/src/lib/locale-path.ts"
  - "frontend/src/lib/structured-data.ts"
  - "frontend/src/config/seo.ts"
  - "frontend/src/config/i18n.ts"
  - "frontend/src/proxy.ts"
---

# SEO for public pages

## Languages

- One URL per language: English plain, the others under their prefix (`/de/pricing`). Never pick
  a public page's language from the browser or a cookie for the same URL, never redirect by it;
  visitors switch language through plain `<a>` links to the other versions.
- Every version lists every version, itself included, plus `x-default` (the plain English URL),
  with absolute URLs, in the head and the sitemap from the same helper, so they agree.
- hreflang codes are ISO 639-1, with a script or region where needed (`zh-Hans`); never
  three-letter codes (`fil` maps to `tl` for hreflang only; URLs keep their prefix).
- A version whose main content isn't translated is a duplicate: its canonical is the English
  URL, it lists only real translations, and it stays out of the sitemap.

## Metadata

- Through `pageMetadata()` only: a unique, descriptive title (the brand after a delimiter; the
  layout adds " · prepza.") and a unique description that leads with the key fact (snippets are
  cut near 155 characters); an absolute self-canonical in the page's own language;
  `metadataBase` in the root layout; metadata always in `<head>` (`htmlLimitedBots`).
- A page's `openGraph` replaces the layout's whole object: set every field. Link previews have
  `og:title`, `og:description`, `og:url` (the canonical), a 1200×630 `og:image` with `alt`,
  `og:locale` and `og:locale:alternate`, and `twitter:card` `summary_large_image`.
- Article front matter limits are `.claude/rules/content-i18n.md`'s; tests check them for every
  file in every folder and language.

## Indexing and the sitemap

- Private and signed-in pages are crawlable and `noindex` (`X-Robots-Tag`); robots.txt blocks
  only non-pages (`/api/`, `/monitoring`), never used for canonicals. Thin or duplicate pages are
  `noindex` and out of the sitemap, as the API decides (`indexable`). Downtime answers 503.
- The sitemap lists every indexable page in every language it exists in, absolute URLs, a
  `lastmod` from that language's own real date (front matter `updated`), nothing else (no
  `priority` or `changefreq`); split with `generateSitemaps` past 50,000 URLs.
- Links are crawlable `<a href>` elements.

## Structured data

- JSON-LD from `lib/structured-data.ts`, escaped (`components/common/json-ld.tsx`); only types Google
  documents and only facts the page shows. Organization (name, url, a crawlable logo of at least
  112 px, `sameAs`, a full `PostalAddress`) and WebSite on the home or about page; Article with
  `headline`, `image`, `dateModified` and the canonical as `url`; BreadcrumbList with absolute
  URLs. FAQPage markup brings no rich result any more but may stay.
- No invented ratings or reviews; `aggregateRating` only from real reviews; only properties
  schema.org defines for the type.

## Content

- Helpful, people-first pages; programmatic or AI-assisted pages add real value or stay
  `noindex`, never scaled thin content.
- Tests check structure and data (a canonical equals the page's URL, hreflang sets are
  symmetric, lengths are within limits, private paths are `noindex`), never titles' wording.

Research (local notes, git-ignored): `internal_docs/best-practices/seo.md`.
