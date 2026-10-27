import { expect, test } from "../fixtures"
import { box } from "../helpers/layout"
import { openDialog, visit } from "../helpers/navigation"
import { throwawayEmail } from "../helpers/users"

// On a wide screen a page's back arrow sits in the page margin before its title, level with
// it, with a clear gap between the two (the companies list's, for one).
test("the back arrow sits before the title with a gap", async ({ signInAs }) => {
  test.setTimeout(120_000)
  const user = await signInAs(throwawayEmail("back-link"))
  await user.setViewportSize({ width: 1440, height: 900 })
  await visit(user, "/companies")

  const arrow = await box(user.getByTestId("back-link").getByRole("link"))
  const title = await box(user.getByRole("main").getByRole("heading", { level: 1 }))

  // Before the title, not touching it.
  expect(arrow.right).toBeLessThanOrEqual(title.left - 12)
  // Level with it: the arrow's middle within the title's height.
  const middle = arrow.top + arrow.height / 2
  expect(middle).toBeGreaterThanOrEqual(title.top)
  expect(middle).toBeLessThanOrEqual(title.top + title.height)
})

// At 1280px the page's margin can't hold them: the back arrow and the info button sit on the
// screen above the title, never past its edge, and both work.
test("the back arrow and info button stay on screen at 1280px", async ({ signInAs }) => {
  test.setTimeout(120_000)
  const user = await signInAs(throwawayEmail("back-link-1280"))
  await user.setViewportSize({ width: 1280, height: 800 })
  await visit(user, "/companies")
  const back = user.getByTestId("back-link")
  const width = user.viewportSize()!.width

  for (const control of [back.getByRole("link"), back.getByTestId("page-help")]) {
    const { left, right } = await box(control)
    expect(left).toBeGreaterThanOrEqual(0)
    expect(right).toBeLessThanOrEqual(width)
  }

  await openDialog(user, back.getByTestId("page-help"))
  await user.keyboard.press("Escape")
  await back.getByRole("link").click()
  await expect(user).toHaveURL(/\/$/)
})
