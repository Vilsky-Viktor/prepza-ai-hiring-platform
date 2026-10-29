import { type Page } from "@playwright/test"

import { GREENHOUSE_E2E_SECRET } from "../constants"
import { expect, test } from "../fixtures"
import { createCompany, createInterview } from "../helpers/api"
import { addAtsConnection } from "../helpers/db-integrations"
import { integrationRow, openDialog, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { throwawayEmail } from "../helpers/users"

// Connecting each ATS beside Workable (i-ats.spec.ts) from its own page. A real connection needs
// an account at the ATS, so Connect is answered in the browser while the connection is saved
// straight into the database; the backend's connect, refusals and web hook signatures are in
// services/ats/tests/unit/api/v1/test_ats_*_routes.py.

type Ats = "greenhouse" | "teamtailor" | "recruitee" | "breezy"

/** A throwaway owner's company with an interview, on the ATS's page, listed on the tab first. */
async function openAtsPage(signInAs: (email: string) => Promise<Page>, ats: Ats) {
  const owner = await signInAs(throwawayEmail(`ats-${ats}`))
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const tab = `/companies/${company.id}/integrations`
  await visit(owner, tab)
  await expect(integrationRow(owner, `/${ats}`)).toBeVisible()
  await shot(owner, "list")
  await visit(owner, `${tab}/${ats}`)
  const main = owner.getByRole("main")

  return {
    owner,
    company,
    interviewId,
    tab,
    main,
    actions: main.getByTestId("integration-actions").getByRole("button"),
  }
}

/** Fills Connect's `fields` (it stays off until each has a value) and connects, the PUT answered
 * in the browser once the connection is saved with `invited` candidates. */
async function connect(
  { owner, company, interviewId, actions }: Awaited<ReturnType<typeof openAtsPage>>,
  ats: Ats,
  fields: string[],
  invited = 1
) {
  await openDialog(owner, actions.last())
  const dialog = owner.getByRole("dialog")
  const inputs = dialog.locator("form input")
  const submit = dialog.locator("button[type=submit]")
  await expect(inputs).toHaveCount(fields.length)

  for (const [index, value] of fields.entries()) {
    await expect(submit).toBeDisabled()
    await inputs.nth(index).fill(value)
  }

  await shot(owner, "connect")
  await owner.route(`**/api/ats/${ats}?*`, async (route) => {
    if (route.request().method() !== "PUT") {
      return route.fallback()
    }

    await addAtsConnection(company.id, interviewId, { invited }, ats)
    await route.fulfill({ status: 204 })
  })
  await submit.click()
}

/** The web hook section of the dialog that opens by itself once connected, with our address. */
async function webhookSection(owner: Page, ats: Ats) {
  const webhook = owner.getByRole("dialog").locator("section")
  await expect(webhook).toBeVisible({ timeout: 60_000 })
  // The address first, then the field for the secret.
  await expect(webhook.getByRole("textbox").first()).toHaveValue(
    new RegExp(`/api/ats/webhooks/${ats}/[0-9a-f-]{36}$`)
  )

  return webhook
}

// Greenhouse: the info dialog has no web hook until connected; then it opens by itself with the
// web hook's address and secret key to copy. Greenhouse names no account: under the title is the
// company's own name, on the page and the tab's row.
test("an owner connects Greenhouse and finds its web hook in the info dialog", async ({
  signInAs,
}) => {
  const page = await openAtsPage(signInAs, "greenhouse")
  const { owner, main, actions, company, tab } = page

  await openDialog(owner, main.getByTestId("instructions"))
  await expect(owner.getByRole("dialog").getByRole("listitem")).toHaveCount(6)
  await expect(owner.getByRole("dialog").locator("section")).toHaveCount(0)
  await owner.keyboard.press("Escape")

  await connect(page, "greenhouse", ["e2e", "e2e"], 2)
  const webhook = await webhookSection(owner, "greenhouse")
  await expect(webhook.getByRole("textbox").last()).toHaveValue(GREENHOUSE_E2E_SECRET)
  await owner.setViewportSize({ width: 1280, height: 1400 })
  await shot(owner, "info")
  await owner.keyboard.press("Escape")

  // The tag, Instructions and Disconnect (no other setup button), and the linked job with its two
  // invited.
  await expect(main.locator("[data-slot=badge]").filter({ visible: true })).toBeVisible()
  await expect(actions).toHaveCount(2)
  const job = main.getByRole("listitem").filter({ hasText: "E2E Backend developer" })
  await expect(job.getByTestId("invited-count")).toHaveText("2")
  await shot(owner, "page")

  const header = owner.getByRole("heading", { level: 1 }).locator("xpath=../..")
  await expect(header.getByText(company.name, { exact: true }).filter({ visible: true })).toBeVisible()
  await visit(owner, tab)
  await expect(
    integrationRow(owner, "/greenhouse").getByText(company.name, { exact: true })
  ).toBeVisible()
})

// Teamtailor and Recruitee: one connected, their dialog opens with the web hook to set up, where
// the key the ATS makes is pasted and saved for real, still there after a reload.
for (const { ats, fields, key } of [
  { ats: "teamtailor" as const, fields: ["e2e"], key: "e2e-signature-key" },
  { ats: "recruitee" as const, fields: ["acme.recruitee.com", "e2e"], key: "e2e-recruitee-secret" },
]) {
  test(`an owner connects ${ats} and saves its web hook's secret`, async ({ signInAs }) => {
    const page = await openAtsPage(signInAs, ats)
    const { owner, main, actions, tab } = page

    // Not connected yet: no tag and no linked jobs; Instructions and Connect.
    await expect(main.locator("[data-slot=badge]")).toHaveCount(0)
    await expect(main.getByRole("listitem")).toHaveCount(0)
    await expect(owner.getByTestId("link-job")).toHaveCount(0)
    await expect(actions).toHaveCount(2)

    await connect(page, ats, fields)
    const webhook = await webhookSection(owner, ats)
    const secret = webhook.locator('input[type="password"]')
    const save = webhook.locator("form:has(input[type=password]) button[type=submit]")
    await expect(secret).toHaveValue("")
    await expect(save).toBeDisabled()
    await secret.fill(key)
    await save.click()
    await expect(owner.locator('[data-sonner-toast][data-type="success"]')).toBeVisible()
    await expect(save).toBeDisabled()
    await owner.setViewportSize({ width: 1280, height: 1400 })
    await shot(owner, "info")
    await owner.keyboard.press("Escape")

    // Connected, the page has the tag and lists its linked jobs; the secret is kept.
    await visit(owner, `${tab}/${ats}`)
    await expect(main.locator("[data-slot=badge]").filter({ visible: true })).toBeVisible()
    await expect(
      main.getByRole("listitem").filter({ hasText: "E2E Backend developer" })
    ).toBeVisible()
    await openDialog(owner, main.getByTestId("instructions"))
    await expect(owner.getByRole("dialog").locator('section input[type="password"]')).toHaveValue(
      key
    )
  })
}

// Breezy HR connects with one key: prepza adds the web hook in Breezy itself, so it connects
// without a dialog to follow, and its Instructions are the candidate flow alone.
test("an owner connects Breezy HR with one key", async ({ signInAs }) => {
  const page = await openAtsPage(signInAs, "breezy")
  const { owner, main, actions } = page
  await expect(main.locator("[data-slot=badge]")).toHaveCount(0)
  await expect(main.getByRole("listitem")).toHaveCount(0)
  await expect(actions).toHaveCount(2)

  await connect(page, "breezy", ["e2e"])
  await expect(main.locator("[data-slot=badge]").filter({ visible: true })).toBeVisible({
    timeout: 60_000,
  })
  await expect(owner.getByRole("dialog")).toHaveCount(0)
  await expect(owner.getByText("E2E Backend developer").filter({ visible: true })).toBeVisible()
  await shot(owner, "page")

  await openDialog(owner, main.getByTestId("instructions"))
  await expect(owner.getByRole("dialog").getByRole("listitem")).toHaveCount(6)
  await expect(owner.getByRole("dialog").locator("section")).toHaveCount(0)
})
