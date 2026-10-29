import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, createInterview } from "../helpers/api"
import { deleteNotice, isSuppressed, sentDpaNotice, suppress } from "../helpers/db-notifications"
import { env } from "../helpers/env"
import { deleteMails, mailHtml, mails } from "../helpers/mailpit"
import { openDialog, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { uidOf } from "../helpers/sign-in"
import { supportId, supportSearch } from "../helpers/support"
import { ownerEmail, randomId, throwawayEmail } from "../helpers/users"

type Campaign = { id: string; kind: string; subject: string; status: string }
type Notice = { document: string; version: string }

const PATH = "/notifications/superadmin/campaigns"
const LINK = "https://prepza.ai/pricing"

/** Deletes the drafts a run left whose subject starts with `subject`. */
async function deleteDrafts(page: Page, subject: string) {
  const rows = await api<Campaign[]>(page, "GET", `${PATH}?offset=0&limit=100`)

  for (const row of rows.filter((one) => one.subject.startsWith(subject))) {
    await api(page, "DELETE", `${PATH}/${row.id}`).catch(() => {})
  }
}

// A superadmin writes a product update with the editor (bold words and a link), sees it as users
// will get it, sends a test to their own address (the local Mailpit, never a real inbox), turns
// it into an offer and deletes the draft. Nothing is sent to users.
test("superadmin writes, previews, tests, edits and deletes a campaign", async ({
  signInSuperadmin,
}) => {
  const superadmin = await signInSuperadmin()
  const address = env("SUPERADMIN_EMAILS").split(",")[0].trim().toLowerCase()
  const subject = `E2E campaign ${randomId()}`

  try {
    await visit(superadmin, "/superadmin/campaigns")
    await openDialog(superadmin, superadmin.getByTestId("new-campaign"))
    const dialog = superadmin.getByRole("dialog")
    await dialog.getByRole("textbox").first().fill(subject)

    // Bold words (the editor's shortcut), then a link from the toolbar's third toggle (bold,
    // italic, link): without words selected, the link shows its address.
    const editor = dialog.locator("[contenteditable=true]")
    await editor.click()
    // The shortcut reaches the editor only once it has the focus.
    await expect(editor).toBeFocused()
    // Bold on: its toggle (the toolbar's first) says so before the words are typed.
    const bold = dialog.locator("button[aria-pressed]").first()
    await expect(async () => {
      if ((await bold.getAttribute("aria-pressed")) !== "true") {
        await superadmin.keyboard.press("ControlOrMeta+b")
      }

      await expect(bold).toHaveAttribute("aria-pressed", "true", { timeout: 2_000 })
    }).toPass()
    await superadmin.keyboard.type("Bold words")
    await superadmin.keyboard.press("ControlOrMeta+b")
    await superadmin.keyboard.type(" and ")
    await dialog.locator("button[aria-pressed]").nth(2).click()
    await dialog.locator("input[type=url]").fill(LINK)
    await dialog.locator("input[type=url]").press("Enter")
    await expect(editor.locator("strong")).toHaveText("Bold words")
    await expect(editor.locator(`a[href="${LINK}"]`)).toHaveText(LINK)
    await shot(superadmin, "campaign-dialog")
    await dialog.locator("button[type=submit]").click()

    // The dev server may compile the campaign's page first.
    await expect(superadmin).toHaveURL(/\/superadmin\/campaigns\/[0-9a-f-]{36}$/, {
      timeout: 90_000,
    })
    const id = superadmin.url().split("/").pop() ?? ""
    const saved = await api<Campaign & { texts: { en: { text: string } } }>(
      superadmin,
      "GET",
      `${PATH}/${id}`
    )
    expect(saved.texts.en.text).toBe(`**Bold words** and [${LINK}](${LINK})`)

    // The preview is the email itself: the words in bold, the link a link.
    const preview = superadmin.frameLocator("main iframe")
    await expect(preview.locator("strong")).toHaveText("Bold words")
    await expect(preview.locator(`a[href="${LINK}"]`)).toHaveText(LINK)
    // Before sending, who'd get it, as the API counts them.
    const { count } = await api<{ count: number }>(superadmin, "GET", `${PATH}/${id}/recipients`)
    await expect(superadmin.getByTestId("campaign-recipients")).toContainText(
      new Intl.NumberFormat("en", { notation: "compact" }).format(count)
    )
    await shot(superadmin, "campaign-draft")

    // The test reaches the superadmin's own address, formatted as previewed.
    await superadmin.getByTestId("send-test").click()
    await expect(superadmin.locator('[data-sonner-toast][data-type="success"]')).toBeVisible()
    await expect.poll(async () => (await mails(superadmin.request, address, subject)).length).toBe(1)
    const [mail] = await mails(superadmin.request, address, subject)
    const html = await mailHtml(superadmin.request, mail.ID)
    await deleteMails(superadmin.request, [mail])
    expect(html).toMatch(/<strong[^>]*>Bold words<\/strong>/)
    expect(html).toContain(`href="${LINK}"`)

    // Made an offer instead: the kind's menu's second choice.
    await openDialog(superadmin, superadmin.getByTestId("edit-campaign").filter({ visible: true }))
    await dialog.getByRole("button").first().click()
    await superadmin.getByRole("menu").getByRole("menuitemradio").nth(1).click()
    await dialog.locator("button[type=submit]").click()
    await expect(dialog).toBeHidden()
    await expect
      .poll(async () => (await api<Campaign>(superadmin, "GET", `${PATH}/${id}`)).kind)
      .toBe("promotions")

    // Deleted from its page: back on the list, without it.
    await superadmin.getByTestId("delete-campaign").filter({ visible: true }).click()
    const confirm = superadmin.getByRole("dialog")
    await confirm.getByRole("button").last().click()
    await expect(superadmin).toHaveURL(/\/superadmin\/campaigns$/)
    await expect(superadmin.locator(`a[href="/superadmin/campaigns/${id}"]`)).toHaveCount(0)
  } finally {
    await deleteDrafts(superadmin, subject)
  }
})

// An address that bounced: its account's support page says so, with the day, and the superadmin
// takes it off the suppression list, so product emails and notices reach it again.
test("superadmin sees a suppressed address and takes it off the list", async ({
  signInAs,
  signInSuperadmin,
}) => {
  const address = throwawayEmail("bounced")
  const person = await signInAs(address)
  await person.context().close()

  try {
    await suppress(address)
    const superadmin = await signInSuperadmin()
    const found = await supportSearch(superadmin, address)
    const userId = await supportId(found.first())
    await visit(superadmin, `/superadmin/support/users/${userId}`)

    const remove = superadmin.getByTestId("remove-suppression")
    await expect(remove).toBeVisible()
    const today = new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date())
    await expect(superadmin.getByRole("main")).toContainText(today)
    await shot(superadmin, "suppressed")

    await remove.click()
    await expect(remove).toHaveCount(0)
    await expect.poll(() => isSuppressed(address)).toBe(false)
  } finally {
    await isSuppressed(address, true)
  }
})

