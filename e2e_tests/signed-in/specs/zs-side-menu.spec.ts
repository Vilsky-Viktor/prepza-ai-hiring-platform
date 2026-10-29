import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, createInterview } from "../helpers/api"
import { addSlackConnection } from "../helpers/db-integrations"
import { PHONE } from "../helpers/layout"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, throwawayEmail } from "../helpers/users"

// The page menus: on wide screens a list at the content's side that stays in view and scrolls
// itself when taller than the window; on phones two tabs and the other pages under "…", an
// open one of those taking the second place.

// A company's pages for its owner, in the menu's order (the owner sees all of them).
const COMPANY_PAGES = [
  "/interviews",
  "/templates",
  "/members",
  "/integrations",
  "/brand",
  "/billing",
  "/actions",
  "/referrals",
]

/** The page menu shown in the page (the other, for the other screen size, is hidden). */
function menu(page: Page) {
  return page.getByRole("main").getByRole("navigation").first()
}

/** The count beside the menu's page that leads to `path` (nothing at 0). */
function countOf(page: Page, path: string) {
  return menu(page).locator(`a[href$="${path}"]`).getByTestId("menu-count")
}

/** Where the menu's links lead, each as the end of its address after the company's. */
async function pagesOf(page: Page, companyId: string, links = menu(page).getByRole("link")) {
  const hrefs = await links.evaluateAll((all) => all.map((link) => link.getAttribute("href") ?? ""))

  return hrefs.map((href) => href.replace(`/companies/${companyId}`, ""))
}

// On a wide screen: the company's pages in order with the open one marked; taller than the
// window, the menu scrolls on its own; and while a page scrolls it holds under the window's top.
// Beside a page's name, how many things it holds: nothing at 0.
test("a company's side menu lists its pages, scrolls on its own and stays in view", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interview = await createInterview(owner, company.id)
  await visit(owner, `/companies/${company.id}/members`)

  await expect.poll(() => pagesOf(owner, company.id)).toEqual(COMPANY_PAGES)
  // One interview and the owner alone; no integration or referral yet, so no count beside them.
  await expect(countOf(owner, "/interviews")).toHaveText("1")
  await expect(countOf(owner, "/members")).toHaveText("1")
  await expect(countOf(owner, "/integrations")).toHaveCount(0)
  await expect(countOf(owner, "/referrals")).toHaveCount(0)
  await expect(countOf(owner, "/templates")).toHaveCount(0)
  // A pending invite counts in the team, a working Slack in the integrations.
  await api(owner, "POST", `/companies/members?company_id=${company.id}`, {
    email: throwawayEmail("menu-count"),
    role: "viewer",
  })
  await addSlackConnection(company.id)
  // The menu leaves out a count another service didn't give within 2 s (a busy local stack), so
  // the page is opened again until it has it.
  await expect(async () => {
    await owner.reload()
    await expect(countOf(owner, "/members")).toHaveText("2", { timeout: 5_000 })
    await expect(countOf(owner, "/integrations")).toHaveText("1", { timeout: 5_000 })
  }).toPass({ timeout: 60_000 })
  const open = menu(owner).locator('a[aria-current="page"]')
  await expect(open).toHaveCount(1)
  await expect(open).toHaveAttribute("href", `/companies/${company.id}/members`)
  await shot(owner, "company-menu")

  await owner.setViewportSize({ width: 1280, height: 400 })
  await visit(owner, `/companies/${company.id}/interviews`)
  const nav = menu(owner)
  await expect(nav.getByRole("link")).toHaveCount(COMPANY_PAGES.length)
  expect(await nav.evaluate((element) => element.scrollHeight > element.clientHeight)).toBe(true)
  await nav.hover()
  await owner.mouse.wheel(0, 200)
  await expect.poll(() => nav.evaluate((element) => element.scrollTop)).toBeGreaterThan(0)
  await expect(nav.getByRole("link").last()).toBeInViewport()
  await shot(owner, "menu-scrolled", false)

  // Scrolled past where the menu starts, it holds 24px under the window's top (sticky's
  // top-6), where it would otherwise have gone above it.
  await owner.setViewportSize({ width: 1280, height: 500 })
  await visit(owner, `/companies/${company.id}/interviews/${interview}`)
  await expect(nav.locator('a[aria-current="page"]')).toBeVisible()
  const start = await nav.evaluate((element) => element.getBoundingClientRect().top + window.scrollY)
  await owner.evaluate((top) => window.scrollTo(0, top + 100), start)
  await expect
    .poll(() => nav.evaluate((element) => Math.round(element.getBoundingClientRect().top)))
    .toBe(24)
  await expect(nav.locator('a[aria-current="page"]')).toBeInViewport()
  await shot(owner, "menu-in-view", false)
})

test("on a phone the menu shows two tabs and the rest under more", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  await owner.setViewportSize(PHONE)
  await visit(owner, `/companies/${company.id}/interviews`)
  const tabs = menu(owner).getByRole("link")
  const more = menu(owner).getByRole("button")
  const items = owner.getByRole("menu").getByRole("menuitem")

  // The first two, the open one marked; the others in their order under "…".
  await expect.poll(() => pagesOf(owner, company.id)).toEqual(COMPANY_PAGES.slice(0, 2))
  await expect(tabs.first()).toHaveAttribute("aria-current", "page")
  await expect(more).toHaveAccessibleName(/.+/)
  await expect(async () => {
    await more.click()
    await expect(owner.getByRole("menu")).toBeVisible({ timeout: 2_000 })
  }).toPass()
  expect(await pagesOf(owner, company.id, items)).toEqual(COMPANY_PAGES.slice(2))
  await shot(owner, "phone-more-open")

  // A page from the menu, once open, takes the second place, and the one it replaces goes under
  // "…".
  await items.last().click()
  await expect(owner).toHaveURL(new RegExp(`/companies/${company.id}/referrals$`))
  await expect
    .poll(() => pagesOf(owner, company.id))
    .toEqual(["/interviews", "/referrals"])
  await expect(tabs.last()).toHaveAttribute("aria-current", "page")
  // The two tabs and "…" fit the phone's width: none is cut off at the row's edges.
  const fits = await menu(owner).evaluate((nav) => {
    const row = nav.parentElement!.getBoundingClientRect()

    return [...nav.children].every((child) => {
      const box = child.getBoundingClientRect()

      return box.left >= row.left - 1 && box.right <= row.right + 1
    })
  })
  expect(fits).toBe(true)
  await expect(async () => {
    await more.click()
    await expect(owner.getByRole("menu")).toBeVisible({ timeout: 2_000 })
  }).toPass()
  expect(await pagesOf(owner, company.id, items)).toEqual(COMPANY_PAGES.slice(1, 7))
  await shot(owner, "phone-overflow-open")
})
