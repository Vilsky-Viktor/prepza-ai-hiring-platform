import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany } from "../helpers/api"
import { billingNow, deleteLimitChanges } from "../helpers/db-ai"
import { addTemplate, deleteTemplate } from "../helpers/db-library"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { throwawayEmail } from "../helpers/users"

type Limit = {
  name: string
  value: number
  default: number
  unit: string
  counted: boolean
  changed: boolean
}

// The value the test changes: no other test makes a hard test, so a moment at 80 disturbs
// nothing.
const HARD = "QUESTION_SECONDS_HARD"
const CHANGED = 80

async function limits(superadmin: Page) {
  return (await api<{ limits: Limit[] }>(superadmin, "GET", "/billing/superadmin/limits")).limits
}

/** A new test made from the hard template, with its seconds a question. */
async function newHardTest(owner: Page, companyId: string, templateId: string) {
  return api<{ id: string; question_seconds: number }>(
    owner,
    "POST",
    `/companies/interviews/from-template?company_id=${companyId}`,
    { template_id: templateId }
  )
}

// A new test starts with its level's seconds a question, as set in the admin zone's Controls,
// where the value is saved and set back. That a change reaches the next new test is billing's
// integration test (test_limits.py) and companies' unit test (test_interviews_from_templates.py).
// The value is global, but only for the moment it's changed, and no other test makes a hard test.
test("a new hard test starts with the hard level's seconds, set in Controls", async ({
  signInAs,
  signInSuperadmin,
}) => {
  const superadmin = await signInSuperadmin()
  const hard = (await limits(superadmin)).find((found) => found.name === HARD)!
  test.skip(hard.changed, "The value is already changed locally: left as it is")
  const owner = await signInAs(throwawayEmail("level-seconds"))
  const company = await createCompany(owner)
  const templateId = await addTemplate(`E2E hard ${Date.now()}`, 10, "company", "hard")
  const start = await billingNow()

  try {
    // The hard level's default, on the new test's settings tab.
    const made = await newHardTest(owner, company.id, templateId)
    expect(made.question_seconds).toBe(hard.default)
    await visit(owner, `/companies/${company.id}/interviews/${made.id}?tab=settings`)
    await expect(owner.getByRole("main").getByRole("spinbutton").first()).toHaveValue(
      String(hard.default)
    )
    await shot(owner, "hard-test-seconds")

    // Controls lists it as a plain value with the others, each at its value.
    await visit(superadmin, "/superadmin/controls")
    for (const found of (await limits(superadmin)).filter((limit) => !limit.counted)) {
      await expect(
        superadmin.getByTestId(`limit-${found.name}`).getByRole("spinbutton")
      ).toHaveValue(String(found.value))
    }

    const row = superadmin.getByTestId(`limit-${HARD}`)
    await row.getByRole("spinbutton").fill(String(CHANGED))
    await row.getByRole("button").first().click()
    await expect(superadmin.locator('[data-sonner-toast][data-type="success"]')).toBeVisible()
    await expect(row.getByRole("button")).toHaveCount(2)
    await expect(
      superadmin.getByTestId("limit-changes").getByRole("listitem").first().locator("span").first()
    ).toHaveText(new RegExp(`\\D${CHANGED}\\D*$`))
    expect((await limits(superadmin)).find((found) => found.name === HARD)!.value).toBe(CHANGED)
    await shot(superadmin, "hard-seconds-changed")

    // Set back.
    await row.getByRole("button").last().click()
    await expect(row.getByRole("spinbutton")).toHaveValue(String(hard.default))
  } finally {
    if ((await limits(superadmin)).find((found) => found.name === HARD)?.changed) {
      await api(superadmin, "DELETE", `/billing/superadmin/limits/${HARD}`)
    }

    await deleteLimitChanges(HARD, start)
    await deleteTemplate(templateId)
  }
})
