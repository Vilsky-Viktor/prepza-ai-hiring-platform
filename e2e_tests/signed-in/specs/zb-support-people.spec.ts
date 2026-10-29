import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, createInterview } from "../helpers/api"
import { EMAIL_BOXES, emailBoxes } from "../helpers/emails"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { supportId, supportLink, supportSearch } from "../helpers/support"
import { companyUnsubscribePath, confirmUnsubscribe } from "../helpers/unsubscribe"
import { ownerEmail, throwawayEmail } from "../helpers/users"

/** A company's row in the candidate page's company emails. */
function companyRow(page: Page, name: string) {
  return page.locator("main div.divide-y > div", { hasText: name })
}

/** The account's email settings on its support page, once loaded. */
async function accountEmails(page: Page, userId: string) {
  await visit(page, `/superadmin/support/users/${userId}`)
  await expect(emailBoxes(page)).toHaveCount(EMAIL_BOXES.count)

  return emailBoxes(page)
}

// Someone asked prepza by email to stop its emails: a superadmin searches the address, turns its
// account's optional emails off on the account's page and, on the candidate's page, stops one
// inviting company's emails, then resumes them. Only the person turns marketing on, and a stop
// they made from an email's link stays theirs.
test("superadmin stops and resumes the emails to an address", async ({
  browser,
  signInAs,
  signInSuperadmin,
}) => {
  const address = throwawayEmail("asked")
  const person = await signInAs(address)
  await person.context().close()
  const companies = []
  const invites = []

  for (let i = 0; i < 2; i++) {
    const owner = await signInAs(ownerEmail())
    const company = await createCompany(owner)
    const interviewId = await createInterview(owner, company.id)
    invites.push(
      await api<{ id: string }>(owner, "POST", `/companies/interviews/${interviewId}/candidates`, {
        email: address,
      })
    )
    companies.push(company)
  }

  // The person stopped the second company's emails themselves, from an email's link.
  const context = await browser.newContext()
  const guest = await context.newPage()
  await visit(guest, companyUnsubscribePath(address, companies[1].id, companies[1].name))
  await confirmUnsubscribe(guest)
  await context.close()

  // The address, typed in capitals, finds its account first, then the candidates invited at it.
  const superadmin = await signInSuperadmin()
  const found = await supportSearch(superadmin, address.toUpperCase())
  await expect(found.first()).toHaveAttribute("href", /\/superadmin\/support\/users\/[^/]+$/)

  for (const invite of invites) {
    await expect(supportLink(superadmin, "candidates", invite.id)).toHaveCount(1)
  }

  await shot(superadmin, "support-address")
  const userId = await supportId(found.first())
  await found.first().click()
  await expect(superadmin.getByRole("heading", { level: 1 })).toHaveText(address)
  const boxes = emailBoxes(superadmin)

  // The account's settings as a new user has them: updates on (the first sign-in), offers off.
  await expect(boxes).toHaveCount(EMAIL_BOXES.count)
  await expect(boxes.nth(EMAIL_BOXES.reminders)).toBeChecked()
  await expect(boxes.nth(EMAIL_BOXES.offers)).not.toBeChecked()
  // Not a member of any company: no company to open.
  await expect(supportLink(superadmin, "companies")).toHaveCount(0)
  await shot(superadmin, "user")

  // Every optional email off, still off after a reload.
  await superadmin.getByTestId("turn-off-all").click()

  for (let index = 0; index < EMAIL_BOXES.count; index++) {
    await expect(boxes.nth(index)).not.toBeChecked()
  }

  await accountEmails(superadmin, userId)

  for (let index = 0; index < EMAIL_BOXES.count; index++) {
    await expect(boxes.nth(index)).not.toBeChecked()
  }

  // Marketing goes back on only by the person's own choice: the API refuses, saying why.
  await boxes.nth(EMAIL_BOXES.offers).click()
  await expect(
    superadmin.getByText("Only the person can turn on product updates and offers.", { exact: false })
  ).toBeVisible()
  await shot(superadmin, "user-marketing-refused")
  await accountEmails(superadmin, userId)
  await expect(boxes.nth(EMAIL_BOXES.offers)).not.toBeChecked()

  // The candidate's page lists both inviting companies' emails. The first company's are sent:
  // they can be stopped here. The person's own stop has nothing to press.
  await visit(superadmin, `/superadmin/support/candidates/${invites[0].id}`)
  await expect(superadmin.getByRole("heading", { level: 1 })).toHaveText(address)
  const stopped = companyRow(superadmin, companies[0].name)
  const theirs = companyRow(superadmin, companies[1].name)
  await expect(stopped.getByTestId("stop-emails")).toBeVisible()
  await expect(theirs).toBeVisible()
  await expect(theirs.getByRole("button")).toHaveCount(0)
  await shot(superadmin, "candidate-emails")

  // One company's emails stopped (the person's own stop stays as it is), still after a reload;
  // then resumed.
  await stopped.getByTestId("stop-emails").click()
  await expect(stopped.getByTestId("resume-emails")).toBeVisible()
  await expect(stopped.getByTestId("stop-emails")).toHaveCount(0)
  await expect(theirs.getByRole("button")).toHaveCount(0)
  await superadmin.reload()
  await expect(stopped.getByTestId("resume-emails")).toBeVisible()
  await shot(superadmin, "candidate-emails-stopped")
  await superadmin.setViewportSize({ width: 390, height: 844 })
  await shot(superadmin, "candidate-emails-stopped-phone")
  await superadmin.setViewportSize({ width: 1280, height: 800 })
  await stopped.getByTestId("resume-emails").click()
  await expect(stopped.getByTestId("stop-emails")).toBeVisible()
  await expect(stopped.getByTestId("resume-emails")).toHaveCount(0)
  await expect(theirs.getByRole("button")).toHaveCount(0)
})
