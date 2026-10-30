import type { Locator, Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, createInterview } from "../helpers/api"
import { createKey, deleteKey, keyNote } from "../helpers/api-keys"
import { box, PHONE } from "../helpers/layout"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, randomId } from "../helpers/users"

// An interview's notes tab: every member writes notes (with the button or ⌘/Ctrl + Enter), the
// author edits their own, the author, the owner and admins delete, and the owner and admins pin
// one, which then shows under the interview's title and in the interviews list. The menu counts
// the notes.

// A note's actions, by their icons: pin (or unpin), edit, delete.
const PIN = "button:has(svg.lucide-bookmark)"
const UNPIN = "button:has(svg.lucide-bookmark-x)"
const EDIT = "button:has(svg.lucide-pencil)"
const DELETE = "button:has(svg.lucide-trash-2)"

/** The notes tab's address. */
function notesTab(companyId: string, interviewId: string) {
  return `/companies/${companyId}/interviews/${interviewId}?tab=notes`
}

/** The page menu shown (the other, for the other screen size, is hidden). */
function menu(page: Page) {
  return page.getByRole("main").getByRole("navigation").first()
}

/** The count beside the interview menu's page `href` ends with (nothing at 0). */
function countOf(page: Page, href: string) {
  return menu(page).locator(`a[href$="${href}"]`).getByTestId("menu-count")
}

/** The notes, in the list's order (the visible ones: the page may hold a hidden copy). */
function notes(page: Page) {
  return page.getByTestId("note").filter({ visible: true })
}

/** The box that writes a new note: the tab's first form. */
function newNote(page: Page) {
  return page.getByRole("main").locator("form").filter({ visible: true }).first()
}

/** Writes `text` in the new note's box and posts it with its button. */
async function post(page: Page, text: string) {
  const form = newNote(page)
  await form.getByRole("textbox").fill(text)
  await form.locator('button[type="submit"]').click()
  await expect(notes(page).getByTestId("note-text").filter({ hasText: text })).toBeVisible()
}

/** The note whose text holds `text`. */
function note(page: Page, text: string): Locator {
  return notes(page).filter({ has: page.getByTestId("note-text").filter({ hasText: text }) })
}

