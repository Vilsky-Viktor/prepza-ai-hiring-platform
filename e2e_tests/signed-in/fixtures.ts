import { test as base, type Page } from "@playwright/test"

import { API_URL } from "./constants"
import { deleteOwnCompanies } from "./helpers/api"
import { env } from "./helpers/env"
import { signIn, tokenOf, type SignInEmails } from "./helpers/sign-in"

type Fixtures = {
  // Signs in through a new browser; a throwaway user's companies are deleted when the test ends,
  // and every browser is closed.
  signInWith: (
    email: string,
    throwaway: boolean,
    emails?: SignInEmails,
    displayName?: string
  ) => Promise<Page>
  // A new browser signed in as `email`, a throwaway user the test made up (named `displayName`
  // when new): straight at the Auth emulator, or with `{ ui: true }` through the site's sign-in,
  // ticking the sign-in's email boxes `emails` names first.
  signInAs: (email: string, emails?: SignInEmails, displayName?: string) => Promise<Page>
  // A new browser signed in as the first superadmin in SUPERADMIN_EMAILS (emulator only). Nothing
  // of theirs is deleted.
  signInSuperadmin: () => Promise<Page>
  // Turns the global pause and maintenance mode off when the test ends, however it ends (a
  // timeout too): given the superadmin's page, it keeps their token and calls the API itself,
  // as the page may be closed by then.
  switchesOffAfter: (superadmin: Page) => Promise<void>
}

export const test = base.extend<Fixtures>({
  signInWith: async ({ browser }, use) => {
    const opened: { page: Page; throwaway: boolean }[] = []

    await use(async (email, throwaway, emails, displayName) => {
      const page = await signIn(browser, email, emails, displayName)
      opened.push({ page, throwaway })

      return page
    })

    for (const { page, throwaway } of opened) {
      if (throwaway) {
        await deleteOwnCompanies(page).catch(() => {})
      }

      await page.context().close()
    }
  },
  signInAs: async ({ signInWith }, use) => {
    await use((email, emails, displayName) => signInWith(email, true, emails, displayName))
  },
  signInSuperadmin: async ({ signInWith }, use) => {
    const email = env("SUPERADMIN_EMAILS").split(",")[0].trim().toLowerCase()
    await use(() => signInWith(email, false))
  },
  switchesOffAfter: async ({ playwright }, use) => {
    let token = ""

    await use(async (superadmin) => {
      token = await tokenOf(superadmin)
    })

    if (!token) {
      return
    }

    const request = await playwright.request.newContext()
    const headers = { Authorization: `Bearer ${token}` }
    await request.put(`${API_URL}/companies/superadmin/maintenance`, { headers, data: { on: false } })
    await request.put(`${API_URL}/companies/superadmin/pause`, { headers, data: { paused: false } })
    await request.dispose()
  },
})

export { expect } from "@playwright/test"
