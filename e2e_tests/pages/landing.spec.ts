import { expect, test, type Page } from "@playwright/test";

import { REQUEST_URL } from "./helpers/env";
import { loaded } from "./helpers/waits";

// The home page: the hero, then its sections in the order of a company's hiring, and the
// closing screen. Every section fits the window on a desktop and on a phone, its pictures hold
// still with reduced motion, and its buttons lead where they say.

const SECTIONS = [
  "how",
  "invite",
  "candidates",
  "reports",
  "agent",
  "trust",
  "compare",
  "pricing",
  "help",
];
const DEMOS = "https://www.youtube.com/@prepza";

type Catalog = {
  currency: string;
  candidate_cents_min: number;
  candidate_cents_max: number;
  free_candidates: number;
  products: {
    key: string;
    price_cents: number;
    candidates: number;
    candidate_cents: number;
  }[];
};

async function catalog(page: Page) {
  const response = await page.request.get(`${REQUEST_URL}/api/billing/catalog`);

  return (await response.json()) as Catalog;
}

// As the site writes a price: whole amounts without cents.
function price(cents: number, currency: string) {
  return new Intl.NumberFormat("en", {
    style: "currency",
    currency,
    maximumFractionDigits: cents % 100 === 0 ? 0 : 2,
  }).format(cents / 100);
}

test("every section shows, in order, within the window", async ({ page }) => {
  // The local dev server compiles the home page on first open.
  test.setTimeout(120_000);
  await page.goto("/");
  const ids = await page
    .locator("main > section")
    .evaluateAll((sections) => sections.map((section) => section.id));
  expect(ids).toEqual(SECTIONS);
  const width = page.viewportSize()!.width;

  for (const id of SECTIONS) {
    const section = page.locator(`#${id}`);
    await section.scrollIntoViewIfNeeded();
    await expect(section.getByRole("heading").first()).not.toBeEmpty();
    // Nothing in it reaches past the window's edges: the page never scrolls sideways.
    const outside = await section.evaluate((element, right) => {
      return [...element.querySelectorAll("*")]
        .filter((part) => {
          const box = part.getBoundingClientRect();

          return box.width > 0 && (box.left < -1 || box.right > right + 1);
        })
        .map((part) => part.outerHTML.slice(0, 120));
    }, width);
    expect(outside, id).toEqual([]);
  }

  const widths = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  expect(widths.scrollWidth).toBeLessThanOrEqual(widths.clientWidth);
});

// In every language the texts fit the window: no word or line runs past its edges (the hero's
// wires, drawn out to the window's edges, aside).
const LOCALES = [
  "ru", "uk", "es", "pt", "de", "fr", "it", "pl", "nl", "tr", "ar", "he", "fa", "ja", "zh", "ko",
  "hi", "id", "th", "vi", "fil", "et",
];

for (const locale of LOCALES) {
  test(`the home page fits the window in ${locale}`, async ({ page }) => {
    test.setTimeout(120_000);
    await page.goto(`/${locale}`);
    const outside = await page.locator("main").evaluate((element, right) => {
      return [...element.querySelectorAll("*")]
        .filter((part) => {
          const box = part.getBoundingClientRect();

          return (
            box.width > 0 &&
            (box.left < -1 || box.right > right + 1) &&
            !part.closest("svg")
          );
        })
        .map((part) => part.outerHTML.slice(0, 120));
    }, page.viewportSize()!.width);
    expect(outside).toEqual([]);
  });
}

test("with reduced motion every picture is a still frame", async ({ page }) => {
  test.setTimeout(120_000);
  await page.emulateMedia({ reducedMotion: "reduce" });
  // The page's timers run on Playwright's clock, so a second and a half passes at once.
  await page.clock.install();
  await page.goto("/");
  await loaded(page);
  // The invite picture's wires are drawn once its cards are laid out, after the page loads.
  await expect(page.locator("#invite svg > g > path").first()).toBeAttached();

  for (const id of SECTIONS) {
    const section = page.locator(`#${id}`);
    await section.scrollIntoViewIfNeeded();
    const before = await section.innerHTML();
    await page.clock.runFor(1_500);
    // Nothing changes, and nothing in sight moves.
    expect(await section.innerHTML(), id).toBe(before);
    const moving = await section.evaluate(
      (element) =>
        element
          .getAnimations({ subtree: true })
          .filter(
            (animation) =>
              animation instanceof CSSAnimation &&
              animation.playState === "running" &&
              ((animation.effect as KeyframeEffect).target as Element).checkVisibility(),
          ).length,
    );
    expect(moving, id).toBe(0);
  }
});

test("the hero's box asks a visitor to sign in to start an interview", async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.goto("/");
  const form = page.locator("main form").first();
  const submit = form.locator('button[type="submit"]');
  await expect(submit).toBeDisabled();
  await form.locator("textarea").fill("A backend developer who knows Python and Postgres");

  await expect(async () => {
    await submit.click();
    await expect(page.getByRole("dialog")).toBeVisible({ timeout: 2_000 });
  }).toPass();
  await expect(page.getByRole("dialog").getByTestId("email-box-noUpdates")).toBeVisible();
});

