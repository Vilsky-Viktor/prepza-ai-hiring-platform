import { expect, test } from "../fixtures"
import { box } from "../helpers/layout"
import { visit } from "../helpers/navigation"
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
