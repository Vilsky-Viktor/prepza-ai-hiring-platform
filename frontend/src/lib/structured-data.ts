import { FOUNDER } from "@/config/about"
import { OPERATOR, OPERATOR_POSTAL_ADDRESS } from "@/config/operator"
import { SITE_NAME } from "@/config/seo"
import { moneyAmount } from "@/lib/format"
import type { Catalog } from "@/types/billing"

// schema.org structured data for search engines and AI answers: who makes testee, what it is and
// costs, and where a page sits. `site` is the site's address (lib/site.ts siteUrl).

const CONTEXT = "https://schema.org"
const BRAND = SITE_NAME.replace(/\.$/, "")

/** The company and the site, for the home page. */
export function organizationData(site: string, description: string) {
  return [
    {
      "@context": CONTEXT,
      "@type": "Organization",
      name: BRAND,
      legalName: OPERATOR.name,
      email: OPERATOR.email,
      address: { "@type": "PostalAddress", ...OPERATOR_POSTAL_ADDRESS },
      url: site,
      logo: `${site}/icon.png`,
      founder: { "@type": "Person", name: FOUNDER.name },
      sameAs: [FOUNDER.linkedin],
    },
    {
      "@context": CONTEXT,
      "@type": "WebSite",
      name: BRAND,
      url: site,
      description,
    },
  ]
}

/** testee as a product with its price per candidate, cheapest to dearest, for the pricing
 * page: only properties schema.org defines for an AggregateOffer, and no rating until real
 * reviews exist. */
export function softwareData(
  site: string,
  description: string,
  catalog: Catalog
) {
  return {
    "@context": CONTEXT,
    "@type": "SoftwareApplication",
    name: BRAND,
    url: site,
    description,
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    offers: {
      "@type": "AggregateOffer",
      priceCurrency: catalog.currency,
      lowPrice: moneyAmount(catalog.candidate_cents_min, catalog.currency),
      highPrice: moneyAmount(catalog.candidate_cents_max, catalog.currency),
    },
  }
}

/** The founder, for the about page. */
export function personData(site: string) {
  return {
    "@context": CONTEXT,
    "@type": "Person",
    name: FOUNDER.name,
    image: `${site}${FOUNDER.photo}`,
    sameAs: [FOUNDER.linkedin],
    worksFor: { "@type": "Organization", name: BRAND, url: site },
  }
}

/** Where a page sits under the home page: each step's name and path, the page itself last. */
export function breadcrumbData(
  site: string,
  steps: { name: string; path: string }[]
) {
  return {
    "@context": CONTEXT,
    "@type": "BreadcrumbList",
    itemListElement: steps.map((step, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: step.name,
      item: `${site}${step.path}`,
    })),
  }
}

/** An article (a guide, a comparison or a pillar page) with its date, language and preview
 * picture. */
export function articleData(
  site: string,
  page: {
    title: string
    description: string
    path: string
    updated: string
    language: string
    image: string
  }
) {
  return {
    "@context": CONTEXT,
    "@type": "Article",
    headline: page.title,
    description: page.description,
    url: `${site}${page.path}`,
    image: page.image,
    inLanguage: page.language,
    dateModified: page.updated,
    author: { "@type": "Person", name: FOUNDER.name, url: `${site}/about` },
    publisher: { "@type": "Organization", name: BRAND, url: site },
  }
}

/** The API docs as a technical reference in English, with its preview picture. */
export function techArticleData(
  site: string,
  page: { title: string; description: string; path: string; image: string }
) {
  return {
    "@context": CONTEXT,
    "@type": "TechArticle",
    headline: page.title,
    description: page.description,
    url: `${site}${page.path}`,
    image: page.image,
    inLanguage: "en",
    publisher: { "@type": "Organization", name: BRAND, url: site },
  }
}

/** The news page as a blog in its language, with its posts (as the page shows them) as blog
 * posts by testee, each at its place on the page. */
export function newsData(
  site: string,
  page: { title: string; description: string; path: string; language: string },
  posts: {
    id: string
    title: string
    text: string
    published_on: string
    updated_at: string
  }[]
) {
  const url = `${site}${page.path}`
  const organization = { "@type": "Organization", name: BRAND, url: site }

  return {
    "@context": CONTEXT,
    "@type": "Blog",
    name: page.title,
    description: page.description,
    url,
    inLanguage: page.language,
    publisher: organization,
    blogPost: posts.map((post) => ({
      "@type": "BlogPosting",
      headline: post.title,
      articleBody: post.text,
      url: `${url}#${post.id}`,
      datePublished: post.published_on,
      dateModified: post.updated_at,
      inLanguage: page.language,
      author: organization,
      publisher: organization,
    })),
  }
}
