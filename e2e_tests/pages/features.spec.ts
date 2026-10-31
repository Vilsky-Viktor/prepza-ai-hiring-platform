import { expect, test, type Page } from "@playwright/test";

import { REQUEST_URL } from "./helpers/env";
import { setScheme } from "./helpers/theme";
import { loaded, scrollAtRest } from "./helpers/waits";

// The features page: the header's link to it, its groups as tabs that stay at the top of the
// window, a picture of the real app per feature in the page's theme, the counts the API gives,
// and the start box at its end. Wording is never checked.

async function counts(page: Page) {
  const [sizes, catalog] = await Promise.all([
    page.request.get(`${REQUEST_URL}/api/generate/sizes`),
    page.request.get(`${REQUEST_URL}/api/billing/catalog`),
  ]);

  return {
    questions: ((await sizes.json()) as { questions_per_topic: number }).questions_per_topic,
    ...((await catalog.json()) as { free_candidates: number; currencies: unknown[] }),
  };
}

test("the header links the features page, whose tabs open each group and stay in view", async ({
  page,
}) => {
  await page.goto("/pricing");
  await page.getByRole("banner").locator('a[href="/features"]').click();
  await expect(page).toHaveURL(/\/features$/);
  await expect(page.getByRole("banner").locator('a[href="/features"]')).toHaveAttribute(
    "aria-current",
    "page",
  );

  // A tab per group, each leading to its section on the page.
  const tabs = page.getByRole("main").locator('[data-sticky-tabs] a[href^="#"]');
  const ids = await tabs.evaluateAll((links) =>
    links.map((link) => link.getAttribute("href")!.slice(1)),
  );
  expect(ids.length).toBeGreaterThan(1);

  for (const id of ids) {
    await expect(page.locator(`main section#${id}`)).toHaveCount(1);
  }

  // The last group opened from its tab: it's the current one, its section in view under the
  // tabs, which stay at the top of the window.
  const last = tabs.last();
  await last.click();
  await expect(last).toHaveAttribute("aria-current", "page");
  await scrollAtRest(page);
  await expect(page.locator(`main section#${ids.at(-1)}`)).toBeInViewport();
  const bar = await page.locator("[data-sticky-tabs]").boundingBox();
  expect(bar?.y).toBe(0);
});

test("each feature shows the picture of the page's theme", { tag: "@phone" }, async ({ page }) => {
  for (const scheme of ["light", "dark"] as const) {
    await setScheme(page, scheme);
    await page.goto("/features");
    await loaded(page);
    const pictures = page.locator('main img[src*="features"]:visible');
    await expect(pictures.first()).toBeVisible();
    const sources = await pictures.evaluateAll((images) =>
      images.map((image) => image.getAttribute("src")!),
    );

    // Every picture shown is its theme's version, and named for screen readers.
    expect(sources.length).toBeGreaterThan(1);
    expect(sources.every((source) => source.includes(`-${scheme}.webp`))).toBe(true);
    // The emails row's picture among them: an invitation email.
    expect(sources.some((source) => source.includes(`email-${scheme}.webp`))).toBe(true);

    for (const picture of await pictures.all()) {
      await expect(picture).toHaveAttribute("alt", /.+/);
    }
  }
});

test("the page shows the API's counts and leads to the start box at its end", async ({ page }) => {
  const { questions, free_candidates: free, currencies } = await counts(page);
  await page.goto("/features");
  await loaded(page);

  await expect(page.locator("main section#create")).toContainText(String(questions));
  // The pricing group's cards: the free candidates first, the currencies prices come in last.
  const pricing = page.locator("main section#pricing").getByTestId("icon-card");
  await expect(pricing.first()).toContainText(String(free));
  await expect(pricing.last()).toContainText(String(currencies.length));
  // The ATSs a company connects, each logo named.
  const logos = page.locator("main section#connect li img");
  expect(await logos.count()).toBeGreaterThan(1);

  for (const logo of await logos.all()) {
    await expect(logo).toHaveAttribute("alt", /.+/);
  }

  // The hero's main button goes down to the start box, where the job description goes.
  await page.getByRole("main").locator('header a[href="#start"]').click();
  await scrollAtRest(page);
  await expect(page.locator("main section#start textarea")).toBeInViewport();
});

test("the features page has its own address in another language", async ({ page }) => {
  await page.goto("/features");
  const english = await page.getByRole("heading", { level: 1 }).textContent();

  await page.goto("/de/features");
  await expect(page.locator("html")).toHaveAttribute("lang", "de");
  const german = page.getByRole("heading", { level: 1 });
  await expect(german).not.toBeEmpty();
  await expect(german).not.toHaveText(english!);
  // Its links onward stay in German.
  await expect(page.getByRole("main").locator('a[href="/de/pricing"]').first()).toBeVisible();
});
