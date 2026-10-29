import { expect, type Page, test } from "@playwright/test";

import { shot } from "./helpers/screenshots";
import { settled } from "./helpers/waits";

// On a phone, a page with pages of its own (the developer docs' MCP tab) names the open one in a
// bar under the tabs, across the whole window; the bar opens the site's menu of them all, each a
// link, the open one marked.

const OPEN = "/api-docs?tab=mcp&page=frameworks";

/** The bar under the tabs: the button straight inside a navigation named by what it shows. */
function subPagesBar(page: Page) {
  return page.locator("main nav > button[aria-labelledby]");
}

/** The MCP tab's own pages, in the order the (wide screens') side menu lists them. */
async function mcpPages(page: Page) {
  const hrefs = await page
    .locator('main nav:has(a[href="/api-docs?tab=objects"]) a[href^="/api-docs?tab=mcp"]')
    .evaluateAll((links) => links.map((link) => link.getAttribute("href")));

  // The first is the MCP tab itself; its pages follow.
  return hrefs.slice(1);
}

/** Opens the bar's menu (retried: a tap before the page is ready does nothing). */
async function openSubPages(page: Page) {
  const menu = page.getByRole("menu");
  await expect(async () => {
    await subPagesBar(page).click();
    await expect(menu).toBeVisible({ timeout: 2_000 });
  }).toPass();
  await settled(menu);

  return menu;
}

test("the sub-pages bar spans the window, square, right under the tabs", { tag: "@phone-only" }, async ({ page }) => {
  await page.goto(OPEN);
  const bar = subPagesBar(page);
  await expect(bar).toBeVisible();
  const box = await bar.evaluate((element) => {
    const rect = element.getBoundingClientRect();
    const tabs = element.closest("nav")!.previousElementSibling!.getBoundingClientRect();

    return {
      left: Math.round(rect.left),
      width: Math.round(rect.width),
      gap: Math.round(rect.top - tabs.bottom),
      radius: getComputedStyle(element).borderTopLeftRadius,
      window: window.innerWidth,
      scroll: document.documentElement.scrollWidth,
    };
  });
  expect(box).toEqual({
    left: 0,
    width: box.window,
    gap: 0,
    radius: "0px",
    window: box.window,
    scroll: box.window,
  });
  await expect(page.locator("main select")).toHaveCount(0);
});

test("the sub-pages bar lists every page, marks the open one and opens another", { tag: "@phone-only" }, async ({ page }) => {
  await page.goto(OPEN);
  const pages = await mcpPages(page);
  expect(pages.length).toBeGreaterThan(1);
  expect(pages).toContain(OPEN);

  let menu = await openSubPages(page);
  const items = menu.getByRole("menuitem");
  const hrefs = await items.evaluateAll((links) => links.map((link) => link.getAttribute("href")));
  expect(hrefs).toEqual(pages);
  await expect(menu.locator('[aria-current="page"]')).toHaveCount(1);
  await expect(menu.locator('[aria-current="page"]')).toHaveAttribute("href", OPEN);
  await shot(page, "phone-sub-pages");

  // Another page from the menu opens at its address and is the marked one next time.
  const other = pages[1];
  await items.nth(1).click();
  await expect(page).toHaveURL(other);
  menu = await openSubPages(page);
  await expect(menu.locator('[aria-current="page"]')).toHaveAttribute("href", other);
});
