import type { Locator, Page } from "@playwright/test";

import { expect, test } from "./helpers/templates";

// A search over a list (SearchedList, shared by every list with a search on top) and the list, or
// its empty state, read as one block: no gap, the same width, square corners where they meet, and
// one border round both, with a single line at the seam. Checked on the practice page's templates,
// on a computer and a phone (the two projects).

/** The block's search field and what continues under it, with the styles that join them. */
async function block(page: Page) {
  const searched = page.locator('[data-slot="searched-list"]');
  const field = searched.locator("form > div").first();
  const under = searched.locator(":scope > :last-child");
  await expect(field).toBeVisible();
  await expect(under).toBeVisible();
  const style = (locator: Locator) =>
    locator.evaluate((element) => {
      const css = getComputedStyle(element);

      return {
        top: css.borderTopWidth,
        bottom: css.borderBottomWidth,
        topColor: css.borderTopColor,
        bottomColor: css.borderBottomColor,
        topStart: css.borderTopLeftRadius,
        bottomStart: css.borderBottomLeftRadius,
      };
    });

  return {
    field: { box: (await field.boundingBox())!, css: await style(field) },
    under: { box: (await under.boundingBox())!, css: await style(under) },
  };
}

async function expectOneBlock(page: Page) {
  const { field, under } = await block(page);

  expect(Math.abs(field.box.y + field.box.height - under.box.y)).toBeLessThan(1);
  expect(Math.abs(field.box.x - under.box.x)).toBeLessThan(1);
  expect(Math.abs(field.box.width - under.box.width)).toBeLessThan(1);
  expect(field.css.bottomStart).toBe("0px");
  expect(under.css.topStart).toBe("0px");
  // One line at the seam: the field's bottom border, none on top of what follows.
  expect(field.css.bottom).toBe("1px");
  expect(under.css.top).toBe("0px");
  // The field's outline is the list's.
  expect(field.css.top).toBe("1px");
  expect(field.css.topColor).toBe(under.css.bottomColor);
}

test("a search and its results read as one block", async ({ page, addTemplate }) => {
  const template = await addTemplate();
  await page.goto(`/practice?q=${encodeURIComponent(template.title)}`);
  await expect(page.locator(`a[href*="${template.slug}"]`).first()).toBeVisible();

  await expectOneBlock(page);
});

test("a search with no results reads as one block with its empty state", async ({ page }) => {
  await page.goto(`/practice?q=no-match-${Date.now()}`);
  await expect(page.locator('[data-slot="searched-list"] form + p')).toBeVisible();

  await expectOneBlock(page);
});
