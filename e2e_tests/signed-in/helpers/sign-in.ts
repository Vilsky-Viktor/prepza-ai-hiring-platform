import { type Browser, expect, type Page } from "@playwright/test"

import { TOKEN_COOKIE } from "../constants"
import { env } from "./env"
import { visit } from "./navigation"

// The email boxes under the sign-in buttons to tick first; both start unticked.
export type SignInEmails = { noUpdates?: boolean; promotions?: boolean }
// The ways to sign in the site offers (frontend/constants/auth.ts).
export type SignInProvider = "google" | "linkedin" | "github"


/** A new browser signed in as `email`, through the site's own "Continue with Google" (or another
 * `provider`'s button) and the Auth emulator's sign-in page (never the real provider): an account
 * the emulator already has is picked from its list, any other is added. The emulator marks these
 * emails verified. `emails` ticks the email boxes first. A new account's `displayName` (its
 * sign-in's name claim) is the email's local part unless given. */
export async function signIn(
  browser: Browser,
  email: string,
  emails: SignInEmails = {},
  displayName = email.split("@")[0],
  provider: SignInProvider = "google",
): Promise<Page> {
  if (!env("NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL")) {
    throw new Error("Signed-in tests need the Firebase Auth emulator")
  }

  const context = await browser.newContext()
  const page = await context.newPage()
  // A page that only asks to sign in shows the options inline.
  await visit(page, "/companies")

  for (const box of ["noUpdates", "promotions"] as const) {
    if (emails[box]) {
      const checkbox = page.getByTestId(`email-box-${box}`)
      await checkbox.click()
      await expect(checkbox).toBeChecked()
    }
  }

  const popup = await openPopup(page, provider)
  await popup.waitForLoadState()
  // Each listed account carries its claims, the email among them, URL-encoded.
  const claim = encodeURIComponent(`"email":"${email}"`)
  const existing = popup.locator(`li.js-reuse-account[data-id-token*="${claim}"]`)

  if ((await existing.count()) > 0) {
    await existing.first().click()
  } else {
    await popup.getByText(/add new account/i).click()
    await popup.locator("#email-input").fill(email)
    await popup.locator("#display-name-input").fill(displayName)
    await popup.locator("#sign-in").click()
  }

  await popup.waitForEvent("close")
  // Signed in once the frontend writes the token cookie and re-renders the page with it.
  await expect
    .poll(async () => (await context.cookies()).some((c) => c.name === TOKEN_COOKIE))
    .toBe(true)
  // The companies page, in whatever language the account uses.
  await expect(page.locator("main h1")).toBeVisible()

  return page
}

/** Clicks the provider's button until the emulator's page opens: a click before the page is
 * ready opens nothing. A page that opens late still counts, and while one is open the buttons
 * are disabled, so a click waits for them instead of failing. */
async function openPopup(page: Page, provider: SignInProvider): Promise<Page> {
  const popups: Page[] = []
  const onPage = (opened: Page) => popups.push(opened)
  page.context().on("page", onPage)

  try {
    await expect(async () => {
      if (popups.length === 0) {
        const button = page.getByTestId(`sign-in-${provider}`)
        await expect(button).toBeEnabled({ timeout: 5_000 })
        await button.click()
      }

      await expect.poll(() => popups.length, { timeout: 5_000 }).toBeGreaterThan(0)
    }).toPass({ timeout: 120_000 })
  } finally {
    page.context().off("page", onPage)
  }

  return popups[0]
}

/** The signed-in user's token, for setting things up through the API. */
export async function tokenOf(page: Page): Promise<string> {
  const cookie = (await page.context().cookies()).find((c) => c.name === TOKEN_COOKIE)

  if (!cookie?.value) {
    throw new Error("not signed in")
  }

  return cookie.value
}

/** The signed-in user's id (their token's user_id claim), for rows saved straight into a
 * database for them. */
export async function uidOf(page: Page): Promise<string> {
  const payload = (await tokenOf(page)).split(".")[1]

  return JSON.parse(Buffer.from(payload, "base64url").toString()).user_id
}
