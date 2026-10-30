import { expect, test, type Locator, type Page } from "@playwright/test";

import { REQUEST_URL } from "./helpers/env";
import { pauseClock } from "./helpers/clock";
import { loaded } from "./helpers/waits";

// The home page's "create an interview" section: one frame playing the three steps, a numbered
// pill on its top edge naming the one shown; under it, short facts, one being how many questions
// each topic gets, as generation's public sizes route says. On phones, the steps as cards.

async function questionsPerTopic(page: Page) {
  const response = await page.request.get(`${REQUEST_URL}/api/generate/sizes`);

  return ((await response.json()) as { questions_per_topic: number }).questions_per_topic;
}

/** Where `frame` is on the page, rounded: its size and its place from the page's top. */
function frameBox(frame: Locator) {
  return frame.evaluate((element) => {
    const box = element.getBoundingClientRect();

    return [box.width, box.height, box.left, box.top + window.scrollY].map(Math.round).join();
  });
}

test("with reduced motion the create section rests on the finished interview and its counts", async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const section = page.locator("#how");
  await section.scrollIntoViewIfNeeded();

  await expect(section.getByTestId("demo-interview")).toBeVisible();
  await expect(section.getByTestId("demo-writing")).toBeHidden();
  // The pill names the last step.
  await expect(section.getByTestId("create-step").last()).toHaveAttribute("data-current", "true");

  // Its topic rows each show how many questions were written for the topic:
  // DEMO_INTERVIEW.topicQuestions (frontend/src/config/create-demo.ts), not what one candidate
  // gets (the demo is hidden from screen readers, so it has no roles to find it by).
  const rows = section.getByTestId("demo-interview").locator("ul").last().locator("li");
  await expect(rows).not.toHaveCount(0);

  for (const row of await rows.all()) {
    await expect(row).toContainText("70");
  }
});

// The pill names each step in turn, as the frame shows it, and the frame never changes size or
// place. The clock runs three seconds at a time (each stage lasts far longer), so a busy page
// still gets through the demo in time.
test("the create demo's pill names each step in turn and the frame never moves", async ({
  page,
}) => {
  test.setTimeout(360_000);
  const count = await questionsPerTopic(page);
  await page.clock.install();
  await page.goto("/");
  await loaded(page);
  // Time stands still from here on, moving only as the test runs it.
  await pauseClock(page);
  const section = page.locator("#how");
  await section.scrollIntoViewIfNeeded();
  await expect(section.getByTestId("notes")).toContainText(String(count));
  const frame = section.getByTestId("demo-panel");
  await expect(frame).toHaveCount(1);
  const pills = section.getByTestId("create-step");
  await expect(pills).toHaveCount(3);
  const current = () =>
    pills.evaluateAll((all) => all.findIndex((pill) => pill.dataset.current === "true"));
  const boxes = new Set([await frameBox(frame)]);

  expect(await current()).toBe(0);

  for (const step of [1, 2]) {
    await expect
      .poll(
        async () => {
          await page.clock.runFor(3_000);
          boxes.add(await frameBox(frame));

          return current();
        },
        { timeout: 150_000 },
      )
      .toBe(step);
  }

  expect([...boxes]).toHaveLength(1);
});

test("on a phone the steps show as three cards in place of the frame", { tag: "@phone-only" }, async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.goto("/");
  const section = page.locator("#how");
  await section.scrollIntoViewIfNeeded();

  await expect(section.getByTestId("demo-panel")).toBeHidden();
  await expect(section.getByTestId("phone-steps").getByTestId("icon-card")).toHaveCount(3);
  // Each as wide as the screen.
  const widths = await section
    .getByTestId("icon-card")
    .evaluateAll((cards) => cards.map((card) => Math.round(card.getBoundingClientRect().width)));
  expect(new Set(widths)).toEqual(new Set([page.viewportSize()!.width]));
});

test("on a 375 px phone the notes are one a row, and nothing scrolls sideways", { tag: "@phone-only" }, async ({
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
