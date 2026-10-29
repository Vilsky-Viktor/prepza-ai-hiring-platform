import { expect, test } from "../fixtures"
import { api, createCompany, createInterview, inviteCandidate } from "../helpers/api"
import { inviteToken, saveLightColors } from "../helpers/db"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { setScheme } from "../helpers/theme"
import { ownerEmail, throwawayEmail } from "../helpers/users"

// What the brand tab saves, as the company's API returns it.
type Saved = {
  // None until colors are saved.
  brand_colors: { light: { background: string } | null; dark: unknown } | null
  brand_style: { heading_font: string; text_font: string; radius: number; button_radius: number }
}

// An owner picks the company's colors on its brand pages (general: the fonts and rounding; then
// each theme's colors), sees them in the preview, can't save unreadable ones, and its
// candidate's invitation shows them.
test("an owner sets the company's colors and its candidates see them", async ({ signInAs }) => {
  // Brand's three pages, then the candidate's invitation, on the local dev server.
  test.setTimeout(300_000)
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)

  const saved = () => api<Saved>(owner, "GET", `/companies/companies/${company.id}`)
  const prepzaStyle = (
    await api<{ style: Saved["brand_style"] }>(owner, "GET", "/companies/brand/prepza")
  ).style
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
  const brand = `/companies/${company.id}/brand`
  // Brand's pages in the side menu: general (brand's own address), then each theme's colors.
  const menu = owner.getByRole("main").getByRole("navigation")
  const subPage = (path: string) => menu.locator(`a[href="${brand}${path}"]:visible`).last()
  const open = (path: string) =>
    expect(menu.locator('a[aria-current="page"]:visible')).toHaveAttribute("href", `${brand}${path}`)

  await owner.setViewportSize({ width: 1280, height: 1300 })
  // General first: the logo, the fonts and the rounding, no colors.
  await visit(owner, brand)
  await open("")
  await expect(style).toBeVisible()
  await expect(owner.getByTestId("brand-page")).toHaveCount(0)
  await subPage("?page=light").click()
  await expect(owner).toHaveURL(new RegExp(`${brand}\\?page=light$`))
  await open("?page=light")
  await expect(field("page", 0)).toBeVisible()
  await expect(style).toHaveCount(0)
  await shot(owner, "prepza-colors")

  // The preview follows the colors as they're typed; edits are kept while moving between brand's
  // pages, until saved or the page is left.
  await fillDark()
  await subPage("").click()
  await expect(style).toBeVisible()
  await subPage("?page=light").click()
  await expect(field("page", 0)).toHaveValue("#101418")

  // Text too close to its background is refused, saying which, and nothing is saved.
  await field("page", 1).fill("#202428")
  await save.click()
  await expect(owner.getByText("The page's text is too hard to read on its background.").filter({ visible: true })).toBeVisible()
  expect((await saved()).brand_colors?.light ?? null).toBeNull()
  await shot(owner, "unreadable")
  await field("page", 1).fill("#f4f1ea")
  await save.click()
  await expect
    .poll(async () => {
      const current = await saved()

      return [current.brand_colors?.light?.background, current.brand_style]
    })
    // The fonts and rounding, untouched on general, stay prepza's.
    .toEqual(["#101418", prepzaStyle])

  // The titles' and the text's fonts and the cards' and buttons' rounding on general, the same in
  // both themes; the preview sets its title and its text in them.
  await subPage("").click()
  await style.getByRole("button").first().click()
  await expect(owner.getByRole("menuitemradio", { name: "Lora" })).toBeVisible()
  await shot(owner, "fonts")
  await owner.getByRole("menuitemradio", { name: "Lora" }).click()
  await style.getByRole("button").nth(1).click()
  await owner.getByRole("menuitemradio", { name: "Inter" }).click()
  const preview = owner.getByTestId("brand-preview")
  await expect(preview.locator("h3")).toHaveCSS("font-family", /Lora/)
  await expect(preview.locator("p").last()).toHaveCSS("font-family", /Inter/)
  await style.getByRole("spinbutton").first().fill("4")
  await style.getByRole("spinbutton").last().fill("8")
  await shot(owner, "picked")
  await owner.setViewportSize({ width: 390, height: 900 })
  await shot(owner, "picked-phone")
  await owner.setViewportSize({ width: 1280, height: 1300 })
  await save.click()
  await expect
    .poll(async () => (await saved()).brand_style)
    .toEqual({ heading_font: "lora", text_font: "inter", radius: 4, button_radius: 8 })
  // Saved colors of its own: the way back to prepza's shows, reset waits for a change.
  await expect(resetToPrepza).toBeVisible()
  await expect(reset).toBeDisabled()
  await owner.setViewportSize({ width: 390, height: 900 })
  await shot(owner, "saved-phone")
  await owner.setViewportSize({ width: 1280, height: 1300 })

  // Back to prepza's defaults and saved again: colors, fonts and rounding.
  await resetToPrepza.click()
  await expect
    .poll(async () => {
      const colors = (await saved()).brand_colors

      return [colors?.light ?? null, colors?.dark ?? null]
    })
    .toEqual([null, null])
  await expect(resetToPrepza).toHaveCount(0)
  await subPage("?page=light").click()
  await fillDark()
  await save.click()
  await expect(resetToPrepza).toBeVisible()

  // The dark set is its own page, prepza's until changed.
  await subPage("?page=dark").click()
  await expect(owner).toHaveURL(new RegExp(`${brand}\\?page=dark$`))
  await open("?page=dark")
  await expect(field("page", 0)).toHaveValue("#0a0a0a")
  await shot(owner, "dark")

  // The candidate's invitation, in the company's colors.
  const email = throwawayEmail("branded")
  await inviteCandidate(owner, interviewId, email)
  const candidate = await signInAs(email)
  // The candidate's own theme is light: the company's light set.
  await setScheme(candidate, "light")
  await visit(candidate, `/invite/${await inviteToken(email)}`)
  await expect(candidate.getByRole("main").getByRole("button")).toBeVisible()
  await expect(candidate.locator("html")).toHaveCSS("--background", "#101418")
  await shot(candidate, "invitation")
  // prepza's rounding (the font and rounding were reset to it), drawn at exactly its px: buttons,
  // and cards (rounded-xl), from which the page's other corners scale.
  await expect(candidate.getByRole("main").getByRole("button").first()).toHaveCSS(
    "border-top-left-radius",
    `${prepzaStyle.button_radius}px`
  )
  const cardCorner = await candidate.evaluate(() => {
    const card = document.createElement("div")
    card.className = "rounded-xl"
    document.querySelector("main")!.append(card)
    const corner = getComputedStyle(card).borderTopLeftRadius
    card.remove()

    return corner
  })
  expect(cardCorner).toBe(`${prepzaStyle.radius}px`)

  // Asked for the dark theme in the address: prepza's dark set, as the company has none.
  await visit(candidate, `/invite/${await inviteToken(email)}?theme=dark`)
  await expect(candidate.locator("html")).toHaveCSS("--background", "#0a0a0a")
})

