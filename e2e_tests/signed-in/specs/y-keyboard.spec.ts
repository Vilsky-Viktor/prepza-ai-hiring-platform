import { expect, test } from "../fixtures"
import { createCompany, createInterview } from "../helpers/api"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail } from "../helpers/users"

// Keyboard use: the first Tab offers to skip past the header to the page, and a dialog's tabs
// move with the arrow keys.
test("the keyboard skips the header and moves between tabs with the arrows", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  await visit(owner, `/companies/${company.id}/interviews/${interviewId}?tab=candidates`)

  // The skip link is the first Tab, even on a page whose tab row scrolled to its current tab;
  // hidden until then, it takes the focus past the header.
  const skip = owner.locator('a[href="#content"]')
  const invite = owner.getByTestId("new-candidate").filter({ visible: true })
  await expect(invite).toBeVisible()
  await owner.keyboard.press("Tab")
  await expect(skip).toBeFocused()
  await expect(skip).toBeVisible()
  await shot(owner, "skip-link")
  await owner.keyboard.press("Enter")
  await expect(owner.locator("#content")).toBeFocused()

  // The invite dialog's tabs: the arrows move between them, Home and End to the ends.
  await invite.click()
  const tabs = owner.getByRole("dialog").getByRole("tab")
  const first = tabs.first()
  await first.click()
  await owner.keyboard.press("ArrowRight")
  await expect(tabs.nth(1)).toBeFocused()
  await expect(tabs.nth(1)).toHaveAttribute("aria-selected", "true")
  await owner.keyboard.press("End")
  await expect(tabs.last()).toBeFocused()
  await owner.keyboard.press("Home")
  await expect(first).toHaveAttribute("aria-selected", "true")
  await shot(owner, "tabs-keyboard")
})
