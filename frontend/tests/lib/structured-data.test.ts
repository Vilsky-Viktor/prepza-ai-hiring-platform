import { describe, expect, it } from "vitest"

import {
  articleData,
  breadcrumbData,
  newsData,
  organizationData,
  softwareData,
  techArticleData,
} from "@/lib/structured-data"
import { OPERATOR } from "@/config/operator"
import type { Catalog } from "@/types/billing"

const SITE = "https://prepza.example"

describe("softwareData", () => {
  it("offers the price per candidate from cheapest to dearest", () => {
    const catalog = {
      currency: "USD",
      candidate_cents_min: 100,
      candidate_cents_max: 300,
    } as Catalog

    expect(softwareData(SITE, "Tests.", catalog).offers).toEqual({
      "@type": "AggregateOffer",
      priceCurrency: "USD",
      lowPrice: 1,
      highPrice: 3,
    })
  })
})

describe("breadcrumbData", () => {
  it("numbers each step from the home page with its full address", () => {
    const data = breadcrumbData(SITE, [
      { name: "prepza", path: "/" },
      { name: "Skills tests", path: "/tests" },
    ])

    expect(data.itemListElement).toEqual([
      { "@type": "ListItem", position: 1, name: "prepza", item: `${SITE}/` },
      {
        "@type": "ListItem",
        position: 2,
        name: "Skills tests",
        item: `${SITE}/tests`,
      },
    ])
  })
})

describe("organizationData", () => {
  it("names the brand without the logo's dot", () => {
    const [organization, website] = organizationData(SITE, "Tests.")

    expect(organization.name).toBe("prepza")
    expect(website.url).toBe(SITE)
  })

  it("names the legal operator, its address and email", () => {
    const [organization] = organizationData(SITE, "Tests.")

    expect(organization.legalName).toBe(OPERATOR.name)
    expect(organization.address).toEqual({
      "@type": "PostalAddress",
      streetAddress: "Sepapaja tn 6",
      postalCode: "15551",
      addressLocality: "Tallinn",
      addressRegion: "Harju maakond",
      addressCountry: "EE",
    })
    expect(organization.email).toBe(OPERATOR.email)
  })
})

describe("articleData", () => {
  it("names the article's address, picture, language and date", () => {
    const data = articleData(SITE, {
      title: "Hiring engineers",
      description: "How to test engineers.",
      path: "/de/guides/hiring-engineers",
      updated: "2026-10-08",
      language: "de",
      image: `${SITE}/preview?title=Hiring+engineers&lang=de`,
    })

    expect(data).toMatchObject({
      "@type": "Article",
      headline: "Hiring engineers",
      url: `${SITE}/de/guides/hiring-engineers`,
      image: `${SITE}/preview?title=Hiring+engineers&lang=de`,
      inLanguage: "de",
      dateModified: "2026-10-08",
    })
  })
})

describe("techArticleData", () => {
  it("names the API docs as an English technical article with its picture", () => {
    const data = techArticleData(SITE, {
      title: "API docs",
      description: "The API reference.",
      path: "/api-docs",
      image: `${SITE}/preview`,
    })

    expect(data).toMatchObject({
      "@type": "TechArticle",
      headline: "API docs",
      url: `${SITE}/api-docs`,
      image: `${SITE}/preview`,
      inLanguage: "en",
    })
  })
})

describe("newsData", () => {
  it("lists the posts as the language's blog posts by prepza, each at its place", () => {
    const data = newsData(
      SITE,
      {
        title: "prepza news",
        description: "What's new.",
        path: "/de/news",
        language: "de",
      },
      [
        {
          id: "p1",
          title: "Neu",
          text: "Text.",
          published_on: "2026-10-08",
          updated_at: "2026-10-08T09:30:00Z",
        },
      ]
    )

    expect(data).toMatchObject({
      "@type": "Blog",
      url: `${SITE}/de/news`,
      inLanguage: "de",
      publisher: { "@type": "Organization", name: "prepza" },
    })
    expect(data.blogPost).toEqual([
      {
        "@type": "BlogPosting",
        headline: "Neu",
        articleBody: "Text.",
        url: `${SITE}/de/news#p1`,
        datePublished: "2026-10-08",
        dateModified: "2026-10-08T09:30:00Z",
        inLanguage: "de",
        author: { "@type": "Organization", name: "prepza", url: SITE },
        publisher: { "@type": "Organization", name: "prepza", url: SITE },
      },
    ])
  })
})
