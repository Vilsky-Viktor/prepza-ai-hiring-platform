import { expect, test } from "../fixtures"
import { api, createCompany, createInterview, inviteCandidate } from "../helpers/api"
import { inviteToken } from "../helpers/db"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, throwawayEmail } from "../helpers/users"

// What the brand tab saves, as the company's API returns it.
type Saved = {
  // None until colors are saved.
  brand_colors: { light: { background: string } | null; dark: unknown } | null
  brand_style: { font: string; radius: number; button_radius: number }
}

// An owner picks the company's colors on its brand tab, sees them in the preview, can't save
// unreadable ones, and its candidate's invitation shows them.
test("an owner sets the company's colors and its candidates see them", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)

  const saved = () => api<Saved>(owner, "GET", `/companies/companies/${company.id}`)
  // A color's hex code: the `index`th in its group (page, primary, secondary, dialogs, borders).
  const field = (group: string, index: number) =>
    owner.getByTestId(`brand-${group}`).locator("input:not([type=color])").nth(index)

  // The colors of a dark page with an orange primary.
  async function fillDark() {
    await field("page", 0).fill("#101418")
    await field("page", 1).fill("#f4f1ea")
    await field("primary", 0).fill("#ff7a1a")
    await field("primary", 1).fill("#1a1007")
    await field("secondary", 0).fill("#1d242c")
    await field("secondary", 1).fill("#a9b4bf")
    await field("dialogs", 0).fill("#1d242c")
    await field("dialogs", 1).fill("#f4f1ea")
    await field("borders", 0).fill("#2c3640")
  }

  const save = owner.getByTestId("brand-save").first()
  const reset = owner.getByTestId("brand-reset").first()
  const resetToPrepza = owner.getByTestId("brand-reset-prepza").first()
  const style = owner.getByTestId("brand-style")

  await owner.setViewportSize({ width: 1280, height: 1300 })
  await visit(owner, `/companies/${company.id}/brand`)
  await expect(field("page", 0)).toBeVisible()
  await shot(owner, "prepza-colors")

  // The preview follows the colors as they're typed.
  await fillDark()
  // The font and the cards' and buttons' rounding, the same in both themes, saved with the colors.
  await style.getByRole("button").click()
  await expect(owner.getByRole("menuitemradio", { name: "Inter" })).toBeVisible()
  await shot(owner, "fonts")
  await owner.getByRole("menuitemradio", { name: "Inter" }).click()
  await style.getByRole("spinbutton").first().fill("4")
  await style.getByRole("spinbutton").last().fill("8")
  await shot(owner, "picked")
  await owner.setViewportSize({ width: 390, height: 900 })
  await shot(owner, "picked-phone")
  await owner.setViewportSize({ width: 1280, height: 1300 })

  // Text too close to its background is refused, saying which, and nothing is saved.
  await field("page", 1).fill("#202428")
  await save.click()
  await expect(owner.getByText("The page's text is too hard to read on its background.")).toBeVisible()
  expect((await saved()).brand_colors?.light ?? null).toBeNull()
  await shot(owner, "unreadable")
  await field("page", 1).fill("#f4f1ea")
  await save.click()
  await expect
    .poll(async () => {
      const current = await saved()

      return [current.brand_colors?.light?.background, current.brand_style]
    })
    .toEqual(["#101418", { font: "inter", radius: 4, button_radius: 8 }])
  // Saved colors of its own: the way back to prepza's shows, reset waits for a change.
  await expect(resetToPrepza).toBeVisible()
  await expect(reset).toBeDisabled()
  await owner.setViewportSize({ width: 390, height: 900 })
  await shot(owner, "saved-phone")
  await owner.setViewportSize({ width: 1280, height: 1300 })

  // Back to prepza's defaults and saved again: colors, font and rounding.
  await resetToPrepza.click()
  await expect
    .poll(async () => {
      const colors = (await saved()).brand_colors

      return [colors?.light ?? null, colors?.dark ?? null]
    })
    .toEqual([null, null])
  await expect(resetToPrepza).toHaveCount(0)
  await fillDark()
  await save.click()
  await expect(resetToPrepza).toBeVisible()

  // The dark set is its own, prepza's until changed.
  await owner.getByRole("main").getByRole("tab").last().click()
  await expect(field("page", 0)).toHaveValue("#0a0a0a")
  await shot(owner, "dark")

  // The candidate's invitation, in the company's colors.
  const email = throwawayEmail("branded")
  await inviteCandidate(owner, interviewId, email)
  const candidate = await signInAs(email)
  await visit(candidate, `/invite/${await inviteToken(email)}`)
  await expect(candidate.getByRole("main").getByRole("button")).toBeVisible()
  await expect(candidate.locator("html")).toHaveCSS("--background", "#101418")
  await shot(candidate, "invitation")

  // Asked for the dark theme in the address: prepza's dark set, as the company has none.
  await visit(candidate, `/invite/${await inviteToken(email)}?theme=dark`)
  await expect(candidate.locator("html")).toHaveCSS("--background", "#0a0a0a")
})