test("the hero's video button plays the video in a window", async ({ page }) => {
  test.setTimeout(120_000);
  // The player itself isn't loaded: only where the window points it.
  await page.route("https://www.youtube-nocookie.com/**", (route) =>
    route.fulfill({ status: 200, body: "" }),
  );
  await page.goto("/");
  await loaded(page);
  const button = page.getByTestId("video-button").filter({ visible: true });
  await expect(button).toHaveCount(1);

  await expect(async () => {
    await button.click();
    await expect(page.getByRole("dialog")).toBeVisible({ timeout: 2_000 });
  }).toPass();
  const dialog = page.getByRole("dialog");
  await expect(dialog.locator("iframe")).toHaveAttribute(
    "src",
    /^https:\/\/www\.youtube-nocookie\.com\/embed\/[\w-]+/,
  );
  // An icon alone closes it: its label is what screen readers read.
  const close = dialog.getByRole("button");
  await expect(close).toHaveAccessibleName(/.+/);
  await close.click();
  await expect(dialog).toBeHidden();
});

test("the pricing section shows the catalog's top-ups and free candidates", async ({
  page,
}) => {
  test.setTimeout(120_000);
  const prices = await catalog(page);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const section = page.locator("#pricing");
  await section.scrollIntoViewIfNeeded();

  await expect(section).toContainText(String(prices.free_candidates));
  // A row per top-up: its price per candidate, then how many for how much.
  const rows = section.getByTestId("price-list").locator("li");
  await expect(rows).toHaveCount(prices.products.length);

  for (const [index, product] of prices.products.entries()) {
    const row = rows.nth(index);
    await expect(row).toContainText(price(product.candidate_cents, prices.currency));
    await expect(row).toContainText(price(product.price_cents, prices.currency));
    await expect(row).toContainText(String(product.candidates));
  }

  // The receipt pays for the top-up with the lowest price per candidate, marked in the list.
  const cheapest = prices.products.reduce((best, product) =>
    product.candidate_cents < best.candidate_cents ? product : best,
  );
  const used = prices.products.indexOf(cheapest);
  await expect(rows.nth(used)).toHaveAttribute("data-used", "true");
  await expect(section.locator("li[data-used]")).toHaveCount(1);
  await expect(section.getByTestId("receipt-total")).toHaveText(
    price(cheapest.price_cents, prices.currency),
  );
  await expect(section.getByTestId("receipt")).toContainText(String(cheapest.candidates));
  await expect(section.getByRole("link").filter({ visible: true }).last()).toHaveAttribute(
    "href",
    "/pricing",
  );
});

test("the comparison shows prepza's price range from the catalog", async ({ page }) => {
  test.setTimeout(120_000);
  const prices = await catalog(page);
  await page.goto("/");
  const section = page.locator("#compare");
  const range = new Intl.NumberFormat("en", {
    style: "currency",
    currency: prices.currency,
    maximumFractionDigits:
      prices.candidate_cents_min % 100 === 0 && prices.candidate_cents_max % 100 === 0 ? 0 : 2,
  }).formatRange(prices.candidate_cents_min / 100, prices.candidate_cents_max / 100);

  // prepza is the last of the three, with the range.
  const cards = section.locator("li");
  await expect(cards).toHaveCount(3);
  await expect(cards.last()).toContainText(range);
  await expect(section.getByRole("link")).toHaveAttribute("href", "/compare");
});

test("the closing buttons lead to Mira, the videos, the FAQ and the guides", async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.goto("/");
  await loaded(page);
  const closing = page.locator("#help");
  await closing.scrollIntoViewIfNeeded();
  const buttons = closing.locator("div:has(> a[href='/faq']) > *");
  await expect(buttons).toHaveCount(4);
  await expect(buttons.nth(0)).toHaveAttribute("data-assistant-toggle");
  await expect(buttons.nth(1)).toHaveAttribute("href", DEMOS);
  await expect(buttons.nth(1)).toHaveAttribute("target", "_blank");
  await expect(buttons.nth(1)).toHaveAttribute("rel", /noopener/);
  await expect(buttons.nth(2)).toHaveAttribute("href", "/faq");
  await expect(buttons.nth(3)).toHaveAttribute("href", "/guides");

  await buttons.nth(0).click();
  await expect(page.getByRole("dialog")).toBeVisible();
});

test("the guides button opens the guides", async ({ page }) => {
  test.setTimeout(120_000);
  await page.goto("/");
  await loaded(page);
  await page.locator("#help a[href='/guides']").click();
  // The local dev server compiles the guides on first open.
  await expect(page).toHaveURL(/\/guides$/, { timeout: 30_000 });
});
