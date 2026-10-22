import { expect, test } from "../fixtures"
import { api, createCompany, createInterview } from "../helpers/api"
import { addAtsConnection } from "../helpers/db-integrations"
import { integrationRow, openDialog, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { throwawayEmail } from "../helpers/users"

// The ATS tab lists Workable (beside Greenhouse) with what connecting needs and how candidates flow; Workable's own
// page has its linked jobs with how their candidates went. A real connection needs a Workable
// account, so one is saved straight into the database, and Workable's lists are answered in the
// browser.
test("an owner sees how to connect Workable and manages its linked jobs", async ({
  signInAs,
}) => {
  const owner = await signInAs(throwawayEmail("ats"))
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const tab = `/companies/${company.id}/integrations`

  await visit(owner, `/companies/${company.id}/interviews`)
  await owner.locator(`main nav a[href$="/integrations"]:visible`).click()
  // The tab compiles on its first visit (slow on the dev server).
  await expect(owner).toHaveURL(new RegExp(`${tab}$`), { timeout: 60_000 })
  // Not connected yet: no tag; Instructions and Connect.
  const row = integrationRow(owner, "/workable")
  const actions = row.getByTestId("integration-actions").getByRole("button")
  await expect(row.locator("[data-slot=badge]")).toHaveCount(0)
  await expect(actions).toHaveCount(2)

  // The candidate flow, explained before connecting.
  await openDialog(owner, row.getByTestId("instructions"))
  await expect(owner.getByRole("dialog").getByRole("listitem")).toHaveCount(6)
  await shot(owner, "candidate-flow")
  await owner.keyboard.press("Escape")

  // The token's form: Connect waits for its fields.
  await actions.last().click()
  const connect = owner.getByRole("dialog")
  await expect(connect.getByRole("textbox").first()).toBeVisible()
  await expect(connect.locator("button[type=submit]")).toBeDisabled()
  await shot(owner, "connect")
  await owner.keyboard.press("Escape")

  await addAtsConnection(company.id, interviewId, { invited: 3, notInvited: 2 })
  await visit(owner, tab)
  await expect(row.locator("[data-slot=badge]")).toBeVisible()
  await expect(row.getByText("e2e-acme")).toBeVisible()

  // The row opens Workable's page: its linked jobs and how their candidates went.
  await row.getByRole("link").click()
  await expect(owner).toHaveURL(new RegExp(`${tab}/workable$`))
  const job = owner.getByRole("main").getByRole("listitem").filter({ hasText: "E2E Backend developer" })
  await expect(job.getByTestId("invited-count")).toHaveText("3")
  await expect(job.getByTestId("not-invited")).toContainText("2")
  // Invite again, under the candidates who weren't invited.
  await expect(job.getByTestId("not-invited").getByRole("button")).toBeVisible()
  await shot(owner, "workable-page")

  // A new interview from a Workable job starts from the job's own text, which can be edited.
  await owner.route("**/api/ats/workable/jobs?*", (route) =>
    route.fulfill({ json: [{ id: "J1", name: "Senior Accountant" }] })
  )
  await owner.route("**/api/ats/workable/jobs/J1/stages?*", (route) =>
    route.fulfill({ json: [{ id: "assessment", name: "Assessment" }] })
  )
  await owner.route("**/api/ats/workable/jobs/J1/text?*", (route) =>
    route.fulfill({ json: { text: "Senior Accountant\n\nOwn our monthly close." } })
  )
  await owner.getByTestId("link-job").click()
  const link = owner.getByRole("dialog")
  // The job's and the stage's pills, then the interview's picker.
  const pills = link.locator("form").getByRole("button")
  await pills.nth(0).click()
  await owner.getByRole("menuitemradio", { name: "Senior Accountant" }).click()
  await pills.nth(1).click()
  await owner.getByRole("menuitemradio", { name: "Assessment" }).click()
  // The interview: the newest ones, and any of the company's found by its title.
  const { title } = await api<{ title: string }>(owner, "GET", `/companies/interviews/${interviewId}`)
  const picker = link.locator("button[role=combobox]")
  const search = owner.locator("input[role=combobox]")
  const options = owner.getByRole("option")
  await picker.click()
  await shot(owner, "interview-picker")
  await search.fill(title.slice(0, 5))
  await expect(options.filter({ hasText: title })).toBeVisible()
  // Nothing found: only the first choice, a new interview from the job, stays.
  await search.fill("no interview has this e2e text")
  await expect(options).toHaveCount(1)
  await shot(owner, "interview-search")
  // A test chosen: the picker shows its title, closed.
  await search.fill(title.slice(0, 5))
  await options.filter({ hasText: title }).click()
  await expect(picker).toHaveText(title)
  await shot(owner, "interview-chosen")
  await picker.click()
  await search.fill("")
  await options.first().click()
  await expect(link.getByRole("textbox")).toHaveValue("Senior Accountant\n\nOwn our monthly close.")
  await shot(owner, "new-interview-from-job")
  await owner.keyboard.press("Escape")

  // Unlinking (the row's last button) asks first, then the job is gone. (The link dialog
  // finishes closing first.)
  await expect(owner.getByRole("dialog")).toHaveCount(0)
  await job.getByRole("button").last().click()
  await owner.getByRole("dialog").getByRole("button").last().click()
  await expect(job).toHaveCount(0)
})
