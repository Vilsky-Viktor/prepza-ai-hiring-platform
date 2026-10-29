import type { Page } from "@playwright/test";

import { REQUEST_URL } from "./helpers/env";
import { expect, test } from "./helpers/templates";

// What search engines and link previews read beyond seo.spec.ts: each page's own description,
// private pages kept out, template pages' breadcrumbs and text direction (on the test's own
// throwaway templates), articles' data, and the preview picture. Each page's own title, naming
// the site once, is in public-heads.spec.ts.


// Written right to left: their lists of topics and questions mirror.
const RTL = ["ar", "he", "fa"];

function description(page: Page) {
  return page
    .locator('head meta[name="description"]')
    .first()
    .getAttribute("content");
}

async function structuredData(page: Page) {
  const scripts = await page
    .locator('script[type="application/ld+json"]')
    .allTextContents();

  return scripts.flatMap((text) => [JSON.parse(text)].flat());
}

test("the FAQ, pricing, about and contact pages have their own descriptions", async ({
  page,
}) => {
  for (const path of ["/faq", "/pricing", "/about", "/contact"]) {
    await page.goto(path);
    const intro = await page
      .locator("main header p, main p")
      .first()
      .textContent();
    const text = (await description(page)) ?? "";

    expect(text.length, path).toBeGreaterThan(100);
    expect(text.length, path).toBeLessThanOrEqual(170);
    expect(text, path).not.toBe(intro);
  }
});

// English only, like the legal pages: one address, no language versions, its own description,
// its title with its capitals in the preview picture, a technical article with breadcrumbs, in
// the sitemap.
test("the developer docs have their description, data and place in the sitemap", async ({
  page,
}) => {
  await page.goto("/api-docs");

  const heading = await page.getByRole("heading", { level: 1 }).textContent();
  const text = (await description(page)) ?? "";
  expect(text.length).toBeGreaterThan(100);
  expect(text.length).toBeLessThanOrEqual(170);
  expect(
    await page.locator('head link[rel="canonical"]').getAttribute("href"),
  ).toMatch(/\/api-docs$/);
  await expect(page.locator('head link[rel="alternate"][hreflang]')).toHaveCount(0);
  const picture = await page
    .locator('head meta[property="og:image"]')
    .first()
    .getAttribute("content");
  expect(new URL(picture ?? "").searchParams.get("title")).toBe(heading);

  const data = await structuredData(page);
  const article = data.find((item) => item["@type"] === "TechArticle");
  expect(article).toMatchObject({ inLanguage: "en", description: text, image: picture });
  const crumbs = data.find((item) => item["@type"] === "BreadcrumbList");
  expect(
    crumbs.itemListElement.map((step: { item: string }) => new URL(step.item).pathname),
  ).toEqual(["/", "/api-docs"]);

  const sitemap = await (await page.request.get(`${REQUEST_URL}/sitemap.xml`)).text();
  expect(sitemap).toContain("/api-docs</loc>");
});

test("the legal pages are dated in the sitemap by their last update", async ({
  page,
}) => {
  const sitemap = await (await page.request.get(`${REQUEST_URL}/sitemap.xml`)).text();

  for (const path of ["/privacy", "/terms", "/dpa"]) {
    const legal = await (
      await page.request.get(`${REQUEST_URL}/api/site/help/legal${path}`)
    ).json();
    expect(sitemap.replace(/\s+/g, ""), path).toContain(
      `${path}</loc><lastmod>${legal.current}</lastmod>`,
    );
  }
});

// Private pages and personal links, even when shared in a job ad, stay out of search results;
// a public page doesn't.
test("private pages and personal links say noindex; public ones don't", async ({ page }) => {
  for (const path of ["/companies", "/apply/abc", "/invite/abc", "/join/abc", "/unsubscribe"]) {
    const response = await page.request.get(`${REQUEST_URL}${path}`);

    expect(response.headers()["x-robots-tag"], path).toBe("noindex");
  }

  const publicPage = await page.request.get(`${REQUEST_URL}/pricing`);
  expect(publicPage.headers()["x-robots-tag"]).toBeUndefined();
});

