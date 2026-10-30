import { expect, test } from "../fixtures"
import { EMAIL_BOXES, emailBoxes } from "../helpers/emails"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail } from "../helpers/users"

// Settings > Emails: one block per kind of email, each saved as it changes. The digest's own
// box turns its five kinds on or off at once, and shows a dash when only some are on.
test("a user chooses their emails in settings", async ({ signInAs }) => {
  const user = await signInAs(ownerEmail())
  await visit(user, "/settings")
  const boxes = emailBoxes(user)
  const digest = boxes.first()

  // A new user: the digest and reminders on, offers off; product updates on, as the first
  // sign-in left the opt-out unticked.
  await expect(boxes).toHaveCount(EMAIL_BOXES.count)
  await expect(digest).toBeChecked()

  for (const kind of EMAIL_BOXES.kinds) {
    await expect(boxes.nth(kind)).toBeChecked()
  }

  await expect(boxes.nth(EMAIL_BOXES.reminders)).toBeChecked()
  await expect(boxes.nth(EMAIL_BOXES.updates)).toBeChecked()
  await expect(boxes.nth(EMAIL_BOXES.offers)).not.toBeChecked()
  await shot(user, "emails")

  // One kind off: kept after a reload, and the digest shows a dash.
  await boxes.nth(EMAIL_BOXES.undelivered).click()
  await expect(boxes.nth(EMAIL_BOXES.undelivered)).not.toBeChecked()
  await expect(digest).toHaveAttribute("data-indeterminate", "")
  await user.reload()
  await expect(boxes.nth(EMAIL_BOXES.undelivered)).not.toBeChecked()
  await expect(digest).toHaveAttribute("data-indeterminate", "")
  await shot(user, "some-kinds")

  // The team's notes have their own kind, saved like the others.
  await boxes.nth(EMAIL_BOXES.notes).click()
  await expect(boxes.nth(EMAIL_BOXES.notes)).not.toBeChecked()
  await user.reload()
  await expect(boxes.nth(EMAIL_BOXES.notes)).not.toBeChecked()

  // The digest's box turns all five on, then all off.
  await digest.click()

  for (const kind of EMAIL_BOXES.kinds) {
    await expect(boxes.nth(kind)).toBeChecked()
  }

  await digest.click()

  for (const kind of EMAIL_BOXES.kinds) {
    await expect(boxes.nth(kind)).not.toBeChecked()
  }

  await expect(digest).not.toBeChecked()
  await user.reload()
  await expect(boxes.nth(EMAIL_BOXES.ready)).not.toBeChecked()
  await user.setViewportSize({ width: 390, height: 844 })
  await shot(user, "emails-phone")
})

// The sign-in's boxes: an unticked opt-out turns product updates on at a first sign-in only;
// offers go on only when ticked; a later sign-in never turns updates back on. The boxes are
// ticked on the site's own sign-in; the other sign-ins send what the site sends with them
// unticked (helpers/sign-in.ts, lib/emails.ts's signInEmailChanges).
test("signing in sets product updates and offers", async ({ signInAs }) => {
  const ticked = await signInAs(ownerEmail(), { noUpdates: true, promotions: true, ui: true })
  await visit(ticked, "/settings")
  await expect(emailBoxes(ticked).nth(EMAIL_BOXES.updates)).not.toBeChecked()
  await expect(emailBoxes(ticked).nth(EMAIL_BOXES.offers)).toBeChecked()

  const email = ownerEmail()
  const first = await signInAs(email)
  await visit(first, "/settings")
  const updates = emailBoxes(first).nth(EMAIL_BOXES.updates)
  await expect(updates).toBeChecked()
  await expect(emailBoxes(first).nth(EMAIL_BOXES.offers)).not.toBeChecked()
  await updates.click()
  await expect(updates).not.toBeChecked()
  // Saved before signing in again.
  await first.reload()
  await expect(updates).not.toBeChecked()

  const again = await signInAs(email)
  await visit(again, "/settings")
  await expect(emailBoxes(again).nth(EMAIL_BOXES.updates)).not.toBeChecked()
})
