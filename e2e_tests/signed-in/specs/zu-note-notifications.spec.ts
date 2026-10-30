import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, createInterview } from "../helpers/api"
import { PHONE } from "../helpers/layout"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { throwawayEmail } from "../helpers/users"

// The team's notes reach the other members' bells: one item per interview that counts the notes
// and names their latest authors, opening the interview's notes tab. The author's own bell
// doesn't get it.

/** The bell's items, opened. */
async function bellItems(page: Page) {
  await page.getByTestId("notifications").click()

  return page.getByRole("menu").getByRole("menuitem")
}

test("a member hears of the team's new notes in one item per interview", async ({
  signInAs,
}) => {
  const annEmail = throwawayEmail("notes-ann")
  const bobEmail = throwawayEmail("notes-bob")
  const ann = await signInAs(annEmail, undefined, "Ann Lee")
  const company = await createCompany(ann)
  const interviewId = await createInterview(ann, company.id)
  const members = `/companies/members?company_id=${company.id}`
  await api(ann, "POST", members, { email: bobEmail, role: "viewer" })
  const [invited] = (await api<{ email: string; token: string }[]>(ann, "GET", members)).filter(
    (member) => member.email === bobEmail,
  )
  const bob = await signInAs(bobEmail, undefined, "Bob Stone")
  await api(bob, "POST", `/companies/members/invites/${invited.token}/accept`)

  const notes = `/companies/interviews/${interviewId}/notes`
  await api(ann, "POST", notes, { text: "Shortlist the top 5" })
  await api(ann, "POST", notes, { text: "Calls on Monday" })
  const tab = `/companies/${company.id}/interviews/${interviewId}?tab=notes`

  // Bob's bell: one item with both notes, by Ann, linking to the notes tab.
  await visit(bob, "/companies")
  const item = bob.getByRole("menu").locator(`a[href$="${tab}"]`)
  await expect(async () => {
    await bob.reload()
    await bellItems(bob)
    await expect(item).toHaveCount(1, { timeout: 3000 })
    await expect(item).toContainText("2")
  }).toPass({ timeout: 60_000 })
  await expect(item).toContainText("Ann Lee")
  await shot(bob, "bell-notes", false)

  // It opens the interview's notes, the newest first.
  await item.click()
  await expect(bob).toHaveURL(new RegExp(`${interviewId}\\?tab=notes$`))
  await expect(bob.getByTestId("note-text").filter({ visible: true }).first()).toHaveText(
    "Calls on Monday",
  )

  // Ann wrote them: her bell has no item about them.
  await visit(ann, "/companies")
  await bellItems(ann)
  await expect(ann.getByRole("menu").locator(`a[href$="${tab}"]`)).toHaveCount(0)

  await bob.setViewportSize(PHONE)
  await visit(bob, "/companies")
  await bellItems(bob)
  await expect(item).toHaveCount(1)
  await shot(bob, "bell-notes-phone", false)
})
