import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, createInterview } from "../helpers/api"
import { PHONE } from "../helpers/layout"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { throwawayEmail } from "../helpers/users"

test.setTimeout(240_000)

/** A company with 21 interviews "Backend 01" to "Backend 21" (oldest first, so "Backend 01" is
 * on a search's second page of 20) and, newest, one "Designer". */
async function interviewsToSearch(owner: Page) {
  const company = await createCompany(owner)
  const titles = [
    ...Array.from({ length: 21 }, (_, index) => `Backend ${String(index + 1).padStart(2, "0")}`),
    "Designer",
  ]

  for (const title of titles) {
    const id = await createInterview(owner, company.id)
    await api(owner, "PATCH", `/companies/interviews/${id}/title`, { title })
  }

  return company
}

function searchField(page: Page) {
  return page.getByRole("main").locator("form").getByRole("textbox")
}

test("the interviews list is searched by title, in the address and across pages", async ({
  signInAs,
}) => {
  const owner = await signInAs(throwawayEmail("interviews-search"))
  const company = await interviewsToSearch(owner)
  const list = `/companies/${company.id}/interviews`

  await visit(owner, list)
  await expect(owner.getByText("Designer", { exact: true }).filter({ visible: true })).toBeVisible()

  // Any case finds the titles containing it; the address keeps the search.
  await searchField(owner).fill("BACKEND")
  await searchField(owner).press("Enter")
  await expect(owner).toHaveURL(/[?&]q=BACKEND/)
  // The visible rows: while the list renders again, Next.js can keep a hidden copy of it.
  await expect(owner.getByText("Backend 21", { exact: true }).filter({ visible: true })).toBeVisible()
  await expect(owner.getByText("Designer", { exact: true }).filter({ visible: true })).toHaveCount(0)
  await shot(owner, "desktop-searched")

  // The next page is asked for with the same search (listened for from the reload on: a tall
  // window can ask for it as soon as the list shows), and brings the last match.
  const nextPage = owner.waitForRequest(
    (request) =>
      request.url().includes("/companies/interviews?") && request.url().includes("offset=20")
  )

  // A reload keeps it.
  await owner.reload()
  await expect(searchField(owner)).toHaveValue("BACKEND")
  await expect(owner.getByText("Backend 21", { exact: true }).filter({ visible: true })).toBeVisible()
  await expect(owner.getByText("Designer", { exact: true }).filter({ visible: true })).toHaveCount(0)

  await expect(async () => {
    await owner.mouse.wheel(0, 4000)
    await expect(
      owner.getByText("Backend 01", { exact: true }).filter({ visible: true })
    ).toBeVisible({ timeout: 1000 })
  }).toPass({ timeout: 30_000 })
  expect(new URL((await nextPage).url()).searchParams.get("q")).toBe("BACKEND")
  await expect(owner.getByText("Designer", { exact: true }).filter({ visible: true })).toHaveCount(0)

  // Nothing matching: the no-matches state, not the "no interviews yet" one.
  await visit(owner, `${list}?q=${encodeURIComponent("50%_off")}`)
  await expect(owner.getByTestId("no-matches").filter({ visible: true })).toBeVisible()
  await expect(owner.getByTestId("no-interviews")).toHaveCount(0)
  await expect(owner.getByText("Backend 21", { exact: true }).filter({ visible: true })).toHaveCount(0)
  await shot(owner, "desktop-no-matches")

  await owner.setViewportSize(PHONE)
  await visit(owner, `${list}?q=backend`)
  await expect(owner.getByText("Backend 21", { exact: true }).filter({ visible: true })).toBeVisible()
  await shot(owner, "phone-searched", false)
})
