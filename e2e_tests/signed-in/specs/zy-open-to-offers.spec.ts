import { expect, test } from "../fixtures"
import { api, createCompany, createInterview } from "../helpers/api"
import { deleteTemplate } from "../helpers/db-library"
import {
  addPracticeResult,
  deletePracticeResults,
  discovered,
  markPaid,
  matchingTemplate,
  unmarkPaid,
} from "../helpers/discover"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { uidOf } from "../helpers/sign-in"
import { ownerEmail, randomId, throwawayEmail } from "../helpers/users"

type OpenToOffers = { on: boolean; linkedin_url: string | null }

// A talent who just finished a practice round turns on Open to offers from the card above its
// results: the switch waits for a LinkedIn profile, and saving the profile turns it on, so a
// paying company hiring for the subject lists them on its interview's Discover tab. In Settings
// the same card shows it on; turning it off there takes them off the list at once.
test("a talent turns Open to offers on after a practice round and off in Settings", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  await markPaid(company.id)
  const interviewId = await createInterview(owner, company.id)
  const { templateId, topicId } = await matchingTemplate(owner, interviewId)
  const talent = await signInAs(throwawayEmail("offers"), undefined, `E2E Talent ${randomId()}`)
  const talentId = await uidOf(talent)
  const profile = `https://www.linkedin.com/in/e2e-${randomId()}`

  try {
    const roundId = await addPracticeResult(talentId, templateId, topicId, 80)
    await visit(talent, `/practice/rounds/${roundId}`)
    const card = talent.getByTestId("open-to-offers").filter({ visible: true })
    const toggle = card.getByRole("switch")

    // Off, and it can't be turned on without a profile.
    await expect(toggle).toHaveAttribute("aria-checked", "false")
    await expect(toggle).toBeDisabled()
    await card.getByRole("textbox").fill(profile)
    await shot(talent, "open-to-offers-off")
    // Save turns it on while it's off.
    await card.getByRole("button").click()
    await expect(toggle).toHaveAttribute("aria-checked", "true")
    await expect(card.getByRole("button")).toBeDisabled()
    await shot(talent, "open-to-offers-on")
    expect(await api<OpenToOffers>(talent, "GET", "/rounds/open-to-offers")).toMatchObject({
      on: true,
      linkedin_url: profile,
    })
    expect(await discovered(owner, interviewId)).toContain(talentId)

    // In Settings it shows on with the profile; turning it off takes them off the list.
    await visit(talent, "/settings")
    const settings = talent.getByTestId("open-to-offers").filter({ visible: true })
    await expect(settings.getByRole("switch")).toHaveAttribute("aria-checked", "true")
    await expect(settings.getByRole("textbox")).toHaveValue(profile)
    await settings.getByRole("switch").click()
    await expect(settings.getByRole("switch")).toHaveAttribute("aria-checked", "false")
    expect((await api<OpenToOffers>(talent, "GET", "/rounds/open-to-offers")).on).toBe(false)
    expect(await discovered(owner, interviewId)).not.toContain(talentId)
  } finally {
    await api(talent, "DELETE", "/rounds/open-to-offers")
    await deletePracticeResults(talentId, templateId)
    await deleteTemplate(templateId)
    await unmarkPaid(company.id)
  }
})
