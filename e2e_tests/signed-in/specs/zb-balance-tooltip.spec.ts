import { expect, test } from "../fixtures"
import { createCompany } from "../helpers/api"
import { hoverFor, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail } from "../helpers/users"

// A balance shows short ("1.5K"); hovering it shows the whole amount (the welcome credits).
test("a balance shows its whole amount on hover", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const tooltip = owner.getByTestId("balance-tooltip")

  // In the company's header.
  await visit(owner, `/companies/${company.id}/interviews`)
  await hoverFor(owner, owner.locator("span.tabular-nums").first(), tooltip)
  await expect(tooltip).toContainText("1,500")
  await shot(owner, "header")

  // On the billing page.
  await visit(owner, `/companies/${company.id}/billing`)
  await hoverFor(owner, owner.locator("span.font-heading.tabular-nums").first(), tooltip)
  await expect(tooltip).toContainText("1,500")
  await shot(owner, "billing")
})
