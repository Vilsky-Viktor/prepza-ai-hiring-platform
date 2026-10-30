import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, createInterview, templatesBySize } from "../helpers/api"
import { PHONE } from "../helpers/layout"
import { openDialog, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, throwawayEmail } from "../helpers/users"

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

// The companies page lists a row per company: its logo whole in a tile the row's full height
// from its start border (its first letter without one; no logo on phones), its name with the
// owner's icon or the member's role, its counts of interviews and of its team, and Remove for
// the owner, which asks to confirm without opening the company. The whole row opens it.
test("companies are rows that open their company", async ({ signInAs }) => {
  const ownerAddress = ownerEmail()
  const owner = await signInAs(ownerAddress)
  // A wide logo with an interview and a pending invite, and a company without a logo.
  const withLogo = await createCompany(owner)
  const noLogo = await createCompany(owner)
  await uploadLogo(owner, withLogo.id, 600, 200)
  await createInterview(owner, withLogo.id)
  await api(owner, "POST", `/companies/members?company_id=${withLogo.id}`, {
    email: throwawayEmail("pending"),
    role: "viewer",
  })
  // A company the owner joined as a viewer.
  const other = await signInAs(ownerEmail())
  const joined = await createCompany(other)
  const invited = await api<{ token: string }>(
    other,
    "POST",
    `/companies/members?company_id=${joined.id}`,
    { email: ownerAddress, role: "viewer" }
  )
  await api(owner, "POST", `/companies/members/invites/${invited.token}/accept`)

  await owner.setViewportSize({ width: 1440, height: 1000 })
  await visit(owner, "/companies")

  const rows = owner.getByRole("main").getByRole("listitem")
  await expect(rows).toHaveCount(3)
  const row = (companyId: string) =>
    rows.filter({ has: owner.locator(`a[href="/companies/${companyId}/interviews"]`) })

  for (const company of [withLogo, noLogo, joined]) {
    await expect(row(company.id).getByRole("link")).toHaveCount(1)
    await expect(row(company.id).getByRole("link")).toContainText(company.name)
  }

  // The logo whole (contained, never cropped) in a tile from the row's start border, top to
  // bottom.
  const tile = row(withLogo.id).getByTestId("company-logo")
  const image = tile.locator("img")
  await expect(image).toHaveJSProperty("complete", true)
  await expect(image).toHaveCSS("object-fit", "contain")
  const rowBox = (await row(withLogo.id).boundingBox())!
  const tileBox = (await tile.boundingBox())!
  expect(Math.abs(tileBox.x - rowBox.x)).toBeLessThan(1)
  // Between the row's borders, if it has them (the list's dividers: a bottom one on every row
  // but the last, and the companies' order is their random names').
  const borders = await row(withLogo.id).evaluate((element) => {
    const style = getComputedStyle(element)

    return { top: parseFloat(style.borderTopWidth), bottom: parseFloat(style.borderBottomWidth) }
  })
  expect(Math.abs(tileBox.y - (rowBox.y + borders.top))).toBeLessThan(1)
  const rowBottom = rowBox.y + rowBox.height - borders.bottom
  expect(Math.abs(tileBox.y + tileBox.height - rowBottom)).toBeLessThan(1)
  expect(Math.abs(tileBox.width - tileBox.height)).toBeLessThan(1)
  // Without a logo, the first letter.
  const letterTile = row(noLogo.id).getByTestId("company-logo")
  await expect(letterTile.locator("img")).toHaveCount(0)
  await expect(letterTile).toHaveText(noLogo.name[0])

  // The counts: interviews, and the team with its pending invites.
  for (const [company, interviews, members] of [
    [withLogo, "1", "2"],
    [noLogo, "0", "1"],
    [joined, "0", "2"],
  ] as const) {
    await expect(row(company.id).getByTestId("interview-count")).toHaveText(interviews)
    await expect(row(company.id).getByTestId("member-count")).toHaveText(members)
  }

  // The owner's icon on the companies they own; a member's role, with nothing to remove.
  await expect(row(withLogo.id).getByRole("img")).toHaveCount(1)
  await expect(row(joined.id).getByRole("img")).toHaveCount(0)
  await expect(row(joined.id)).toContainText("viewer")
  await expect(row(joined.id).getByRole("button")).toHaveCount(0)
  await shot(owner, "rows")

  // Remove, always shown, asks to confirm and stays on the page; Cancel keeps the row.
  const remove = row(withLogo.id).getByRole("button")
  await expect(remove).toHaveCount(1)
  await expect(remove).toBeVisible()
  await openDialog(owner, remove)
  await expect(owner).toHaveURL(/\/companies$/)
  await owner.getByRole("dialog").getByRole("button").first().click()
  await expect(owner.getByRole("dialog")).toHaveCount(0)
  await expect(rows).toHaveCount(3)

  // On a phone: no logo, the name at the row's padding, the counts under it, Remove on screen.
  await owner.setViewportSize(PHONE)
  await visit(owner, "/companies")
  await expect(tile).toBeHidden()
  const phoneRow = (await row(withLogo.id).boundingBox())!
  const nameBox = (await row(withLogo.id).getByRole("link").getByText(withLogo.name).boundingBox())!
  const countBox = (await row(withLogo.id).getByTestId("interview-count").boundingBox())!
  expect(Math.abs(nameBox.x - phoneRow.x - 24)).toBeLessThan(1)
  expect(countBox.y).toBeGreaterThanOrEqual(nameBox.y + nameBox.height - 1)
  await expect(remove).toBeInViewport({ ratio: 1 })
  await shot(owner, "rows-phone")

  // Choosing a company for a template: the same rows, each opening the template, without Remove.
  await owner.setViewportSize({ width: 1440, height: 1000 })
  const [template] = await templatesBySize(owner)
  await visit(owner, `/companies/templates/${template.id}`)
  const pick = owner.getByRole("main").getByRole("listitem")
  await expect(pick).toHaveCount(3)
  await expect(
    pick.locator(`a[href="/companies/${withLogo.id}/templates/${template.id}"]`)
  ).toHaveCount(1)
  await expect(pick.getByTestId("member-count")).toHaveCount(3)
  await expect(pick.getByRole("button")).toHaveCount(0)

  // Anywhere on the row, the logo too, opens the company.
  await visit(owner, "/companies")
  await row(noLogo.id).getByTestId("company-logo").click()
  await expect(owner).toHaveURL(new RegExp(`/companies/${noLogo.id}/interviews$`))
})
