import { readFile } from "node:fs/promises"

import { expect, test } from "../fixtures"
import { api, createCompany, createInterview, inviteCandidate } from "../helpers/api"
import { finishInvite } from "../helpers/db"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, throwawayEmail } from "../helpers/users"

type Member = { email: string; token: string | null }

// The owner's bias-audit export on the action log page: a CSV of the candidates who finished,
// with their grades and results, all interviews or one; the export shows in the log. An admin
// has neither the page nor the export.
test("the owner exports finished candidates' outcomes for a bias audit", async ({ signInAs }) => {
  const ownerAddress = ownerEmail()
  const adminAddress = throwawayEmail("audit-admin")
  const owner = await signInAs(ownerAddress)
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const passing = throwawayEmail("audit-pass")
  const failing = throwawayEmail("audit-fail")
  const waiting = throwawayEmail("audit-wait")

  for (const email of [passing, failing, waiting]) {
    await inviteCandidate(owner, interviewId, email)
  }

  await finishInvite(passing.toLowerCase(), 95)
  await finishInvite(failing.toLowerCase(), 10)

  const path = `/companies/${company.id}/actions`
  await visit(owner, path)
  await owner.getByTestId("bias-audit-export").click()
  const dialog = owner.getByRole("dialog")
  await expect(dialog.locator('input[type="date"]')).toHaveCount(2)
  await shot(owner, "bias-audit-export")

  const downloaded = owner.waitForEvent("download")
  await dialog.locator('button[type="submit"]').click()
  const file = await downloaded
  expect(file.suggestedFilename()).toMatch(/^testee-bias-audit-\d{4}-\d{2}-\d{2}\.csv$/)
  const saved = test.info().outputPath(file.suggestedFilename())
  await file.saveAs(saved)
  const [header, ...rows] = (await readFile(saved, "utf8")).trim().split(/\r?\n/)
  const columns = header.split(",")
  const byEmail = Object.fromEntries(
    rows.map((row) => {
      const cells = Object.fromEntries(row.split(",").map((cell, at) => [columns[at], cell]))

      return [cells.candidate_email, cells]
    })
  )

  // Only the two who finished, each with its grade and whether they passed; the one still
  // invited isn't in it, and nothing about who they are but the email.
  expect(Object.keys(byEmail).sort()).toEqual([failing, passing].map((email) => email.toLowerCase()).sort())
  expect(byEmail[passing.toLowerCase()]).toMatchObject({ interview_id: interviewId, grade: "95", passed: "true", above_median: "true" })
  expect(byEmail[failing.toLowerCase()]).toMatchObject({ grade: "10", passed: "false", above_median: "false" })
  expect(columns).not.toContain("name")
  await expect(dialog).toBeHidden()

  // The export is in the log, newest first.
  await owner.reload()
  await expect(owner.getByRole("main").getByRole("listitem").first()).toContainText(ownerAddress)

  // An admin has no action log, so no export: the page sends them to the interviews.
  await api(owner, "POST", `/companies/members?company_id=${company.id}`, { email: adminAddress, role: "admin" })
  const tokens = await api<Member[]>(owner, "GET", `/companies/members?company_id=${company.id}`)
  const admin = await signInAs(adminAddress)
  const token = tokens.find((member) => member.email === adminAddress.toLowerCase())?.token
  await api(admin, "POST", `/companies/members/invites/${token}/accept`)
  await visit(admin, path)
  await expect(admin).toHaveURL((url) => url.pathname.endsWith(`/companies/${company.id}/interviews`))
  await expect(admin.getByTestId("bias-audit-export")).toHaveCount(0)
})
