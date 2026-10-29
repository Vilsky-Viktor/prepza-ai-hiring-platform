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

test("nothing on the home page reaches past the page's edges, so it never scrolls sideways", { tag: "@phone" }, async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.goto("/");
  await loaded(page);

  for (const width of [390, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    // The hero's wires run out to the page's edges, never over a scrollbar's gutter; once the
    // pictures have redrawn for the new width.
    await expect
      .poll(
        () =>
          page.locator("main svg").evaluateAll((all) => {
            const body = document.body.getBoundingClientRect();

            return all
              .filter((svg) => {
                const box = svg.getBoundingClientRect();

                return box.width > 0 && (box.left < body.left - 1 || box.right > body.right + 1);
              })
              .map((svg) => svg.outerHTML.slice(0, 80));
          }),
        { message: String(width) },
      )
      .toEqual([]);
    await expect
      .poll(
        () =>
          page.evaluate(() => {
            window.scrollTo(300, 0);

            return window.scrollX;
          }),
        { message: String(width) },
      )
      .toBe(0);
  }
});
