import { expect, test } from "../fixtures"
import { createCompany, createInterview } from "../helpers/api"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { throwawayEmail } from "../helpers/users"

// An interview's settings are its own tab: time per question, passing grade, hired and keeping
// its questions out of the shared question bank, each saved as it changes and kept after a reload.
test("an owner changes an interview's settings on its settings tab", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("interview-settings"))
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const interviewUrl = `/companies/${company.id}/interviews/${interviewId}`

  await visit(owner, interviewUrl)
  await owner.locator('main nav a[href$="?tab=settings"]:visible').click()
  await expect(owner).toHaveURL(new RegExp(`${interviewUrl}\\?tab=settings$`))
  await shot(owner, "settings-tab")

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
