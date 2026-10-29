import { type Browser, expect, type Locator, type Page } from "@playwright/test"

import { API_URL, HUMAN_CHECK_TOKEN, LOCALE_COOKIE, SITE_URL, TOKEN_COOKIE } from "../constants"
import { type EmulatorSession, googleSignIn, refreshed } from "./emulator"
import { env } from "./env"
import { visit } from "./navigation"

// The email boxes under the sign-in buttons to tick first; both start unticked. `ui` signs in
// through the site's own button and the emulator's sign-in page, for the tests of signing in.
export type SignInEmails = { noUpdates?: boolean; promotions?: boolean; ui?: boolean }
// The ways to sign in the site offers (frontend/src/config/auth.ts).
export type SignInProvider = "google" | "linkedin" | "github"
// How long the language cookie lasts, as the site writes it: a year.
const LOCALE_SECONDS = 365 * 24 * 60 * 60

/** A new browser signed in as `email` (Google; the emulator marks the email verified). Signing in
 * is what a few tests check (`emails.ui`, another `provider`): those go through the site's button
 * and the emulator's sign-in page. Every other test signs in straight at the emulator and opens
 * the site with the session the site's Firebase would have kept, saving the sign-in page's wait.
 * A new account's `displayName` (its sign-in's name claim) is the email's local part unless
 * given. */
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

  if (emails.ui || provider !== "google") {
    return signInThroughPopup(browser, email, emails, displayName, provider)
  }

  const session = await firstSignIn(await googleSignIn(email, displayName), emails)
  const context = await browser.newContext({ storageState: storageOf(session) })
  const page = await context.newPage()
  await visit(page, "/companies")
  await expect(page.locator("main h1")).toBeVisible()

  return page
}

/** What the site does once someone signs in, made through the API: a new account's language (the
 * page's, English) and the sign-in's email boxes (sign-in-options.tsx, auth-provider.tsx). The
 * session then carries the language, so the site has nothing left to change once it opens. */
async function firstSignIn(session: EmulatorSession, emails: SignInEmails) {
  const call = (path: string, body: object, token: string) =>
    fetch(`${API_URL}${path}`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        "X-Human-Check": HUMAN_CHECK_TOKEN,
      },
      body: JSON.stringify(body),
    }).then((response) => {
      if (!response.ok) {
        throw new Error(`PUT ${path} -> ${response.status}`)
      }
    })
  const changes = { updates: !emails.noUpdates, ...(emails.promotions ? { promotions: true } : {}) }
  await call("/accounts/me/email-preferences", { changes, source: "sign_in" }, session.idToken)
  if (claimsOf(session).language) {
    return session
  }

  await call("/accounts/me/settings", { language: "en" }, session.idToken)

  return refreshed(session)
}

/** The claims of the session's ID token (the account's language among them). */
function claimsOf(session: EmulatorSession) {
  return JSON.parse(Buffer.from(session.idToken.split(".")[1], "base64url").toString())
}

/** The browser's storage for a signed-in session: the user as the site's Firebase saves it (its
 * local storage, which it moves to IndexedDB on loading) and the cookies it writes, the token's
 * and the account's language, so the first page is already in it and nothing changes after. */
function storageOf(session: EmulatorSession) {
  const apiKey = env("NEXT_PUBLIC_FIREBASE_API_KEY")
  const now = Date.now()
  const user = {
    uid: session.uid,
    email: session.email,
    emailVerified: true,
    displayName: session.displayName || undefined,
    isAnonymous: false,
    providerData: [
      {
        providerId: "google.com",
        uid: session.uid,
        displayName: session.displayName || null,
        email: session.email,
        phoneNumber: null,
        photoURL: null,
      },
    ],
    stsTokenManager: {
      refreshToken: session.refreshToken,
      accessToken: session.idToken,
      expirationTime: now + session.expiresIn * 1000,
    },
    createdAt: String(now),
    lastLoginAt: String(now),
    apiKey,
    appName: "[DEFAULT]",
  }
  const site = new URL(SITE_URL)
  const cookie = (name: string, value: string, seconds: number) => ({
    name,
    value,
    domain: site.hostname,
    path: "/",
    expires: Math.floor(now / 1000) + seconds,
    httpOnly: false,
    secure: false,
    sameSite: "Lax" as const,
  })

  return {
    cookies: [
      cookie(TOKEN_COOKIE, session.idToken, session.expiresIn),
      cookie(LOCALE_COOKIE, claimsOf(session).language, LOCALE_SECONDS),
    ],
    origins: [
      {
        origin: site.origin,
        localStorage: [{ name: `firebase:authUser:${apiKey}:[DEFAULT]`, value: JSON.stringify(user) }],
      },
    ],
  }
}

/** Signs in through the site's own "Continue with Google" (or another `provider`'s button) and
 * the Auth emulator's sign-in page (never the real provider): an account the emulator already has
 * is picked from its list, any other is added. `emails` ticks the email boxes first. */
async function signInThroughPopup(
  browser: Browser,
  email: string,
  emails: SignInEmails,
  displayName: string,
  provider: SignInProvider,
): Promise<Page> {
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

  const reuse = (await existing.count()) > 0
  const submit = reuse ? existing.first() : popup.locator("#sign-in")

  if (!reuse) {
    await popup.getByText(/add new account/i).click()
    await popup.locator("#email-input").fill(email)
    await popup.locator("#display-name-input").fill(displayName)
  }

  await chooseAccount(popup, submit)
  // Signed in once the frontend writes the token cookie and re-renders the page with it.
  await expect
    .poll(async () => (await context.cookies()).some((c) => c.name === TOKEN_COOKIE))
    .toBe(true)
  // The companies page, in whatever language the account uses, rendered again as signed in: its
  // sign-in options gone (a busy run may take a while to render it).
  await expect(page.locator("main h1")).toBeVisible()
  await expect(page.getByTestId(`sign-in-${provider}`)).toHaveCount(0, { timeout: 90_000 })

  return page
}

/** Chooses the account on the emulator's page and waits for the page to close. It listens for the
 * close before clicking: the page can close while the click is still being reported. A click that
 * lands before the page's script is ready does nothing and the page stays open, so if it's still
 * open after a while and the button is still there, it's clicked once more; never an endless
 * wait. */
async function chooseAccount(popup: Page, submit: Locator) {
  const closed = popup.waitForEvent("close", { timeout: 60_000 })
  const soon = popup
    .waitForEvent("close", { timeout: 15_000 })
    .then(() => true)
    .catch(() => false)
  await clickUnlessClosed(popup, submit)

  if (!(await soon) && !popup.isClosed() && (await submit.isVisible().catch(() => false))) {
    await clickUnlessClosed(popup, submit)
  }

  await closed
}

/** Clicks `submit` on the emulator's page; the page closing as it's clicked is what's wanted. */
async function clickUnlessClosed(popup: Page, submit: Locator) {
  await submit.click().catch((error: unknown) => {
    if (!popup.isClosed()) {
      throw error
    }
  })
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
