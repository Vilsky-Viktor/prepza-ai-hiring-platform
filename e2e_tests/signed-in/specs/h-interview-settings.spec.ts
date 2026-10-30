import { expect, test } from "../fixtures"
import { createCompany, createInterview } from "../helpers/api"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { throwawayEmail } from "../helpers/users"

// The voice mode icon's name: an icon-only mark, so its name is what it says.
const VOICE_MODE = "Voice mode: questions are read aloud and answered by voice"

// An interview's settings are its own tab: click or voice mode, time per question, passing grade,
// hired and keeping its questions out of the shared question bank, each saved as it changes and
// kept after a reload. The mode shows as an icon after the interview's title, here and in the
// interviews list, named for screen readers.
test("an owner changes an interview's settings on its settings tab", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("interview-settings"))
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const interviewUrl = `/companies/${company.id}/interviews/${interviewId}`

  await visit(owner, interviewUrl)
  await owner.locator('main nav a[href$="?tab=settings"]:visible').click()
  await expect(owner).toHaveURL(new RegExp(`${interviewUrl}\\?tab=settings$`))
  await shot(owner, "settings-tab")

  // Click mode by default; voice mode chosen on the mode's switch, its first row.
  const modes = owner.getByRole("main").getByRole("group").first().getByRole("button")
  const mode = owner.getByRole("main").getByTestId("answer-mode").filter({ visible: true })
  await expect(modes.first()).toHaveAttribute("aria-pressed", "true")
  await expect(mode).toHaveAttribute("data-mode", "click")
  await modes.nth(1).click()
  await expect(modes.nth(1)).toHaveAttribute("aria-pressed", "true")
  await expect(modes.first()).toHaveAttribute("aria-pressed", "false")

  // The time per question, then the passing grade.
  const seconds = owner.getByRole("main").getByRole("spinbutton").first()
  const mark = owner.getByRole("main").getByRole("spinbutton").nth(1)
  await seconds.fill("90")
  await seconds.press("Enter")
  await mark.fill("70")
  await mark.press("Enter")
  // Hired, then keeping the questions out of the shared question bank: shared by default.
  const hired = owner.getByRole("main").getByRole("checkbox").first()
  const keepPrivate = owner.getByRole("main").getByRole("checkbox").nth(1)
  await expect(keepPrivate).not.toBeChecked()
  await hired.click()
  await expect(hired).toBeChecked()
  await keepPrivate.click()
  await expect(keepPrivate).toBeChecked()

  await owner.reload()
  await expect(modes.nth(1)).toHaveAttribute("aria-pressed", "true")
  await expect(mode).toHaveAttribute("data-mode", "voice")
  await expect(mode).toHaveAccessibleName(VOICE_MODE)
  await expect(seconds).toHaveValue("90")
  await expect(mark).toHaveValue("70")
  await expect(hired).toBeChecked()
  await expect(keepPrivate).toBeChecked()

  // Unchecked again, the questions may join the bank again.
  await keepPrivate.click()
  await expect(keepPrivate).not.toBeChecked()
  await owner.reload()
  await expect(keepPrivate).not.toBeChecked()
  await expect(hired).toBeChecked()

  // The interviews list names its mode too.
  await visit(owner, `/companies/${company.id}/interviews`)
  const listed = owner
    .locator(`main a[href$="/interviews/${interviewId}"]`)
    .getByTestId("answer-mode")
    .filter({ visible: true })
  await expect(listed).toHaveAttribute("data-mode", "voice")
  await expect(listed).toHaveAccessibleName(VOICE_MODE)
})

// The shareable link is on the settings tab, not the candidates tab: turned on there, it gives
// the link to copy.
test("an owner turns on the shareable link on the settings tab", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("share-link-settings"))
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const interviewUrl = `/companies/${company.id}/interviews/${interviewId}`

  await visit(owner, `${interviewUrl}?tab=candidates`)
  // Loaded: the candidates' search is there.
  await expect(owner.locator('main form input[name="tab"][value="candidates"]')).toHaveCount(1)
  await expect(owner.getByRole("main").getByRole("switch")).toHaveCount(0)

  await visit(owner, `${interviewUrl}?tab=settings`)
  const share = owner.getByRole("main").getByRole("switch")
  await expect(share).toHaveCount(1)
  await share.click()
  await expect(share).toBeChecked()
  await expect(owner.getByRole("main").locator('input[readonly]')).toHaveValue(/\/apply\/\S+$/)
})
