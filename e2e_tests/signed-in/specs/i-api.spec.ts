import { expect, test } from "../fixtures"
import { API_URL } from "../constants"
import { createCompany, createInterview } from "../helpers/api"
import { markWebhookFailing, setWebhookMaker } from "../helpers/db-integrations"
import { settled } from "../helpers/layout"
import { openDialog, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail } from "../helpers/users"

// The API sits last on the integrations tab and opens its own page, where an owner makes a key
// (shown once) and adds a web hook (its secret shown once).
test("an owner makes an API key and adds a web hook", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const tab = `/companies/${company.id}/integrations`

  await owner.setViewportSize({ width: 1280, height: 1400 })
  await visit(owner, tab)
  await shot(owner, "list")
  await visit(owner, `${tab}/api`)
  await shot(owner, "empty")

  // The open tab's action beside the docs: a new key, or a new web hook.
  const action = owner.getByTestId("integration-actions").locator("button")
  await openDialog(owner, action)
  await owner.getByRole("dialog").getByRole("textbox").fill("Careers site")
  // When it expires: nothing picked yet, so the key can't be made; the menu doesn't move the dialog.
  const create = owner.getByRole("dialog").locator('button[type="submit"]')
  const expiry = owner.getByRole("dialog").locator('[aria-haspopup="menu"]')
  // The expiries in the API's order: 1, 3, 6 and 12 months, then never.
  const expiries = owner.getByRole("menu").getByRole("menuitemradio")
  await expect(create).toBeDisabled()
  await settled(owner.getByRole("dialog"))
  const closed = await owner.getByRole("dialog").boundingBox()
  await expiry.click()
  await expect(owner.getByRole("menu")).toBeVisible()
  expect(await owner.getByRole("dialog").boundingBox()).toEqual(closed)
  await shot(owner, "expiry-menu")
  // Never expiring is allowed, with a warning under the select while it's picked.
  const warning = owner.getByRole("dialog").getByRole("status")
  await expiries.last().click()
  await expect(warning).toBeVisible()
  await shot(owner, "never-warning")
  await expiry.click()
  await expiries.nth(3).click()
  await expect(warning).toHaveCount(0)
  await expect(create).toBeEnabled()
  // What the key may do: "Select all", then each group's permissions (interviews: read, create;
  // candidates: read, invite, change, delete; credits: read; AI agents). A new key starts with
  // the two reads; ticking Invite ticks Candidates read and keeps it ticked.
  const ticks = owner.getByRole("dialog").getByRole("checkbox")
  const checked = owner.getByRole("dialog").locator('[role=checkbox][aria-checked="true"]')
  await expect(ticks).toHaveCount(9)
  await expect(checked).toHaveCount(2)
  await expect(ticks.nth(1)).toBeChecked()
  await expect(ticks.nth(3)).toBeChecked()
  await ticks.nth(4).click()
  await expect(ticks.nth(4)).toBeChecked()
  await expect(ticks.nth(3)).toBeDisabled()
  await shot(owner, "new-key")
  await create.click()
  // The key, shown this once in a field to copy.
  const shown = owner.getByRole("dialog").getByRole("textbox")
  await expect(shown).toHaveValue(/^pz_/)
  await shot(owner, "key-shown")
  const key = await shown.inputValue()
  await owner.keyboard.press("Escape")

  // The key works: the company's interview, and its candidate invited through the API.
  const headers = { Authorization: `Bearer ${key}` }
  const listed = await owner.request.get(`${API_URL}/v1/interviews`, { headers })
  expect(listed.status()).toBe(200)
  expect((await listed.json()).map((item: { id: string }) => item.id)).toEqual([interviewId])
  const invited = await owner.request.post(`${API_URL}/v1/interviews/${interviewId}/candidates`, {
    headers,
    data: { email: "delivered+e2e-api-candidate@resend.dev" },
  })
  expect(invited.status()).toBe(201)
  expect(await invited.json()).toMatchObject({ status: "invited", progress: 0 })
  const refused = await owner.request.get(`${API_URL}/v1/interviews`, {
    headers: { Authorization: "Bearer pz_wrong" },
  })
  expect(refused.status()).toBe(401)
  // What the key wasn't given is refused, naming the permission it lacks.
  const credits = await owner.request.get(`${API_URL}/v1/credits`, { headers })
  expect(credits.status()).toBe(403)
  expect(await credits.json()).toEqual({
    detail: "This API key doesn't have the credits:read permission.",
    code: "missing_permission",
  })

  // Its row shows its permissions as tags: interviews read, candidates read and invite.
  const tags = owner.getByTestId("key-permissions").first().locator("[data-slot=badge]")
  await expect(tags).toHaveCount(3)
  await shot(owner, "keys-tab")

  // Narrowed: Invite unticked and saved, the key can't invite any more, and Invite can't be
  // ticked again (adding one means a new key).
  const editKey = owner.getByRole("main").getByRole("listitem").first().getByRole("button").first()
  await openDialog(owner, editKey)
  const keyTicks = owner.getByRole("dialog").getByRole("checkbox")
  await expect(keyTicks).toHaveCount(8)
  await keyTicks.nth(3).click()
  await expect(keyTicks.nth(3)).not.toBeChecked()
  await shot(owner, "narrow-key")
  await owner.getByRole("dialog").getByRole("button").last().click()
  await expect(owner.getByRole("dialog")).toHaveCount(0)
  await expect(tags).toHaveCount(2)
  const uninvited = await owner.request.post(
    `${API_URL}/v1/interviews/${interviewId}/candidates`,
    { headers, data: { email: "delivered+e2e-api-narrowed@resend.dev" } }
  )
  expect(uninvited.status()).toBe(403)
  expect((await uninvited.json()).detail).toBe(
    "This API key doesn't have the candidates:invite permission."
  )
  await openDialog(owner, editKey)
  await expect(keyTicks.nth(3)).toBeDisabled()
  await expect(keyTicks.nth(3)).not.toBeChecked()
  await owner.keyboard.press("Escape")

  // The web hooks have a tab of their own, with its own button: a dialog with no expiry.
  await owner.locator('main nav a[href$="?tab=webhooks"]:visible').click()
  await expect(owner).toHaveURL(/\?tab=webhooks$/)

  // Only HTTPS addresses on the internet: anything else is refused, in a red toast.
  await openDialog(owner, action)
  await expect(expiry).toHaveCount(0)
  await owner.getByRole("dialog").getByRole("textbox").fill("http://example.com/prepza")
  await create.click()
  await expect(owner.locator('[data-sonner-toast][data-type="error"]')).toContainText(
    "Use an HTTPS address that's reachable from the internet"
  )
  await shot(owner, "webhook-refused")
  await owner.getByRole("dialog").getByRole("textbox").fill("https://example.com/prepza")
  await create.click()
  // Its signing secret, shown this once.
  await expect(owner.getByRole("dialog").getByRole("textbox")).toHaveValue(/^whsec_/)
  await shot(owner, "secret-shown")
  await owner.keyboard.press("Escape")
  await expect(owner.getByText("https://example.com/prepza")).toBeVisible()
  await shot(owner, "filled")
  await visit(owner, tab)
  await shot(owner, "list-filled")

  // A web hook that stopped taking events, after days of retries, is paused, and says so.
  await markWebhookFailing("https://example.com/prepza", company.id)
  await visit(owner, `${tab}/api?tab=webhooks`)
  await expect(owner.getByText(/^Paused: it didn't answer for 3 days/)).toBeVisible()
  await shot(owner, "webhook-failing")

  // One whose member is no longer an owner or admin gets no events, and says so instead.
  await setWebhookMaker("https://example.com/prepza", company.id, "removed-member")
  await visit(owner, `${tab}/api?tab=webhooks`)
  await expect(
    owner.getByText(
      "Stopped: the member who added it is no longer an owner or admin. Add it again to keep getting results."
    )
  ).toBeVisible()
  await shot(owner, "webhook-stopped")
})
