import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, createInterview } from "../helpers/api"
import { createKey, deleteKey, keyNote, mcpTool } from "../helpers/api-keys"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { randomId, throwawayEmail } from "../helpers/users"

type Member = { id: string; email: string; token: string | null }

/** Opens a filter's menu (`nth`: member, then action), clicking again if the first click came
 * before the page was ready for it. */
async function openFilter(page: Page, nth: number) {
  await expect(async () => {
    await page.getByTestId("action-filters").getByRole("button").nth(nth).click()
    await expect(page.getByRole("menu")).toBeVisible({ timeout: 2_000 })
  }).toPass()

  return page.getByRole("menu").getByRole("menuitemradio")
}

/** Today and tomorrow in the browser's own days, as a date field takes them. */
function localDay(page: Page, after = 0) {
  return page.evaluate((days) => {
    const day = new Date()
    day.setDate(day.getDate() + days)

    return `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, "0")}-${String(day.getDate()).padStart(2, "0")}`
  }, after)
}

// The owner's action log: Ann (the owner) invites Bob as an admin and Vic as a viewer, both
// join, and Bob renames the company. Ann sees her own and Bob's actions, and narrows them by
// member, by kind of action and by days; Bob and Vic have no action log.
test("the owner reads and filters the company's action log; admins and viewers have none", async ({
  signInAs,
}) => {
  const annEmail = throwawayEmail("log-ann")
  const bobEmail = throwawayEmail("log-bob")
  const vicEmail = throwawayEmail("log-vic")
  const ann = await signInAs(annEmail)
  const company = await createCompany(ann)
  const members = `/companies/members?company_id=${company.id}`
  await api(ann, "POST", members, { email: bobEmail, role: "admin" })
  await api(ann, "POST", members, { email: vicEmail, role: "viewer" })
  const tokens = Object.fromEntries(
    (await api<Member[]>(ann, "GET", members)).map((member) => [member.email, member.token])
  )
  const bob = await signInAs(bobEmail)
  await api(bob, "POST", `/companies/members/invites/${tokens[bobEmail]}/accept`)
  const vic = await signInAs(vicEmail)
  await api(vic, "POST", `/companies/members/invites/${tokens[vicEmail]}/accept`)
  const renamed = `E2E ${randomId()}`
  await api(bob, "PATCH", `/companies/companies/${company.id}/name`, { title: renamed })

  const path = `/companies/${company.id}/actions`
  await visit(ann, `/companies/${company.id}/interviews`)
  // The owner's company tabs lead to the action log.
  await expect(ann.getByRole("main").getByRole("navigation").locator(`a[href$="${path}"]`)).toBeVisible()
  await visit(ann, path)
  const main = ann.getByRole("main")
  const rows = main.getByRole("listitem")
  const filters = ann.getByTestId("action-filters")
  // Ann's invites and Bob's and Vic's joining, Bob's rename: who did each, and to what.
  await expect(rows.filter({ hasText: renamed }).filter({ hasText: bobEmail })).toHaveCount(1)
  await expect(rows.filter({ hasText: vicEmail }).filter({ hasText: annEmail })).toHaveCount(1)
  await expect(rows).toHaveCount(5)
  await shot(ann, "action-log")

  // Bob's actions only: his joining and his rename.
  await (await openFilter(ann, 0)).filter({ hasText: bobEmail }).click()
  await expect(ann).toHaveURL(/member_id=/)
  await expect(rows).toHaveCount(2)
  await expect(rows.filter({ hasText: vicEmail })).toHaveCount(0)
  await expect(rows.filter({ hasText: annEmail })).toHaveCount(0)
  await shot(ann, "action-log-member")

  // Everyone again, then only the team's actions (the fourth choice: after "all", interviews and
  // candidates): the rename, a company action, goes.
  await (await openFilter(ann, 0)).first().click()
  await expect(ann).not.toHaveURL(/member_id=/)
  await (await openFilter(ann, 1)).nth(3).click()
  await expect(ann).toHaveURL(/group=team/)
  await expect(rows).toHaveCount(4)
  await expect(rows.filter({ hasText: renamed })).toHaveCount(0)
  await shot(ann, "action-log-group")

  // From tomorrow: nothing; from today: today's actions again.
  const days = filters.locator('input[type="date"]')
  await days.first().fill(await localDay(ann, 1))
  await expect(ann).toHaveURL(/from=/)
  await expect(rows).toHaveCount(0)
  await days.first().fill(await localDay(ann))
  await expect(rows).toHaveCount(4)
  // Up to today: the same.
  await days.last().fill(await localDay(ann))
  await expect(ann).toHaveURL(/to=/)
  await expect(rows).toHaveCount(4)
  await shot(ann, "action-log-days")

  // An admin and a viewer have no tab, and the page sends them to the company's interviews.
  for (const member of [bob, vic]) {
    await visit(member, `/companies/${company.id}/interviews`)
    await expect(member.getByRole("main").getByRole("navigation").first()).toBeVisible()
    await expect(member.getByRole("main").locator(`a[href$="/actions"]`)).toHaveCount(0)
    await visit(member, path)
    await expect(member).toHaveURL((url) => url.pathname.endsWith(`/companies/${company.id}/interviews`))
  }
})

// An API key is the author of what it does: a key adds a note through the API and another
// through MCP, and a second key adds one and is then deleted. The log names the live key in the
// rows of what it did, each marked with the way it came; the deleted key's row names neither the
// key nor the member who made it.
test("the action log names the API key that acted, through the API or MCP", async ({
  signInAs,
}) => {
  const ownerAddress = throwawayEmail("log-keys")
  const owner = await signInAs(ownerAddress)
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const permissions = ["notes:add", "mcp"]
  const live = `Careers site ${randomId()}`
  const gone = `Old agent ${randomId()}`
  const { key } = await createKey(owner, company.id, live, permissions)
  const old = await createKey(owner, company.id, gone, permissions)
  await keyNote(owner, key, interviewId, `Through the API ${randomId()}`)
  await mcpTool(owner, key, "add_interview_note", {
    interview_id: interviewId,
    text: `Through MCP ${randomId()}`,
  })
  await keyNote(owner, old.key, interviewId, `From a key deleted later ${randomId()}`)
  await deleteKey(owner, company.id, old.id)

  await visit(owner, `/companies/${company.id}/actions`)
  const rows = owner.getByRole("main").getByRole("listitem")
  const through = (via: string) => rows.filter({ has: owner.locator(`[data-via="${via}"]`) })
  await expect(through("mcp").filter({ hasText: live })).toHaveCount(1)
  await expect(through("api").filter({ hasText: live })).toHaveCount(1)
  // The deleted key's note: by the API, named by neither its key nor its maker.
  const deleted = through("api").filter({ hasNotText: live })
  await expect(deleted).toHaveCount(1)
  await expect(deleted).not.toContainText(ownerAddress)
  await expect(deleted).not.toContainText(gone)
  await shot(owner, "action-log-keys")
})