test("the team writes, edits, pins and deletes an interview's notes", async ({ signInAs }) => {
  test.setTimeout(180_000)
  const name = `E2E Anna ${randomId()}`
  const owner = await signInAs(ownerEmail(), undefined, name)
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const { topics } = await api<{ topics: unknown[] }>(
    owner,
    "GET",
    `/companies/interviews/${interviewId}`
  )

  // The menu counts the topics; no candidates and no notes yet, so no count beside them.
  await visit(owner, notesTab(company.id, interviewId))
  await expect(owner.getByTestId("no-notes").filter({ visible: true })).toBeVisible()
  await expect(countOf(owner, `/interviews/${interviewId}`)).toHaveText(String(topics.length))
  await expect(countOf(owner, "?tab=candidates")).toHaveCount(0)
  await expect(countOf(owner, "?tab=notes")).toHaveCount(0)
  await expect(newNote(owner).getByTestId("submit-hint")).toBeVisible()

  // Posted with the button: the author's name, the text with its address as a link (without
  // the sentence's full stop), the box empty again and the menu counting it.
  const first = `Strong on SQL, see https://example.com/cv-${randomId()}.`
  await post(owner, first)
  const link = first.slice(first.indexOf("https://"), -1)
  await expect(note(owner, first).getByTestId("note-author")).toHaveText(name)
  await expect(note(owner, first).getByRole("link")).toHaveAttribute("href", link)
  await expect(newNote(owner).getByRole("textbox")).toHaveValue("")
  await expect(countOf(owner, "?tab=notes")).toHaveText("1")

  // Posted with ⌘/Ctrl + Enter: the newest first.
  const second = `Ask about indexes ${randomId()}`
  await newNote(owner).getByRole("textbox").fill(second)
  await newNote(owner).getByRole("textbox").press("ControlOrMeta+Enter")
  await expect(notes(owner)).toHaveCount(2)
  await expect(notes(owner).first().getByTestId("note-text")).toHaveText(second)
  await expect(countOf(owner, "?tab=notes")).toHaveText("2")
  await expect(notes(owner).getByTestId("note-edited")).toHaveCount(0)
  await shot(owner, "notes")

  // Editing: the box takes the focus with the cursor at the note's end; ⌘/Ctrl + Enter saves,
  // and the note is marked edited.
  await note(owner, second).locator(EDIT).click()
  const editBox = notes(owner).first().locator("textarea")
  await expect(editBox).toBeFocused()
  expect(
    await editBox.evaluate(
      (box: HTMLTextAreaElement) =>
        box.selectionStart === box.value.length && box.selectionEnd === box.value.length
    )
  ).toBe(true)
  await shot(owner, "note-editing")
  await owner.keyboard.type(" and joins")
  await editBox.press("ControlOrMeta+Enter")
  const edited = `${second} and joins`
  await expect(notes(owner).first().getByTestId("note-text")).toHaveText(edited)
  await expect(notes(owner).first().getByTestId("note-edited")).toBeVisible()

  // Escape leaves the note as it was.
  await note(owner, edited).locator(EDIT).click()
  await owner.keyboard.type(" (draft)")
  await owner.keyboard.press("Escape")
  await expect(notes(owner).first().locator("textarea")).toHaveCount(0)
  await expect(notes(owner).first().getByTestId("note-text")).toHaveText(edited)

  // Pinning the older note: it goes first, shows under the title and in the interviews list.
  await note(owner, first).locator(PIN).click()
  await expect(note(owner, first)).toHaveAttribute("data-pinned", "true")
  await owner.reload()
  await expect(notes(owner).first()).toHaveAttribute("data-pinned", "true")
  await expect(notes(owner).first().getByTestId("note-text")).toHaveText(first)
  const pinnedLine = owner.getByTestId("pinned-note").filter({ visible: true })
  await expect(pinnedLine).toHaveText(first)
  await shot(owner, "note-pinned")

  // One pinned at a time: pinning the other unpins the first.
  await note(owner, edited).locator(PIN).click()
  await expect(note(owner, edited)).toHaveAttribute("data-pinned", "true")
  await expect(owner.locator("[data-testid=note][data-pinned]")).toHaveCount(1)
  await expect(pinnedLine).toHaveText(edited)
  await visit(owner, `/companies/${company.id}/interviews`)
  await expect(owner.getByTestId("pinned-note").filter({ visible: true })).toHaveText(edited)
  await shot(owner, "interviews-pinned")

  // Unpinned, no line under the title.
  await visit(owner, notesTab(company.id, interviewId))
  await note(owner, edited).locator(UNPIN).click()
  await expect(owner.locator("[data-testid=note][data-pinned]")).toHaveCount(0)
  await expect(pinnedLine).toHaveCount(0)

  // Deleting asks first (the dialog's last button deletes); the menu counts one again.
  await note(owner, first).locator(DELETE).click()
  await owner.getByRole("dialog").getByRole("button").last().click()
  await expect(notes(owner)).toHaveCount(1)
  await expect(countOf(owner, "?tab=notes")).toHaveText("1")
  await owner.reload()
  await expect(notes(owner)).toHaveCount(1)
  await expect(notes(owner).first().getByTestId("note-text")).toHaveText(edited)
})

