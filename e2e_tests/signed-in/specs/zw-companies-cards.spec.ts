import type { Locator, Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany } from "../helpers/api"
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

// The companies page shows a card per company, three to a row on a laptop: each card opens its
// company, its names level across the row whatever the logo, a logo covers its whole area, and
// Remove asks to confirm without opening the company.
test("companies are cards that open their company", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  // A wide logo, a tall one, and none (the first letter); a long name (45 characters, the most) too.
  const companies = [
    await createCompany(owner),
    await createCompany(owner),
    await createCompany(owner, `E2E A long company name that runs on ${randomId()}`),
  ]
  await uploadLogo(owner, companies[0].id, 600, 200)
  await uploadLogo(owner, companies[1].id, 200, 600)
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

  // Remove, the card's one button, asks to confirm and stays on the page; Cancel keeps the card.
  await expect(card(0).getByRole("button")).toHaveCount(1)
  await openDialog(owner, card(0).getByRole("button"))
  await expect(owner).toHaveURL(/\/companies$/)
  await owner.getByRole("dialog").getByRole("button").first().click()
  await expect(owner.getByRole("dialog")).toHaveCount(0)
  await expect(cards).toHaveCount(3)

  // Anywhere on the card, the logo too, opens the company.
  await card(1).click({ position: { x: 60, y: 120 } })
  await expect(owner).toHaveURL(new RegExp(`/companies/${companies[1].id}/interviews$`))
})
