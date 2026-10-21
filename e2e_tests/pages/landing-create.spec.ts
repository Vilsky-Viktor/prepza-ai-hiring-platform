import { expect, test, type Page } from "@playwright/test";

import { REQUEST_URL } from "./helpers/env";
import { loaded } from "./helpers/waits";

// The home page's "create an interview" section: three panels (the description, the topics and
// the interview made from them), and under them short facts, the first being how many questions
// each topic gets, as generation's public sizes route says.

async function questionsPerTopic(page: Page) {
  const response = await page.request.get(`${REQUEST_URL}/api/generate/sizes`);

  return ((await response.json()) as { questions_per_topic: number }).questions_per_topic;
}

test("the create section shows three panels and the questions per topic", async ({ page }) => {
  test.setTimeout(120_000);
  const count = await questionsPerTopic(page);
  await page.goto("/");
  const section = page.locator("#how");
  await section.scrollIntoViewIfNeeded();

  await expect(section.getByTestId("demo-panel")).toHaveCount(3);
  await expect(section.getByTestId("notes")).toContainText(String(count));
});

test("with reduced motion the create section rests on the finished interview", async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const section = page.locator("#how");
  await section.scrollIntoViewIfNeeded();

  await expect(section.getByTestId("demo-interview")).toBeVisible();
  await expect(section.getByTestId("demo-writing")).toBeHidden();
});

test("on a 375 px phone the notes are one a row, and nothing scrolls sideways", async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/");
  const section = page.locator("#how");
  await section.scrollIntoViewIfNeeded();

  const notes = section.getByTestId("notes").locator("li").filter({ visible: true });
  const count = await notes.count();
  expect(count).toBeGreaterThan(1);
  const tops = await notes.evaluateAll((items) =>
    items.map((item) => Math.round(item.getBoundingClientRect().top)),
  );
  // Each note on a row of its own, one under another.
  expect(new Set(tops).size).toBe(count);
  expect(tops).toEqual([...tops].sort((a, b) => a - b));

  const widths = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  expect(widths.scrollWidth).toBeLessThanOrEqual(widths.clientWidth);
});

// "create an interview" under the reports, beside the prices and on the closing screen: each
// goes back up to the job description box, ready to type.
for (const id of ["reports", "pricing", "help"]) {
  test(`create an interview in #${id} goes to the job description box`, async ({ page }) => {
    test.setTimeout(120_000);
    await page.goto("/");
    await loaded(page);
    const button = page.locator(`#${id}`).getByTestId("start-button");
    await expect(button).toHaveCount(1);
    await button.scrollIntoViewIfNeeded();
    await button.click();

    const box = page.locator("main textarea").first();
    await expect(box).toBeFocused();
    await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
    await expect(box).toBeInViewport();
  });
}
