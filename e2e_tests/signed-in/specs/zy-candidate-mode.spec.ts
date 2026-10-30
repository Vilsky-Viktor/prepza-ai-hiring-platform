import { expect, test } from "../fixtures"
import { api, createCompany, createInterview, finishOneAnswer } from "../helpers/api"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, throwawayEmail } from "../helpers/users"

type Candidate = { id: string; email: string; voice: boolean }

// A company chooses how one candidate takes the interview, apart from its mode: invited with
// voice mode (here through the API; the invite dialog follows the interview's mode), it's kept for
// that candidate. The candidate list marks only the candidates whose mode differs.
// On the candidate's page the same switch changes it until they start, then disappears.
test("a candidate takes the interview in their own mode, set until they start", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const voiceEmail = throwawayEmail("voice-mode")
  const clickEmail = throwawayEmail("click-mode")
  await api(owner, "POST", `/companies/interviews/${interviewId}/candidates`, {
    email: clickEmail,
  })
  const interviewPath = `/companies/${company.id}/interviews/${interviewId}`

  await api(owner, "POST", `/companies/interviews/${interviewId}/candidates`, {
    email: voiceEmail,
    voice: true,
  })
  await visit(owner, `${interviewPath}?tab=candidates`)

  const candidates = await api<Candidate[]>(
    owner,
    "GET",
    `/companies/interviews/${interviewId}/candidates?sort=date`
  )
  const voiced = candidates.find((candidate) => candidate.email === voiceEmail)!
  const clicked = candidates.find((candidate) => candidate.email === clickEmail)!
  expect([voiced.voice, clicked.voice]).toEqual([true, false])

  // Only the candidate in another mode than the interview's shows a mode icon: voice.
  const row = (id: string) =>
    owner.getByRole("main").locator(`a[href$="/candidates/${id}"]`).filter({ visible: true })
  await expect(row(voiced.id).getByTestId("answer-mode")).toHaveAttribute("data-mode", "voice")
  await expect(row(clicked.id)).toBeVisible()
  await expect(row(clicked.id).getByTestId("answer-mode")).toHaveCount(0)

  // On their page, back to click mode, kept after a reload.
  await visit(owner, `${interviewPath}/candidates/${voiced.id}`)
  const card = owner.getByTestId("candidate-mode").filter({ visible: true })
  const switches = card.getByRole("group").getByRole("button")
  await expect(switches.nth(1)).toHaveAttribute("aria-pressed", "true")
  await shot(owner, "candidate-mode")
  await switches.first().click()
  await expect(switches.first()).toHaveAttribute("aria-pressed", "true")
  await owner.reload()
  await expect(switches.first()).toHaveAttribute("aria-pressed", "true")

  // Once they start, the mode is fixed: the switch is gone.
  const candidate = await signInAs(voiceEmail)
  await finishOneAnswer(candidate, voiceEmail)
  await owner.reload()
  await expect(owner.getByRole("heading", { level: 1 })).toBeVisible()
  await expect(owner.getByTestId("candidate-mode")).toHaveCount(0)
})
