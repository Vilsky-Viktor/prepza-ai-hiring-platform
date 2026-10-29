import { expect, test } from "../fixtures"
import { api, createCompany } from "../helpers/api"
import { PHONE } from "../helpers/layout"
import { openTab, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail } from "../helpers/users"

// The API's refusal of a public suffix, naming the entry.
const NOT_A_DOMAIN =
  "co.uk isn't a domain a page can be on: use a domain like jobs.acme.com, *.acme.com for its subdomains, or localhost:3000"

type Company = { allowed_domains: string[]; allow_localhost: boolean }

// The API page's SDK tab: an owner adds and takes off the company's allowed domains and lets
// localhost in; each change saves at once and stays after a reload.
test("an owner sets the allowed domains and localhost on the SDK tab", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const sdkTab = `/companies/${company.id}/integrations/api?tab=domains`
  const saved = () => api<Company>(owner, "GET", `/companies/companies/${company.id}`)

  await owner.setViewportSize({ width: 1280, height: 1000 })
  await visit(owner, `/companies/${company.id}/integrations/api`)
  await openTab(owner, "?tab=domains")
  const field = owner.getByRole("main").getByRole("textbox")
  const add = owner.getByRole("main").locator('form button[type="submit"]')
  const entries = owner.getByTestId("allowed-entry")
  const localhost = owner.getByRole("main").getByRole("switch")
  await expect(entries).toHaveCount(0)
  await expect(localhost).not.toBeChecked()
  await shot(owner, "sdk-empty")

  // A public suffix is refused with the API's reason and stays in the field.
  await field.fill("co.uk")
  await add.click()
  await expect(
    owner.locator('[data-sonner-toast][data-type="error"]').filter({ hasText: NOT_A_DOMAIN })
  ).toBeVisible()
  await expect(field).toHaveValue("co.uk")
  await expect(entries).toHaveCount(0)

  // A pasted address keeps only its host; a wildcard is added with Enter.
  await field.fill("https://Jobs.acme-e2e.com/careers")
  await add.click()
  await expect(entries).toHaveText(["jobs.acme-e2e.com"])
  await expect(field).toHaveValue("")
  await field.fill("*.acme-e2e.com")
  await field.press("Enter")
  await expect(entries).toHaveText(["jobs.acme-e2e.com", "*.acme-e2e.com"])

  // localhost let in.
  await localhost.click()
  await expect(localhost).toBeChecked()
  await expect(localhost).toBeEnabled()
  await shot(owner, "sdk-filled")
  await visit(owner, sdkTab)
  await expect(entries).toHaveText(["jobs.acme-e2e.com", "*.acme-e2e.com"])
  await expect(localhost).toBeChecked()
  expect(await saved()).toMatchObject({
    allowed_domains: ["jobs.acme-e2e.com", "*.acme-e2e.com"],
    allow_localhost: true,
  })

  // One domain taken off and localhost shut out again.
  await entries.first().getByRole("button").click()
  await expect(entries).toHaveText(["*.acme-e2e.com"])
  await localhost.click()
  await expect(localhost).not.toBeChecked()
  await expect(localhost).toBeEnabled()
  await visit(owner, sdkTab)
  await expect(entries).toHaveText(["*.acme-e2e.com"])
  await expect(localhost).not.toBeChecked()
  expect(await saved()).toMatchObject({
    allowed_domains: ["*.acme-e2e.com"],
    allow_localhost: false,
  })

  // On a phone the localhost card spans the page from edge to edge, as wide as its <main>.
  await owner.setViewportSize(PHONE)
  const edges = () =>
    localhost.evaluate((element) => {
      const card = element.closest("label")!.getBoundingClientRect()
      const page = element.closest("main")!.getBoundingClientRect()

      return [card.left - page.left, card.right - page.right]
    })
  await expect.poll(edges).toEqual([0, 0])
  await shot(owner, "sdk-phone")
})

// A viewer sees the allowed domains and the localhost switch, with nothing to change.
test("a viewer sees the SDK tab without changing it", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  await api(owner, "PUT", `/companies/companies/${company.id}/allowed-domains`, {
    domains: ["jobs.acme-e2e.com"],
    allow_localhost: true,
  })
  const viewerAddress = ownerEmail()
  const invited = await api<{ token: string }>(
    owner,
    "POST",
    `/companies/members?company_id=${company.id}`,
    { email: viewerAddress, role: "viewer" }
  )
  const viewer = await signInAs(viewerAddress)
  await api(viewer, "POST", `/companies/members/invites/${invited.token}/accept`)

  await visit(viewer, `/companies/${company.id}/integrations/api?tab=domains`)
  await expect(viewer.getByTestId("allowed-entry")).toHaveText(["jobs.acme-e2e.com"])
  await expect(viewer.getByRole("main").getByRole("switch")).toBeChecked()
  await expect(viewer.getByRole("main").getByRole("switch")).toBeDisabled()
  await expect(viewer.getByRole("main").getByRole("textbox")).toHaveCount(0)
  await expect(viewer.getByTestId("allowed-entry").getByRole("button")).toHaveCount(0)
  await shot(viewer, "sdk-viewer")
})
