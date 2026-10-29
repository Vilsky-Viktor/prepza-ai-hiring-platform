import { expect, test } from "../fixtures"
import { api, createCompany, createInterview, inviteCandidate } from "../helpers/api"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, throwawayEmail } from "../helpers/users"

const OUTSIDE_COMPANY =
  "Only an owner or admin can email a report outside the company. Send it to one of your company's members."
// What the service says once the address may get the report: nobody finished yet.
const NO_FINISHED_CANDIDATES =
  "A report can be emailed once a candidate has finished this interview."

// A viewer shares a report only inside the company: an outside address is refused with the
// reason, a member's address goes on to the next check.
test("a viewer emails reports only to the company's members", async ({ signInAs }) => {
  const ownerAddress = ownerEmail()
  const owner = await signInAs(ownerAddress)
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  await inviteCandidate(owner, interviewId, throwawayEmail("candidate"))
  const viewerAddress = ownerEmail()
  const invited = await api<{ token: string }>(
    owner,
    "POST",
    `/companies/members?company_id=${company.id}`,
    { email: viewerAddress, role: "viewer" }
  )
  const viewer = await signInAs(viewerAddress)
  await api(viewer, "POST", `/companies/members/invites/${invited.token}/accept`)

  await visit(viewer, `/companies/${company.id}/interviews/${interviewId}?tab=candidates`)

  async function share(email: string) {
    await viewer.getByRole("button", { name: "Share report" }).click()
    const dialog = viewer.getByRole("dialog")
    await dialog.locator('input[type="email"]').fill(email)
    await dialog.locator('input[type="email"]').press("Enter")
  }

  await share(throwawayEmail("outside"))
  await expect(viewer.getByText(OUTSIDE_COMPANY).filter({ visible: true })).toBeVisible()
  await shot(viewer, "outside-refused")

  await viewer.keyboard.press("Escape")
  await share(ownerAddress)
  await expect(viewer.getByText(NO_FINISHED_CANDIDATES).filter({ visible: true })).toBeVisible()
})
