import { expect, test } from "../fixtures"
import { api, createCompany, createInterview, inviteCandidate } from "../helpers/api"
import { inviteToken } from "../helpers/db"
import { hoverFor, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, throwawayEmail } from "../helpers/users"

// The invite dialog's three tabs: one email with a name, a list with a name beside one email,
// and a file (its examples download; the welcome credits cover three candidates, so it isn't
// sent: the backend's tests read CSV name columns). The list shows each name under the
// email ("No name yet" without one), and search finds a candidate by name. The dialog's tabs, in
// order: one, many, upload.
test("owner invites candidates with names three ways and finds one by name", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const list = `/companies/${company.id}/interviews/${interviewId}?tab=candidates`
  const ann = throwawayEmail("ann")
  const bob = throwawayEmail("bob")
  const plain = throwawayEmail("plain")
  await visit(owner, list)
  const dialog = owner.getByRole("dialog")
  const tabs = dialog.getByRole("tab")
  const invite = dialog.locator("button[type=submit]")

  // Invite one: an email and its name.
  await owner.getByTestId("new-candidate").click()
  await tabs.nth(0).click()
  await dialog.getByRole("textbox").first().fill(ann)
  await dialog.getByRole("textbox").nth(1).fill("  Ann Lee ")
  await shot(owner, "invite-one")
  await invite.click()
  // The dialog closes once everyone was invited; the list then shows them (read afresh, as the
  // local dev server can be slow to refresh it).
  await expect(dialog).toBeHidden({ timeout: 60_000 })
  await visit(owner, list)
  await expect(owner.getByText("Ann Lee", { exact: true })).toBeVisible()

  // Invite many: a name beside one email, none beside the other.
  await visit(owner, list)
  await owner.getByTestId("new-candidate").click()
  await tabs.nth(1).click()
  await dialog.getByRole("textbox").fill(`Bob Stone <${bob}>\n${plain}`)
  await shot(owner, "invite-many")
  await invite.click()
  // The dialog closes once everyone was invited; the list then shows them (read afresh, as the
  // local dev server can be slow to refresh it).
  await expect(dialog).toBeHidden({ timeout: 60_000 })
  await visit(owner, list)
  await expect(owner.getByText("Bob Stone", { exact: true })).toBeVisible()
  const plainRow = owner.getByRole("link").filter({ hasText: plain })
  const noName = plainRow.getByTestId("no-name")
  await expect(noName).toBeVisible()
  // Its tooltip says when it's filled in, and that an owner can enter it (the tooltip has no
  // ARIA role).
  await hoverFor(owner, noName, owner.locator("[data-side][data-open][tabindex]"))
  await shot(owner, "no-name-tooltip")

  // Upload from file: the example files download, and a CSV with a name column invites.
  await visit(owner, list)
  await owner.getByTestId("new-candidate").click()
  await tabs.nth(2).click()

  for (const file of ["prepza-candidates-example.csv", "prepza-candidates-example.txt"]) {
    const download = owner.waitForEvent("download")
    await dialog.locator(`a[download][href$="/${file}"]`).click()
    expect((await download).suggestedFilename()).toBe(file)
  }

  // A file is read on Invite, like a pasted list (the list tab invites the same way).
  await owner.locator("input[type=file]").setInputFiles({
    name: "candidates.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(`email,name\n${throwawayEmail("cid")},Cid Moss\n`),
  })
  await expect(dialog.getByRole("button", { name: "candidates.csv" })).toBeVisible()
  await shot(owner, "invite-file")
  await owner.keyboard.press("Escape")
  await shot(owner, "candidates-with-names")

  // The dialog opens on the tab used last.
  await owner.getByTestId("new-candidate").click()
  await expect(tabs.nth(2)).toHaveAttribute(
    "aria-selected",
    "true"
  )
  await owner.keyboard.press("Escape")

  // Search matches part of a name, in any case.
  const search = owner.locator("main input[name=q]")
  await search.fill("stone")
  await search.press("Enter")
  await expect(owner).toHaveURL(/q=stone/)
  await expect(owner.getByText(bob, { exact: true })).toBeVisible()
  await expect(owner.getByText(ann, { exact: true })).toHaveCount(0)
  await shot(owner, "search-by-name")
})

