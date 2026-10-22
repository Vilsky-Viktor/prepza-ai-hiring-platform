import { expect, test, type Page } from "@playwright/test";

// The home page's hero: the page's info button and the video's play icon sit beside the title
// on the start side on wide screens and above it on narrower ones; the play icon is named in its
// tooltip, and its ring holds still with reduced motion; the sentence under the title has each
// of its sentences on a line of its own, in every language.

const LOCALES = [
  "en", "ru", "uk", "es", "pt", "de", "fr", "it", "pl", "nl", "tr", "ar", "he", "fa", "ja", "zh",
  "ko", "hi", "id", "th", "vi", "fil", "et",
];

/** The hero's title, info button and play icon, as boxes on the page. */
async function heroBoxes(page: Page) {
  const title = page.getByRole("heading", { level: 1 });
  const help = page.getByTestId("page-help").filter({ visible: true }).first();
  const video = page.getByTestId("video-button");
  await expect(video).toBeVisible();

  return {
    title: (await title.boundingBox())!,
    help: (await help.boundingBox())!,
    video: (await video.boundingBox())!,
  };
}

test("on a wide screen the icons sit on the title's start side, the video under the info", async ({
  page,
}) => {
  test.skip(test.info().project.name !== "desktop", "a wide screen");
  test.setTimeout(120_000);
  await page.goto("/");
  const { title, help, video } = await heroBoxes(page);

  expect(help.x + help.width).toBeLessThanOrEqual(title.x);
  expect(video.x + video.width).toBeLessThanOrEqual(title.x);
  expect(video.y).toBeGreaterThanOrEqual(help.y + help.height);
});

test("in a right-to-left language the icons sit on the title's right", async ({ page }) => {
  test.skip(test.info().project.name !== "desktop", "a wide screen");
  test.setTimeout(120_000);
  await page.goto("/ar");
  const { title, help, video } = await heroBoxes(page);

  expect(help.x).toBeGreaterThanOrEqual(title.x + title.width);
  expect(video.x).toBeGreaterThanOrEqual(title.x + title.width);
});

test("on a phone the icons sit side by side above the title", async ({ page }) => {
  test.skip(test.info().project.name !== "phone", "a phone");
  test.setTimeout(120_000);
  await page.goto("/");
  const { title, help, video } = await heroBoxes(page);

  expect(help.y + help.height).toBeLessThanOrEqual(title.y);
  expect(video.y + video.height).toBeLessThanOrEqual(title.y);
  expect(video.x).toBeGreaterThanOrEqual(help.x + help.width);
});

test("the play icon is named in its tooltip and its ring holds still with reduced motion", async ({
  page,
}) => {
  test.skip(test.info().project.name !== "desktop", "hovered with a mouse");
  test.setTimeout(120_000);
  await page.goto("/");
  const video = page.getByTestId("video-button");
  // An icon alone: its label is what screen readers read.
  await expect(video).toHaveAccessibleName(/.+/);
  const name = await video.evaluate((element) => element.getAttribute("aria-label"));

  // The tooltip has no ARIA role (Base UI's popup): it's the open popup beside the trigger.
  const tooltip = page.locator("[data-side][data-open][tabindex]");
  await expect(async () => {
    await page.mouse.move(0, 0);
    await video.hover();
    await expect(tooltip).toBeVisible({ timeout: 2_000 });
  }).toPass();
  await expect(tooltip).toHaveText(name!);

  // The ring pulses, and is gone with reduced motion.
  const ring = video.locator("span[aria-hidden]");
  await expect(ring).toBeVisible();
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(ring).toBeHidden();
});

// The facts under the start box, a dot between each two: first the any-job fact, then the
// languages (as many as prepza speaks), the time to ready and no subscription.
test("the facts under the start box start with the any-job fact", async ({ page }) => {
  test.skip(test.info().project.name !== "desktop", "once");
  test.setTimeout(120_000);
  await page.goto("/");
  const proof = page.getByTestId("hero-proof");
  await expect(proof).toBeVisible();

  // Each fact's text, split at the drawn dots; screen readers' commas left out.
  const facts = await proof.evaluate((element) => {
    const parts = [""];

    for (const node of Array.from(element.childNodes)) {
      if (node instanceof HTMLElement && node.getAttribute("aria-hidden") !== null) {
        parts.push("");
      } else if (!(node instanceof HTMLElement && node.classList.contains("sr-only"))) {
        parts[parts.length - 1] += node.textContent ?? "";
      }
    }

    return parts.map((part) => part.trim());
  });

  expect(facts).toHaveLength(4);
  expect(facts[0]).not.toBe("");
  expect(facts[1]).toContain(String(LOCALES.length));
});

for (const locale of LOCALES) {
  test(`the hero's sentences are each on a line of their own in ${locale}`, async ({ page }) => {
    test.skip(test.info().project.name !== "desktop", "once per language");
    test.setTimeout(120_000);
    // English is the plain address; /en is not a page (one URL per language).
    await page.goto(locale === "en" ? "/" : `/${locale}`);
    const lines = page.getByTestId("hero-text").locator("span");
    await expect(lines).toHaveCount(2);
    const [first, second] = [
      (await lines.nth(0).boundingBox())!,
      (await lines.nth(1).boundingBox())!,
    ];

    expect(second.y).toBeGreaterThanOrEqual(first.y + first.height - 1);
  });
}
