import { type Locator } from "@playwright/test"

import { expect, test } from "../fixtures"
import { createCompany, createInterview } from "../helpers/api"
import { box, settled } from "../helpers/layout"
import { visit } from "../helpers/navigation"
import { ownerEmail } from "../helpers/users"

/** Where a field's label stands: "up" on the box's top edge, or "rest" inside it. `field` is the
 * input, the label's box the input's parent. */
async function labelPlace(field: Locator, label: Locator) {
  const area = field.locator("..")
  await settled(area)
  const [outer, name] = [await box(area), await box(label)]
  const middle = (name.top + name.bottom) / 2

  return Math.abs(middle - outer.top) <= 4 ? "up" : "rest"
}

/** The <label> that names `field`, found by its `for`. */
async function labelOf(field: Locator) {
  const id = await field.getAttribute("id")

  return field.page().locator(`label[for="${id}"]`)
}

// The site's fields carry their name inside: it is the field's accessible name, it rests where
// the value goes while the field is empty and rises onto the box's top edge once the field is
// focused or has a value (a select once something is chosen, a date field always), and a click
// anywhere in the box focuses the field.
test("a field's name rests inside it and rises onto its edge when focused or filled", async ({
  signInAs,
}) => {
  // Three pages on the dev server, each compiled on first visit.
  test.setTimeout(480_000)
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)

  // The invite dialog's email and name fields.
  await visit(owner, `/companies/${company.id}/interviews/${interviewId}?tab=candidates`)
  await owner.getByTestId("new-candidate").filter({ visible: true }).click()
  const dialog = owner.getByRole("dialog")
  await dialog.getByRole("tab").first().click()
  const email = dialog.locator('input[type="email"]')
  const name = dialog.getByRole("textbox").nth(1)
  const emailLabel = await labelOf(email)
  const nameLabel = await labelOf(name)

  // Each label names its field.
  for (const [field, label] of [
    [email, emailLabel],
    [name, nameLabel],
  ] as const) {
    const text = (await label.textContent())!.trim()
    expect(text).not.toBe("")
    await expect(dialog.getByRole("textbox", { name: text, exact: true })).toHaveAttribute(
      "id",
      (await field.getAttribute("id"))!
    )
  }

  // Empty and not focused: inside. A click at the box's far end focuses the field.
  await dialog.getByRole("tab").first().focus()
  await expect.poll(() => labelPlace(name, nameLabel)).toBe("rest")
  const area = await box(name.locator(".."))
  await owner.mouse.click(area.right - 30, (area.top + area.bottom) / 2)
  await expect(name).toBeFocused()
  await expect.poll(() => labelPlace(name, nameLabel)).toBe("up")

  // Filled and left: still up. Emptied and left: back inside.
  await email.fill("ann@example.com")
  await name.focus()
  await expect.poll(() => labelPlace(email, emailLabel)).toBe("up")
  await expect.poll(() => labelPlace(name, nameLabel)).toBe("up")
  await email.fill("")
  await name.fill("Ann")
  await expect.poll(() => labelPlace(email, emailLabel)).toBe("rest")
  await expect.poll(() => labelPlace(name, nameLabel)).toBe("up")
  await owner.keyboard.press("Escape")

  // The action log's filters: two selects with a choice made and two date fields, which show
  // their "dd/mm/yyyy" while empty: all four labels are up.
  await visit(owner, `/companies/${company.id}/actions`)
  const filters = owner.getByTestId("action-filters")

  for (const nth of [0, 1]) {
    const pill = filters.getByRole("button").nth(nth)
    const pillLabel = owner.locator(`[id="${(await pill.getAttribute("aria-labelledby"))!.split(" ")[0]}"]`)
    await expect
      .poll(async () => {
        const [outer, label] = [await box(pill), await box(pillLabel)]

        return Math.abs((label.top + label.bottom) / 2 - outer.top)
      })
      .toBeLessThanOrEqual(4)
  }

  for (const day of await filters.locator('input[type="date"]').all()) {
    const dayLabel = await labelOf(day)
    await expect.poll(() => labelPlace(day, dayLabel)).toBe("up")
  }
})
