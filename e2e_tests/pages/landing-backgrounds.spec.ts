import { expect, test } from "@playwright/test";

import { loaded } from "./helpers/waits";

// The home page's section backgrounds: grey bands, a dot grid and soft glows, each across the
// whole page and as tall as its section, without letting the page scroll sideways.

test("the sections' backgrounds run across the whole page, top to bottom", async ({ page }) => {
  test.setTimeout(120_000);
  await page.goto("/");
  await loaded(page);

  // The grey bands, the dot grid and the glows: each section's layer under its content, from the
  // page's left edge to its right one (a scrollbar's gutter aside), as tall as the section.
  for (const id of ["how", "invite", "reports", "agent", "compare", "help"]) {
    const section = page.locator(`#${id}`);
    await section.scrollIntoViewIfNeeded();
    const layer = await section.evaluate((element) => {
      const box = element.getBoundingClientRect();
      const before = getComputedStyle(element, "::before");
      const left = box.left + parseFloat(before.left);

      return {
        left,
        right: left + parseFloat(before.width),
        height: parseFloat(before.height),
        sectionHeight: box.height,
        pageLeft: document.body.getBoundingClientRect().left,
        pageRight: document.body.getBoundingClientRect().right,
      };
    });
    expect(layer.left, id).toBeCloseTo(layer.pageLeft, 0);
    expect(layer.right, id).toBeCloseTo(layer.pageRight, 0);
    expect(layer.height, id).toBeCloseTo(layer.sectionHeight, 0);
  }

  const widths = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  expect(widths.scrollWidth).toBeLessThanOrEqual(widths.clientWidth);
});