test("the FAQ page's structured data lists its questions", async ({ page }) => {
  await page.goto("/faq");
  const faq = (await structuredData(page)).find(
    (item) => item["@type"] === "FAQPage",
  );

  expect(faq.mainEntity.length).toBeGreaterThan(0);
  // An answer with a link reads as the page shows it: the link's text, without its address.
  const linked = page
    .getByRole("main")
    .locator("details")
    .filter({ has: page.locator('a[href="/pricing"]') });
  const question = (await linked.locator("summary").textContent())!.trim();
  const shown = (await linked.locator("summary + *").textContent())!.trim();
  const entry = faq.mainEntity.find(
    (item: { name: string }) => item.name === question,
  );

  expect(entry.acceptedAnswer.text).toBe(shown);
  expect(JSON.stringify(faq)).not.toContain("](");
});

test("an article names its picture, language and date, and shows the date as words", async ({
  page,
}) => {
  await page.goto("/de/guides/hiring-engineers");
  const article = (await structuredData(page)).find(
    (item) => item["@type"] === "Article",
  );
  const picture = await page
    .locator('head meta[property="og:image"]')
    .first()
    .getAttribute("content");

  expect(article.inLanguage).toBe("de");
  expect(article.image).toBe(picture);
  expect(article.dateModified).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  // The German date, not the ISO one.
  const date = page.locator("main header time");
  await expect(date).toHaveAttribute("datetime", article.dateModified);
  await expect(date).toHaveText(/^\d{2}\.\d{2}\.\d{4}$/);
});

test("a free practice page has breadcrumbs, and template text has its direction", async ({
  page,
  addTemplate,
}) => {
  // Five pages, which the dev server may compile first.
  test.setTimeout(120_000);
  const english = await addTemplate("en");
  const arabic = await addTemplate("ar");

  await page.goto(`/practice/${english.slug}`);
  const crumbs = (await structuredData(page)).find(
    (item) => item["@type"] === "BreadcrumbList",
  );
  expect(
    crumbs.itemListElement.map(
      (step: { item: string }) => new URL(step.item).pathname,
    ),
  ).toEqual(["/", "/practice", `/practice/${english.slug}`]);
  expect(crumbs.itemListElement[2].name).toBe(english.title);

  for (const template of [english, arabic]) {
    const direction = RTL.includes(template.language) ? "rtl" : "ltr";

    for (const base of ["/practice", "/tests"]) {
      await page.goto(`${base}/${template.slug}`);
      const topics = page.locator("main ul[lang]").first();
      await expect(topics).toHaveAttribute("lang", template.language);
      await expect(topics).toHaveAttribute("dir", direction);
    }
  }
});

test("the preview picture draws only signed titles, and is kept out of image search", async ({
  page,
}) => {
  // The pricing page names its own picture, signed; the same address with another title isn't.
  await page.goto("/pricing");
  const named = new URL(
    (await page.locator('meta[property="og:image"]').getAttribute("content")) ?? "",
  );
  expect(named.pathname).toBe("/preview");
  expect(named.searchParams.get("sig")).toMatch(/^[0-9a-f]{32}$/);
  const image = await page.request.get(`${REQUEST_URL}${named.pathname}${named.search}`);
  named.searchParams.set("title", "Anything someone else wrote");
  const forged = await page.request.get(`${REQUEST_URL}${named.pathname}${named.search}`);
  const robots = await (
    await page.request.get(`${REQUEST_URL}/robots.txt`)
  ).text();

  expect(image.status()).toBe(200);
  expect(image.headers()["x-robots-tag"]).toBe("noindex");
  expect(forged.status()).toBe(404);
  expect(robots).not.toContain("Disallow: /preview");
});
