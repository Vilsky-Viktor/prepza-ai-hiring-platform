import { expect, test } from "../fixtures"
import { createCompany, createInterview, finishOneAnswer, inviteCandidate } from "../helpers/api"
import { PHONE } from "../helpers/layout"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, throwawayEmail } from "../helpers/users"

// Each page a complaint may be about has "copy id", so a user can quote its ID when writing to
// testee: a company, an interview and a candidate, each copying its own.
test("the company, interview and candidate pages copy their IDs", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  await owner.context().grantPermissions(["clipboard-read", "clipboard-write"])
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const candidate = throwawayEmail("quoted")
  await inviteCandidate(owner, interviewId, candidate)
  const copied = () => owner.evaluate(() => navigator.clipboard.readText())

  // The visible one: while a page renders again, Next.js can keep a hidden copy of it.
  const copyId = owner.getByTestId("copy-id").filter({ visible: true })

  await visit(owner, `/companies/${company.id}/interviews`)
  await copyId.click()
  // The check shows for a moment, then the copy icon again.
  await expect(copyId).toHaveAttribute("data-copied", "true")
  await expect(copyId.locator("svg")).toHaveClass(/lucide-check/)
  expect(await copied()).toBe(company.id)
  await shot(owner, "company-copied")
  await expect(copyId).toHaveAttribute("data-copied", "false")
  await expect(copyId.locator("svg")).toHaveClass(/lucide-copy/)

  await visit(owner, `/companies/${company.id}/interviews/${interviewId}?tab=candidates`)
  await copyId.click()
  expect(await copied()).toBe(interviewId)
  await shot(owner, "interview")

  await owner.getByRole("link").filter({ hasText: "quoted" }).click()
  await expect(owner.getByRole("heading", { name: candidate })).toBeVisible()
  const candidatePage = owner.url()
  await copyId.click()
  expect(await copied()).toBe(candidatePage.split("/").pop())
  await shot(owner, "candidate")

  await owner.setViewportSize(PHONE)
  await visit(owner, `/companies/${company.id}/interviews`)
  await shot(owner, "company-phone")
  await owner.goto(candidatePage)
  await expect(copyId).toBeVisible()
  await shot(owner, "candidate-phone")
})

// The account's ID: a button in Settings, and an icon beside the name in the account menu.
test("Settings and the account menu copy the account's ID", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  await owner.context().grantPermissions(["clipboard-read", "clipboard-write"])
  const copied = () => owner.evaluate(() => navigator.clipboard.readText())

  await visit(owner, "/settings")
  await owner.getByRole("main").getByTestId("copy-id").click()
  const uid = await copied()
  expect(uid).toMatch(/^\w{20,}$/)
  await shot(owner, "settings")

  await owner.getByTestId("account-menu").click()
  const item = owner.getByRole("menu").getByTestId("copy-id")
  // Only an icon, named for screen readers (and by its tooltip).
  await expect(item).toHaveText("")
  await expect(item).toHaveAccessibleName("Copy ID")
  await item.click()
  // The menu stays open to show the check mark.
  await expect(item).toHaveAttribute("data-copied", "true")
  await expect(item.locator("svg")).toHaveClass(/lucide-check/)
  expect(await copied()).toBe(uid)
  await shot(owner, "account-menu")
  await owner.keyboard.press("Escape")

  await owner.setViewportSize(PHONE)
  await visit(owner, "/settings")
  await shot(owner, "settings-phone")
})
