import { expect, test } from "../fixtures"
import { createCompany, createInterview, finishOneAnswer, inviteCandidate } from "../helpers/api"
import { expectAccessible } from "../helpers/accessibility"
import { inviteToken } from "../helpers/db"
import { visit } from "../helpers/navigation"
import { setScheme } from "../helpers/theme"
import { ownerEmail, throwawayEmail } from "../helpers/users"

// The signed-in screens checked with axe (WCAG 2.0 A and AA), with motion reduced so no
// animation is caught halfway; known issues are listed in helpers/accessibility.ts. Scans find
// about half of the issues, so the keyboard tests stay (y-keyboard.spec.ts).

// A company's screens, as its owner sees them: the companies list, the interviews, an interview's
// topics and candidates, the invite dialog, a finished candidate's report, billing and settings,
// in light and in dark.
for (const scheme of ["light", "dark"] as const) {
  test(`a company's screens meet WCAG 2.0 AA in ${scheme}`, async ({ signInAs }) => {
    const owner = await signInAs(ownerEmail())
    await owner.emulateMedia({ reducedMotion: "reduce" })
    await setScheme(owner, scheme)
    const company = await createCompany(owner)
    const interviewId = await createInterview(owner, company.id)
    const candidate = throwawayEmail("axe")
    await inviteCandidate(owner, interviewId, candidate)
    await finishOneAnswer(await signInAs(candidate), candidate)
    const interview = `/companies/${company.id}/interviews/${interviewId}`

    for (const path of [
      "/companies",
      `/companies/${company.id}/interviews`,
      interview,
      `/companies/${company.id}/billing`,
      "/settings",
    ]) {
      await visit(owner, path)
      await expect(owner.getByRole("main").getByRole("heading", { level: 1 })).toBeVisible()
      await expectAccessible(owner, path)
    }

    await visit(owner, `${interview}?tab=candidates`)
    const row = owner.getByRole("main").getByRole("link").filter({ hasText: candidate })
    await expect(row).toBeVisible()
    await expectAccessible(owner, "candidates")
    await owner.getByTestId("new-candidate").filter({ visible: true }).click()
    await expect(owner.getByRole("dialog")).toBeVisible()
    await expectAccessible(owner, "invite dialog")
    await owner.keyboard.press("Escape")

    await row.click()
    await expect(owner.getByTestId("human-review").filter({ visible: true })).toBeVisible()
    await expectAccessible(owner, "candidate report")
  })
}

// A candidate's screens: the invitation with its rules and pledge, and a question of the
// interview, timed.
test("a candidate's invitation and question meet WCAG 2.0 AA", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const email = throwawayEmail("axe-candidate")
  await inviteCandidate(owner, interviewId, email)
  const candidate = await signInAs(email)
  await candidate.emulateMedia({ reducedMotion: "reduce" })

  await visit(candidate, `/invite/${await inviteToken(email)}`)
  const start = candidate.getByRole("main").getByRole("button")
  await expect(start).toBeVisible()
  await expectAccessible(candidate, "invitation")

  await candidate.getByTestId("start-pledge").filter({ visible: true }).click()
  await start.click()
  await expect(candidate).toHaveURL(/\/sessions\//)
  await expect(candidate.getByRole("timer")).toBeVisible()
  await expectAccessible(candidate, "question")
})
