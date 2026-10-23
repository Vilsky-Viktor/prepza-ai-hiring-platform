import type { Locator } from "@playwright/test"

import { expect, test } from "../fixtures"
import { createCompany, createInterview } from "../helpers/api"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { setScheme } from "../helpers/theme"
import { ownerEmail } from "../helpers/users"

function colors(stat: Locator) {
  return stat.evaluate((element) => {
    const style = getComputedStyle(element)

    return `${style.backgroundColor} ${style.color}`
  })
}

// A stat icon (an interview's candidate count) isn't a button, but hovered it reacts like one: its
// background and colour change, light and dark; it stays out of the tab order.
test("a stat icon reacts on hover like an icon button", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  await createInterview(owner, company.id)

  for (const scheme of ["light", "dark"] as const) {
    await setScheme(owner, scheme)
    await visit(owner, `/companies/${company.id}/interviews`)
    const stat = owner.getByRole("main").getByTestId("candidate-count")
    await expect(stat).toHaveText("0")
    await expect(stat).not.toHaveAttribute("tabindex", /.*/)
    await owner.mouse.move(0, 0)
    const idle = await colors(stat)

    await stat.hover()
    await expect.poll(() => colors(stat)).not.toBe(idle)
    await shot(owner, `hover-${scheme}`)
  }
})
