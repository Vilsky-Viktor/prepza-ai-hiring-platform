import type { Locator, Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, createInterview } from "../helpers/api"
import { PHONE } from "../helpers/layout"
import { openDialog, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, randomId } from "../helpers/users"

// A logo of `width` × `height` drawn in the browser, uploaded to the company.
async function uploadLogo(page: Page, companyId: string, width: number, height: number) {
  const image = await page.evaluate(
    ([w, h]) => {
      const canvas = document.createElement("canvas")
      canvas.width = w
      canvas.height = h
      const context = canvas.getContext("2d")!
      context.fillStyle = "#0f172a"
      context.fillRect(0, 0, w, h)

      return canvas.toDataURL("image/png").split(",")[1]
    },
    [width, height]
  )
  await api(page, "PUT", `/companies/companies/${companyId}/logo`, { image })
}

// The companies page shows a square card per company, three to a row on a laptop: each card opens
// its company, its names level across the row whatever the logo, its count of interviews at the
// end of the name row, a logo covers its whole area, and Remove shows on hover or keyboard focus
// (always on touch screens) and asks to confirm without opening the company.
test("companies are cards that open their company", async ({ browser, signInAs }) => {
  const owner = await signInAs(ownerEmail())
  // A wide logo, a tall one, and none (the first letter); a long name (45 characters, the most) too.
  const companies = [
    await createCompany(owner),
    await createCompany(owner),
    await createCompany(owner, `E2E A long company name that runs on ${randomId()}`),
  ]
  await uploadLogo(owner, companies[0].id, 600, 200)
  await uploadLogo(owner, companies[1].id, 200, 600)
  await createInterview(owner, companies[0].id)
  await owner.setViewportSize({ width: 1440, height: 1000 })
  await visit(owner, "/companies")

  const cards = owner.getByRole("main").getByRole("listitem")
  await expect(cards).toHaveCount(3)
  const card = (index: number) =>
    cards.filter({ has: owner.locator(`a[href="/companies/${companies[index].id}/interviews"]`) })

  // One link per card, named by the company; one row of three, the names level.
  // Tops as laid out, in fractions of a pixel: the middle column can start between pixels.
  const tops: number[] = []
  const nameTops: number[] = []
  const top = async (locator: Locator) => (await locator.boundingBox())!.y

  for (const [index, company] of companies.entries()) {
    const link = card(index).getByRole("link")
    await expect(link).toHaveCount(1)
    await expect(link).toHaveAccessibleName(company.name)
    tops.push(await top(card(index)))
    nameTops.push(await top(link))
  }

  expect(Math.max(...tops) - Math.min(...tops)).toBeLessThan(1)
  expect(Math.max(...nameTops) - Math.min(...nameTops)).toBeLessThan(1)

  // A logo covers its area, wide or tall, from border to border (measured unhovered: hovered,
  // it zooms in).
  await owner.mouse.move(0, 0)
  for (const index of [0, 1]) {
    const area = card(index).getByTestId("company-logo")
    const image = area.locator("img")
    await expect(image).toHaveJSProperty("complete", true)
    await expect(image).toHaveCSS("object-fit", "cover")
    const areaBox = (await area.boundingBox())!
    const imageBox = (await image.boundingBox())!
    expect(Math.abs(imageBox.width - areaBox.width)).toBeLessThan(1)
    expect(Math.abs(imageBox.height - areaBox.height)).toBeLessThan(1)
    // From the card's left border (1 px) to its right one.
    expect(Math.abs(areaBox.x - (await card(index).boundingBox())!.x - 1)).toBeLessThan(1)
  }

  await expect(card(2).getByTestId("company-logo").locator("img")).toHaveCount(0)
  await shot(owner, "cards")

  for (const [index, count] of [1, 0, 0].entries()) {
    // Square, within a pixel's rounding.
    const cardBox = (await card(index).boundingBox())!
    expect(Math.abs(cardBox.width - cardBox.height)).toBeLessThan(1.5)

    // The count sits in the name row, after the name, below the logo.
    const link = card(index).getByRole("link")
    const stat = link.locator("xpath=..").getByText(String(count), { exact: true })
    await expect(stat).toBeVisible()
    const statBox = (await stat.boundingBox())!
    const linkBox = (await link.boundingBox())!
    const logoBox = (await card(index).getByTestId("company-logo").boundingBox())!
    expect(statBox.x).toBeGreaterThanOrEqual(linkBox.x + linkBox.width)
    expect(statBox.y).toBeGreaterThanOrEqual(logoBox.y + logoBox.height - 1)
  }

  // Remove, the card's one button, is hidden until the card is hovered or holds focus.
  const remove = card(0).getByRole("button")
  await expect(remove).toHaveCount(1)
  const removePill = remove.locator("xpath=..")
  await expect(removePill).toHaveCSS("opacity", "0")
  await card(0).hover()
  await expect(removePill).toHaveCSS("opacity", "1")
  await owner.mouse.move(0, 0)
  await expect(removePill).toHaveCSS("opacity", "0")
  await card(0).getByRole("link").focus()
  await owner.keyboard.press("Tab")
  await expect(remove).toBeFocused()
  await expect(removePill).toHaveCSS("opacity", "1")
  await remove.blur()
  await expect(removePill).toHaveCSS("opacity", "0")

  // Remove asks to confirm and stays on the page; Cancel keeps the card.
  await openDialog(owner, card(0).getByRole("button"))
  await expect(owner).toHaveURL(/\/companies$/)
  await owner.getByRole("dialog").getByRole("button").first().click()
  await expect(owner.getByRole("dialog")).toHaveCount(0)
  await expect(cards).toHaveCount(3)

  // A touch screen, which can't hover, always shows Remove: the owner's session on a phone.
  const storageState = await owner.context().storageState({ indexedDB: true })
  const phone = await browser.newContext({ storageState, isMobile: true, hasTouch: true, viewport: PHONE })

  try {
    const touch = await phone.newPage()
    await visit(touch, "/companies")
    expect(await touch.evaluate(() => matchMedia("(hover: none)").matches)).toBe(true)
    const touchRemove = touch
      .getByRole("main")
      .getByRole("listitem")
      .filter({ has: touch.locator(`a[href="/companies/${companies[0].id}/interviews"]`) })
      .getByRole("button")
    await expect(touchRemove.locator("xpath=..")).toHaveCSS("opacity", "1")
  } finally {
    await phone.close()
  }

  // Anywhere on the card, the logo too, opens the company.
  await card(1).click({ position: { x: 60, y: 120 } })
  await expect(owner).toHaveURL(new RegExp(`/companies/${companies[1].id}/interviews$`))
})