// A viewer writes notes and edits or deletes only their own; they pin none. The owner deletes
// and pins the viewer's note but doesn't edit it.
test("a viewer writes notes but pins none", async ({ signInAs }) => {
  test.setTimeout(180_000)
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const ownerText = `Owner's note ${randomId()}`
  await api(owner, "POST", `/companies/interviews/${interviewId}/notes`, { text: ownerText })
  const viewerAddress = ownerEmail()
  const invited = await api<{ token: string }>(
    owner,
    "POST",
    `/companies/members?company_id=${company.id}`,
    { email: viewerAddress, role: "viewer" }
  )
  const viewer = await signInAs(viewerAddress)
  await api(viewer, "POST", `/companies/members/invites/${invited.token}/accept`)

  await visit(viewer, notesTab(company.id, interviewId))
  await expect(note(viewer, ownerText)).toBeVisible()
  await expect(note(viewer, ownerText).getByRole("button")).toHaveCount(0)
  const viewerText = `Viewer's note ${randomId()}`
  await post(viewer, viewerText)
  const own = note(viewer, viewerText)
  await expect(own.locator(EDIT)).toHaveCount(1)
  await expect(own.locator(DELETE)).toHaveCount(1)
  await expect(own.locator(PIN)).toHaveCount(0)
  await shot(viewer, "viewer-notes")

  await visit(owner, notesTab(company.id, interviewId))
  const theirs = note(owner, viewerText)
  await expect(theirs.locator(PIN)).toHaveCount(1)
  await expect(theirs.locator(DELETE)).toHaveCount(1)
  await expect(theirs.locator(EDIT)).toHaveCount(0)
})

// A note an API key wrote names the key with a key for its avatar; once the key is deleted, its
// note still has the key for its avatar and names neither the key nor the member who made it.
test("a note written by an API key names the key", async ({ signInAs }) => {
  const ownerName = `E2E Anna ${randomId()}`
  const owner = await signInAs(ownerEmail(), undefined, ownerName)
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const permissions = ["notes:add"]
  const live = `Careers site ${randomId()}`
  const gone = `Old agent ${randomId()}`
  const { key } = await createKey(owner, company.id, live, permissions)
  const old = await createKey(owner, company.id, gone, permissions)
  const liveText = `From the careers site ${randomId()}`
  const goneText = `From a key deleted later ${randomId()}`
  await keyNote(owner, key, interviewId, liveText)
  await keyNote(owner, old.key, interviewId, goneText)
  await deleteKey(owner, company.id, old.id)

  await visit(owner, notesTab(company.id, interviewId))
  const keyIcon = "[data-slot=avatar] svg.lucide-key-round"
  await expect(note(owner, liveText).getByTestId("note-author")).toHaveText(live)
  await expect(note(owner, liveText).locator(keyIcon)).toHaveCount(1)
  const deleted = note(owner, goneText)
  await expect(deleted.locator(keyIcon)).toHaveCount(1)
  await expect(deleted.getByTestId("note-author")).not.toBeEmpty()
  await expect(deleted.getByTestId("note-author")).not.toHaveText(gone)
  await expect(deleted.getByTestId("note-author")).not.toHaveText(ownerName)
  await shot(owner, "key-notes")
})

// On a phone the menu shows two tabs, the open notes tab from under "…" in the second place;
// a note's actions take a centred line of their own under its text.
test("the notes tab on a phone", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const text = `A note on a phone ${randomId()}`
  await api(owner, "POST", `/companies/interviews/${interviewId}/notes`, { text })
  await owner.setViewportSize(PHONE)

  await visit(owner, notesTab(company.id, interviewId))
  const tabs = menu(owner).getByRole("link")
  await expect(tabs).toHaveCount(2)
  await expect(tabs.last()).toHaveAttribute("href", /\?tab=notes$/)
  await expect(tabs.last()).toHaveAttribute("aria-current", "page")
  await expect(menu(owner).getByRole("button")).toHaveCount(1)

  const row = note(owner, text)
  const actions = row.getByRole("button")
  await expect(actions).toHaveCount(3)
  const textBox = await box(row.getByTestId("note-text"))
  const first = await box(actions.first())
  const last = await box(actions.last())
  const whole = await box(row)
  expect(first.top).toBeGreaterThan(textBox.bottom)
  expect(last.top).toBe(first.top)
  // Centred in the row: as much room on either side.
  expect(Math.abs(first.left - whole.left - (whole.right - last.right))).toBeLessThanOrEqual(2)
  await shot(owner, "notes-phone")
})
