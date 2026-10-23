import { REQUEST_URL } from "./helpers/env";
import { expect, test } from "./helpers/templates";

// What search engines see of the template pages, the sitemap and robots.txt, checked on the
// test's own throwaway templates (helpers/templates.ts).

/** The links on a page drawn as the site's buttons with words, in order (the back arrow, an
 * icon, isn't one of them). */
function buttonLinks(page: import("@playwright/test").Page) {
  return page
    .locator("main a[data-slot=button]:not([aria-label])")
    .evaluateAll((links) => links.map((link) => link.getAttribute("href")));
}

// The two ways on are links drawn as the site's buttons: creating a test first, practising it
// second.
test("a role test page is for hiring, with the way to practise second", async ({
  page,
  addTemplate,
}) => {
  const template = await addTemplate();
  await page.goto(`/tests/${template.slug}`);

  await expect(page.locator("h1")).toContainText(template.title);
  expect(await buttonLinks(page)).toEqual(["/", `/practice/${template.slug}`]);
  const data = await page
    .locator('script[type="application/ld+json"]')
    .allTextContents();
  expect(data.join()).toContain('"@type":"BreadcrumbList"');
  // The site FAQ's answers to companies' questions, opening on a click; no FAQ data, as the
  // same answers repeat on every role page (/faq carries it).
  const faq = page.locator("main section").filter({ has: page.locator("details") });
  await expect(faq.locator("details")).toHaveCount(5);
  const first = faq.locator("details").first();
  await expect(first).not.toHaveAttribute("open");
  await first.locator("summary").click();
  await expect(first).toHaveAttribute("open");
  expect(data.join()).not.toContain('"@type":"FAQPage"');
});

// A template's pages (role test and free practice) exist in English and in the template's
// language only: an English template's pages have no other language versions, and their
// addresses under another language aren't found.
test("a template's pages are only in English and its template's language", async ({
  page,
  addTemplate,
}) => {
  const template = await addTemplate();

  for (const base of ["/tests", "/practice"]) {
    await page.goto(`${base}/${template.slug}`);
    await expect(page.locator('head link[rel="alternate"][hreflang]')).toHaveCount(0);
    const other = await page.request.get(`${REQUEST_URL}/de${base}/${template.slug}`);
    expect(other.status()).toBe(404);
  }
});

test("old addresses move to their readable ones for good", async ({ page, addTemplate }) => {
  const template = await addTemplate();

  const practice = await page.request.get(`${REQUEST_URL}/practice/${template.id}`, {
    maxRedirects: 0,
  });
  expect(practice.status()).toBe(308);
  expect(practice.headers().location).toBe(`/practice/${template.slug}`);

  const companies = await page.request.get(`${REQUEST_URL}/company/abc/interviews`, {
    maxRedirects: 0,
  });
  expect(companies.status()).toBe(308);
  expect(companies.headers().location).toBe("/companies/abc/interviews");
});

test("robots.txt and the sitemap list what should be found", async ({
  page,
  addTemplate,
}) => {
  const full = await addTemplate("en", 3);
  const thin = await addTemplate("en", 1);
  const robots = await (await page.request.get(`${REQUEST_URL}/robots.txt`)).text();
  expect(robots).toContain("Disallow: /api/");
  expect(robots).not.toContain("Disallow: /companies");
  expect(robots).toContain("/sitemap.xml");

  const sitemap = await (await page.request.get(`${REQUEST_URL}/sitemap.xml`)).text();

  // Only the templates the API calls indexable (enough topics, not a near-duplicate).
  for (const [template, indexable] of [
    [full, true],
    [thin, false],
  ] as const) {
    for (const base of ["/tests", "/practice"]) {
      const listed = sitemap.includes(`${base}/${template.slug}</loc>`);
      expect(listed, `${base}/${template.slug}`).toBe(indexable);
    }
  }

  for (const path of [
    "/de/pricing",
    "/tests",
    "/compare/testgorilla",
    "/guides/hiring-engineers",
    "/pre-employment-testing",
    "/de/guides/hiring-engineers",
    "/ja/compare/testgorilla",
  ]) {
    expect(sitemap).toContain(`${path}</loc>`);
  }

  expect(sitemap).toContain('hreflang="x-default"');
});

// A template the API doesn't call indexable (too few topics, or a near-duplicate) keeps its pages
// out of search results; an indexable one doesn't.
test("only an indexable template's pages may be found", async ({ page, addTemplate }) => {
  const thin = await addTemplate("en", 1);
  const full = await addTemplate("en", 3);

  for (const [template, robots] of [
    [thin, "noindex"],
    [full, null],
  ] as const) {
    for (const base of ["/tests", "/practice"]) {
      await page.goto(`${base}/${template.slug}`);
      // Read at once: an indexable page has no robots tag to wait for.
      const meta = await page
        .locator('head meta[name="robots"]')
        .evaluateAll((tags) => tags.map((tag) => tag.getAttribute("content")).join());
      expect(meta.includes("noindex") ? "noindex" : null).toBe(robots);
    }
  }
});

// A template in another language has its pages at that language's address too: their links,
// back to the list, to the home page and between its two pages, stay in it, and the page (its
// level among it) is in that language, unlike the English one.
test("a template's page in its language keeps its links and level in it", async ({
  page,
  addTemplate,
}) => {
  const template = await addTemplate("de");
  const level = page.locator("main [data-slot=badge]").first();

  await page.goto(`/tests/${template.slug}`);
  const english = { heading: await page.locator("h1").textContent(), level: await level.textContent() };

  await page.goto(`/de/tests/${template.slug}`);
  await expect(page.locator("html")).toHaveAttribute("lang", "de");
  await expect(page.locator("h1")).toContainText(template.title);
  await expect(page.locator("h1")).not.toHaveText(english.heading!);
  await expect(level).not.toHaveText(english.level!);
  await expect(page.locator('main a[href="/de/tests"]')).toHaveCount(1);
  expect(await buttonLinks(page)).toEqual(["/de", `/de/practice/${template.slug}`]);

  await page.goto("/de/tests");
  await expect(page.locator(`a[href="/de/tests/${template.slug}"]`)).toHaveCount(1);
});
