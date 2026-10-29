import { expect, type Locator, type Page } from "@playwright/test"

/** Opens the dialog `button` opens, clicking again if the first click came before the page was
 * ready for it. */
export async function openDialog(page: Page, button: Locator) {
  await expect(async () => {
    await button.click()
    await expect(page.getByRole("dialog")).toBeVisible({ timeout: 2_000 })
  }).toPass()
}

/** Opens one of a page's tabs (a company's, the admin zone's) by where it leads (`path`, the
 * end of its address, such as "/billing" or "?tab=reserved"), clicking again if the first click
 * came before the page was ready for it. */
export async function openTab(page: Page, path: string) {
  // The visible one: the side menu on wide screens, the tabs on phones (the other is hidden); the
  // first, as a page's first sub-page shares its address and is listed under it.
  const tab = page
    .getByRole("main")
    .getByRole("navigation")
    .locator(`a[href$="${path}"]:visible`)
    .first()
  const href = await tab.getAttribute("href")

  await expect(async () => {
    await tab.click()
    // Long enough for a slow page on a busy run: a click again cancels the first.
    await expect(page).toHaveURL((url) => url.href.endsWith(href ?? path), { timeout: 15_000 })
  }).toPass()
}

/** Hovers `trigger` until `tooltip` shows: a hover that came before the page was interactive
 * (it hydrates after it shows) is lost, as the mouse doesn't move again. */
export async function hoverFor(page: Page, trigger: Locator, tooltip: Locator) {
  await expect(async () => {
    await page.mouse.move(0, 0)
    await trigger.hover()
    await expect(tooltip).toBeVisible({ timeout: 3_000 })
  }).toPass({ timeout: 90_000 })
}

/** Opens `path`. While the test site restarts the gateway answers 502, so it's tried again until
 * it's back. Other statuses count: maintenance mode is a 503. */
export async function visit(page: Page, path: string) {
  await expect(async () => {
    const response = await page.goto(path)
    expect(response?.status(), `${path} answers`).not.toBe(502)
  }).toPass({ timeout: 90_000, intervals: [2_000] })
}

/** An integration's row on a company's integrations tab, by the page it opens (`path`, such as
 * "/workable", "/slack", "/api" or "/ai"). */
export function integrationRow(page: Page, path: string) {
  return page
    .getByRole("listitem")
    .filter({ has: page.locator(`a[href$="/integrations${path}"]`) })
}
