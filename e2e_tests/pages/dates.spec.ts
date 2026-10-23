import { expect, test as base, type Locator } from "@playwright/test";

import { addNewsPost, deleteNewsPost } from "./helpers/db";
import { loaded } from "./helpers/waits";

// Every date on the site is in italics: shown in a <time> element that names its day.

const DAY = /^\d{4}-\d{2}-\d{2}/;

// A throwaway news post of the test's own, published today, deleted after it.
const test = base.extend<{ newsPost: string }>({
  newsPost: async ({}, use) => {
    const id = await addNewsPost();
    await use(id);
    await deleteNewsPost(id);
  },
});

/** Each of the dates in `area`: a <time> naming its day, in italics. */
async function expectItalicDates(area: Locator) {
  const dates = area.locator("time");

  await expect(dates.first()).toBeVisible();
  const shown = await dates.evaluateAll((items) =>
    items.map((item) => ({
      day: item.getAttribute("datetime") ?? "",
      style: getComputedStyle(item).fontStyle,
    })),
  );

  for (const date of shown) {
    expect(date.day).toMatch(DAY);
    expect(date.style).toBe("italic");
  }
}

test("a news post's day is in italics", async ({ page, newsPost }) => {
  await page.goto("/news");
  await loaded(page);
  await expectItalicDates(page.locator(`article[id="${newsPost}"]`));
});

test("the terms' days are in italics, in the sentence and the versions", async ({ page }) => {
  await page.goto("/terms");
  await loaded(page);
  await expectItalicDates(page.locator("main header"));
  // Only the day is in italics, not the sentence around it.
  await expect(page.locator("main header > p")).toHaveCSS("font-style", "normal");

  if ((await page.locator("main nav").count()) > 0) {
    await expectItalicDates(page.locator("main nav"));
  }
});
