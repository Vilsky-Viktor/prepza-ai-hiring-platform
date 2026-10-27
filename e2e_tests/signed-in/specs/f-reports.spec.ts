import { readFile } from "node:fs/promises"

import { expect, test } from "../fixtures"
import { createCompany, createInterview, inviteCandidate } from "../helpers/api"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, throwawayEmail } from "../helpers/users"

// The candidates tab's report of all candidates: downloaded as a PDF, or shared.
test("owner downloads and shares the report of all candidates", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  await inviteCandidate(owner, interviewId, throwawayEmail("candidate"))
  await visit(owner, `/companies/${company.id}/interviews/${interviewId}?tab=candidates`)
  await shot(owner, "candidates")

  const downloaded = owner.waitForEvent("download")
  // The report's icon buttons, named for screen readers.
  await owner.getByRole("button", { name: "Download PDF" }).click()
  const file = await downloaded
  expect(file.suggestedFilename()).toMatch(/^Candidates .*\.pdf$/)
  const path = test.info().outputPath(file.suggestedFilename())
  await file.saveAs(path)
  expect((await readFile(path)).subarray(0, 5).toString()).toBe("%PDF-")

  await owner.getByRole("button", { name: "Share report" }).click()
  const dialog = owner.getByRole("dialog")
  await expect(dialog.locator('input[type="email"]')).toBeVisible()
  // The summary goes to each chat app with its own link (icon links named after the app), after
  // a lowercase label.
  await expect(
    dialog.getByRole("link", { name: "WhatsApp" }).locator("xpath=preceding-sibling::span")
  ).toHaveCSS("text-transform", "lowercase")
  await expect(dialog.getByRole("link", { name: "WhatsApp" })).toHaveAttribute("href", /^https:\/\/wa\.me\/\?text=/)
  await expect(dialog.getByRole("link", { name: "Telegram" })).toHaveAttribute("href", /^https:\/\/t\.me\/share\/url\?/)
  await expect(dialog.getByRole("link", { name: "Viber" })).toHaveAttribute("href", /^viber:\/\/forward\?text=/)
  await expect(dialog.getByRole("link", { name: "LINE" })).toHaveAttribute("href", /^https:\/\/line\.me\/R\/share\?text=/)
  await shot(owner, "share-dialog")
  await owner.keyboard.press("Escape")
})