// A candidate without a name gets the one their sign-in has when they start; an owner corrects
// it on the candidate's page, and starting again doesn't change it back.
test("the sign-in fills a name once and an owner's correction stays", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const email = throwawayEmail("named")
  await inviteCandidate(owner, interviewId, email)
  const list = `/companies/${company.id}/interviews/${interviewId}?tab=candidates`
  await visit(owner, list)
  await expect(owner.getByRole("link").filter({ hasText: email }).getByTestId("no-name")).toBeVisible()

  const candidate = await signInAs(email, {}, "Maria Kowalska")
  const start = `/companies/invites/${await inviteToken(email)}/start`
  await api(candidate, "POST", start, { pledged: true })

  await visit(owner, list)
  await owner.getByText("Maria Kowalska", { exact: true }).click()
  await expect(owner).toHaveURL(/\/candidates\/[^/?]+$/, { timeout: 90_000 })
  await expect(owner.getByRole("heading", { name: email })).toBeVisible()
  // The name's line under the email, with its pencil for an owner.
  const nameLine = owner.locator("main h1 + div > p")
  await expect(nameLine).toContainText("Maria Kowalska")
  await expect(nameLine.getByRole("button")).toBeVisible()
  await shot(owner, "report-name")

  await nameLine.getByRole("button").click()
  const field = owner.locator("main h1 + div input")
  await field.fill("Maria Nowak")
  await field.press("Enter")
  await expect(nameLine).toContainText("Maria Nowak")
  await shot(owner, "report-name-edited")

  // Starting again (reopening the invite) keeps the corrected name.
  await api(candidate, "POST", start, { pledged: true })
  await owner.reload()
  await expect(nameLine).toContainText("Maria Nowak")
  await expect(owner.getByText("Maria Kowalska")).toHaveCount(0)
})

// A list's problems are said in the dialog: a file that isn't a CSV or TXT file, one too large to
// send (not read at all), and each line nobody could be invited from, with why. Nobody is invited.
test("the invite dialog says what it couldn't read", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  await visit(owner, `/companies/${company.id}/interviews/${interviewId}?tab=candidates`)
  const dialog = owner.getByRole("dialog")
  const file = owner.locator("input[type=file]")

  const tabs = dialog.getByRole("tab")
  const invite = dialog.locator("button[type=submit]")
  await owner.getByTestId("new-candidate").click()
  await tabs.nth(2).click()
  await file.setInputFiles({
    name: "candidates.xlsx",
    mimeType: "application/octet-stream",
    buffer: Buffer.from(`email\n${throwawayEmail("xlsx")}\n`),
  })
  await invite.click()
  await expect(dialog.getByText("Only CSV or TXT files.")).toBeVisible()
  await shot(owner, "wrong-file-type")

  await file.setInputFiles({
    name: "big.csv",
    mimeType: "text/csv",
    buffer: Buffer.alloc(60_000, "a"),
  })
  await expect(dialog.getByText("The file is too large (max 50 KB).")).toBeVisible()
  await expect(invite).toBeDisabled()
  await shot(owner, "file-too-large")

  // A file's unusable rows are named under it (nobody is invited from them).
  await file.setInputFiles({
    name: "candidates.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("email,name\nJohn Smith,\nbob@example,Bob\n"),
  })
  await invite.click()
  await expect(dialog.getByText("No email found: John Smith,")).toBeVisible()
  await expect(dialog.getByText("Email isn't valid: bob@example,Bob")).toBeVisible()
  await shot(owner, "file-unusable-lines")

  // A list keeps only its unusable lines, each named once with its main reason.
  await tabs.nth(1).click()
  const list = ["John Smith", "bob@example", "Bob <bob@example", "Ann <ann@example.com"]
  await dialog.getByRole("textbox").fill(list.join("\n"))
  await invite.click()
  await expect(dialog.getByText("No email found: John Smith")).toBeVisible()
  await expect(dialog.getByText("Email isn't valid: bob@example", { exact: true })).toBeVisible()
  await expect(dialog.getByText("Email isn't valid: Bob <bob@example")).toBeVisible()
  await expect(
    dialog.getByText("Write the name as Name <email>: Ann <ann@example.com")
  ).toBeVisible()
  await expect(dialog.getByRole("textbox")).toHaveValue(list.join("\n"))
  await shot(owner, "unusable-lines")
})
