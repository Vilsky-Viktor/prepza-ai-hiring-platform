import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import {
  addPatterns,
  deletePatterns,
  PATTERN_QUESTIONS,
  patternStatus,
} from "../helpers/db-patterns"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { uidOf } from "../helpers/sign-in"
import { randomId } from "../helpers/users"

// The status pill's choices, in its menu's order (frontend/constants/patterns.ts).
const STATUSES = ["proposed", "approved", "in_use", "dismissed"]
// A row's buttons, in their order: dismiss, then approve.
const DISMISS = 0
const APPROVE = 1

/** The test's own pattern rows, by their text. */
function row(page: Page, text: string) {
  return page.getByTestId("pattern-row").filter({ hasText: text })
}

/** Approves or dismisses (`button`) the pattern with `text`, and sees it leave the list; clicked
 * again if the first click came before the page was ready for it. */
async function review(page: Page, text: string, button: number) {
  await expect(async () => {
    await row(page, text).getByRole("button").nth(button).click({ timeout: 2_000 })
    await expect(row(page, text)).toHaveCount(0, { timeout: 3_000 })
  }).toPass()
}

/** Lists the patterns of `status` through the pill above the list, opening its menu again if
 * the first click came too early. */
async function show(page: Page, status: string) {
  const pill = page.getByRole("main").getByRole("button").first()

  await expect(async () => {
    await pill.click()
    await expect(page.getByRole("menu")).toBeVisible({ timeout: 2_000 })
  }).toPass()
  await page.getByRole("menuitemradio").nth(STATUSES.indexOf(status)).click()
  await expect(page).toHaveURL(new RegExp(`status=${status}`))
}

test("superadmin approves and dismisses proposed patterns", async ({ signInSuperadmin }) => {
  const marker = randomId()
  const [approved, dismissed, kept] = await addPatterns(marker, 3)

  try {
    const superadmin = await signInSuperadmin()
    await visit(superadmin, "/superadmin/questions/patterns")

    // Proposed ones are listed with their count and a way to approve or dismiss each.
    for (const text of [approved, dismissed, kept]) {
      await expect(row(superadmin, text)).toBeVisible()
      await expect(row(superadmin, text)).toContainText(new RegExp(`(^|\\D)${PATTERN_QUESTIONS}(\\D|$)`))
      await expect(row(superadmin, text).getByRole("button")).toHaveCount(2)
    }

    await shot(superadmin, "patterns-proposed")

    await review(superadmin, approved, APPROVE)
    await review(superadmin, dismissed, DISMISS)
    await expect(row(superadmin, kept)).toBeVisible()

    // Saved with who reviewed it.
    const uid = await uidOf(superadmin)
    expect(await patternStatus(approved)).toEqual({ status: "approved", reviewed_by: uid })
    expect(await patternStatus(dismissed)).toEqual({ status: "dismissed", reviewed_by: uid })

    // Each is under its status now, with nothing left to decide.
    await show(superadmin, "approved")
    await expect(row(superadmin, approved)).toBeVisible()
    await expect(row(superadmin, approved).getByRole("button")).toHaveCount(0)
    await expect(row(superadmin, dismissed)).toHaveCount(0)
    await shot(superadmin, "patterns-approved")

    await show(superadmin, "dismissed")
    await expect(row(superadmin, dismissed)).toBeVisible()
    await expect(row(superadmin, dismissed).getByRole("button")).toHaveCount(0)
    await expect(row(superadmin, approved)).toHaveCount(0)

    // A reload of the proposed list shows only the one left.
    await show(superadmin, "proposed")
    await expect(row(superadmin, kept)).toBeVisible()
    await expect(row(superadmin, approved)).toHaveCount(0)
    await expect(row(superadmin, dismissed)).toHaveCount(0)
  } finally {
    await deletePatterns(marker)
  }
})