// Colors saved before a check that now refuses them (the page's text on the gray card behind
// the questions): the light page shows them as saved, with why, to adjust.
test("saved colors a check now refuses stay in the brand settings with why", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const prepza = await api<{ colors: { light: Record<string, string> } }>(
    owner,
    "GET",
    "/companies/brand/prepza"
  )
  const colors = { ...prepza.colors.light, foreground: "#1a1a1a", muted: "#767676", muted_foreground: "#000000" }
  await saveLightColors(company.id, colors)
  const problem = owner.getByTestId("brand-problem")

  await owner.setViewportSize({ width: 1280, height: 1300 })
  await visit(owner, `/companies/${company.id}/brand?page=light`)
  await expect(problem).toContainText(
    "The page's text is too hard to read on the secondary fill behind the questions."
  )
  // The saved secondary fill, not prepza's.
  await expect(
    owner.getByTestId("brand-secondary").locator("input:not([type=color])").first()
  ).toHaveValue("#767676")
  await shot(owner, "refused-saved")

  // Darker text that reads on the fill too: saved, and the notice goes.
  await owner.getByTestId("brand-page").locator("input:not([type=color])").nth(1).fill("#000000")
  await owner.getByTestId("brand-save").first().click()
  await expect(problem).toHaveCount(0)
})