// A candidate's address that bounced: their support page warns too, and the superadmin takes it
// off the list. Each other reason shows as a warning on an account's page.
test("superadmin sees a suppressed candidate address and takes it off the list", async ({
  signInAs,
  signInSuperadmin,
}) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const candidate = throwawayEmail("bounced-candidate")
  const invited = await api<{ id: string }>(
    owner,
    "POST",
    `/companies/interviews/${interviewId}/candidates`,
    { email: candidate }
  )
  const others = ["suppressed", "soft_bounced", "complained"].map((reason) => ({
    reason,
    address: throwawayEmail(`suppressed-${reason}`),
  }))

  try {
    await suppress(candidate)
    const superadmin = await signInSuperadmin()
    await visit(superadmin, `/superadmin/support/candidates/${invited.id}`)

    const remove = superadmin.getByTestId("remove-suppression")
    await expect(remove).toBeVisible()
    await shot(superadmin, "candidate-suppressed")
    await remove.click()
    await expect(remove).toHaveCount(0)
    await expect.poll(() => isSuppressed(candidate)).toBe(false)

    for (const { reason, address } of others) {
      const person = await signInAs(address)
      await person.context().close()
      await suppress(address, reason)
      const userId = await supportId((await supportSearch(superadmin, address)).first())
      await visit(superadmin, `/superadmin/support/users/${userId}`)
      await expect(superadmin.getByTestId("remove-suppression").filter({ visible: true })).toBeVisible()
      await shot(superadmin, `account-${reason}`)
    }
  } finally {
    await isSuppressed(candidate, true)

    for (const { address } of others) {
      await isSuppressed(address, true)
    }
  }
})

// A legal document's new version announced and not in force yet: a thin banner tells the user
// from when, links to it, and stays closed once closed. The DPA's notice concerns only the
// users it was sent to: here, one throwaway user, and no email goes out.
test("the legal banner shows a pending change until it's closed", async ({
  signInAs,
  signInSuperadmin,
}) => {
  const superadmin = await signInSuperadmin()
  const notices = await api<Notice[]>(superadmin, "GET", "/notifications/superadmin/legal-notices")
  const today = new Date().toISOString().slice(0, 10)
  const dpa = notices.find((notice) => notice.document === "dpa" && notice.version > today)
  test.skip(!dpa, "The DPA's current version is in force: no change to announce")

  const user = await signInAs(throwawayEmail("legal"))
  const noticeId = await sentDpaNotice(dpa!.version, await uidOf(user))
  test.skip(!noticeId, "A notice of this DPA version exists already: left as it is")

  try {
    await visit(user, "/companies")
    const banner = user.getByTestId("legal-banner")
    await expect(banner.locator('a[href="/dpa"]')).toBeVisible()
    await expect(banner).toContainText(
      new Intl.DateTimeFormat("en", { dateStyle: "medium", timeZone: "UTC" }).format(
        new Date(dpa!.version)
      )
    )
    await shot(user, "legal-banner")

    await banner.getByRole("button").click()
    await expect(banner).toHaveCount(0)
    // Still closed once the page has asked again.
    const asked = user.waitForResponse((response) => response.url().includes("/legal-changes"))
    await user.reload()
    await asked
    await expect(user.getByTestId("legal-banner")).toHaveCount(0)
  } finally {
    await deleteNotice(noticeId!)
  }
})
