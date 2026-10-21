import { expect, test } from "@playwright/test";

import { loaded, scrollAtRest } from "./helpers/waits";

// The home page's "how it works" link scrolls smoothly to its section, not in one jump.

test("how it works scrolls smoothly", async ({ page }, info) => {
  test.skip(info.project.name === "phone")
  await page.goto("/")
  await loaded(page)
  expect(await page.evaluate(() => getComputedStyle(document.documentElement).scrollBehavior)).toBe("smooth")
  // Every place the page scrolls through on its way.
  await page.evaluate(() => {
    const passed: number[] = []
    Object.assign(window, { passed })
    window.addEventListener("scroll", () => passed.push(window.scrollY))
  })
  await page.locator('main a[href="#how"]').click()
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(0)
  await scrollAtRest(page)
  const passed = await page.evaluate(() => (window as unknown as { passed: number[] }).passed)
  const end = passed[passed.length - 1]
  // A jump lands at once; a smooth scroll passes places between the top and the section.
  expect(passed.some((place) => place > 0 && place < end)).toBe(true)
})

// On a long page, "back to top" shows once it's scrolled down, and goes back to the top.
test("back to top shows on a long page and returns to its top", async ({ page }) => {
  await page.goto("/")
  await loaded(page)
  const button = page.getByTestId("back-to-top")
  await expect(button).toHaveCount(0)
  await page.mouse.wheel(0, 2500)
  await expect(button).toBeVisible()
  // An icon alone: its label is what screen readers read.
  await expect(button).toHaveAccessibleName(/.+/)
  await button.click()
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0)
  await expect(button).toHaveCount(0)
})
