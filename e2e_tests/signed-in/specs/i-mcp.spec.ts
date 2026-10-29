import type { Locator, Page } from "@playwright/test"
import { createHash, randomBytes } from "node:crypto"

import { FRONTEND_URL } from "../constants"
import { expect, test } from "../fixtures"
import { createCompany } from "../helpers/api"
import { addAiConnections, deleteAiConnections } from "../helpers/db-integrations"
import { box, PHONE, settled } from "../helpers/layout"
import { integrationRow, openDialog, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { uidOf } from "../helpers/sign-in"
import { setScheme } from "../helpers/theme"
import { throwawayEmail } from "../helpers/users"

/** Checks an Instructions dialog opened on the dialog itself (not its first field), and that
 * only its body scrolls: Close, in its footer, sits outside the scrolling part. */
async function expectInstructionsDialog(page: Page, dialog: Locator) {
  await expect
    .poll(() => page.evaluate(() => document.activeElement?.getAttribute("role")))
    .toBe("dialog")
  const closeInBody = await dialog.evaluate((popup) => {
    const scrolling = [...popup.querySelectorAll("*")].find(
      (item) => getComputedStyle(item).overflowY === "auto"
    )
    const close = popup.querySelector("[data-slot=dialog-footer] button")

    return { scrolling: Boolean(scrolling), close: Boolean(close), inside: scrolling?.contains(close!) }
  })
  expect(closeInBody).toEqual({ scrolling: true, close: true, inside: false })
}

// The MCP server sits last on the integrations tab, with its Instructions: the server's address
// and how to add it to Claude and ChatGPT. A real connection needs an AI app going through
// OAuth, so the user's connections are saved straight into the database; disconnecting goes
// through the API for real.
test("an owner sees the MCP server's instructions and disconnects AI apps", async ({
  signInAs,
}) => {
  const owner = await signInAs(throwawayEmail("mcp"))
  const uid = await uidOf(owner)
  const company = await createCompany(owner)
  const tab = `/companies/${company.id}/integrations`

  try {
    await visit(owner, tab)
    const row = integrationRow(owner, "/ai")
    await expect(row.locator("[data-slot=badge]")).toHaveCount(0)

    // The address to copy (the server's own), then Claude's and ChatGPT's steps with Claude
    // Code's command, which adds that address.
    await openDialog(owner, row.getByTestId("instructions"))
    const dialog = owner.getByRole("dialog")
    const copies = dialog.getByRole("textbox")
    await expect(copies.first()).toHaveValue(/\/mcp$/)
    const address = await copies.first().inputValue()
    await expect(copies.last()).toHaveValue(new RegExp(` ${address}$`))
    await expect(dialog.locator("form").first().getByRole("button")).toBeEnabled()
    await expectInstructionsDialog(owner, dialog)
    await shot(owner, "instructions")
    await dialog.getByRole("button").last().click()
    await expect(dialog).toHaveCount(0)

    await visit(owner, `${tab}/ai`)
    const apps = owner.getByRole("main").getByRole("listitem")
    await expect(owner.getByRole("main").getByTestId("instructions").filter({ visible: true })).toBeVisible()
    await expect(apps).toHaveCount(0)
    await shot(owner, "no-apps")

    // Connected: one "connected" tag, and the apps' names, the latest first.
    await addAiConnections(uid, ["Claude", "ChatGPT"])
    await visit(owner, tab)
    await expect(row.locator("[data-slot=badge]")).toHaveCount(1)
    await expect(row.getByText("Claude, ChatGPT", { exact: true }).filter({ visible: true })).toBeVisible()
    await shot(owner, "row-connected")

    // The row opens the apps' page: each with Disconnect, which asks first.
    await row.getByRole("link").click()
    await expect(owner).toHaveURL(new RegExp(`${tab}/ai$`))
    await expect(apps).toHaveCount(2)
    await expect(apps.getByRole("button")).toHaveCount(2)
    await shot(owner, "apps")
    const claude = apps.filter({ hasText: "Claude" })
    await openDialog(owner, claude.getByRole("button"))
    await expect(owner.getByRole("dialog")).toContainText("Claude")
    await owner.getByRole("dialog").getByRole("button").last().click()
    await expect(apps).toHaveCount(1)
    await expect(apps).toContainText("ChatGPT")
    await expect(owner.getByText("Claude", { exact: true })).toHaveCount(0)
  } finally {
    await deleteAiConnections(uid)
  }
})

// On a phone the MCP server's Instructions fill the screen.
test("the MCP server's instructions fill a phone's screen", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("mcp-phone"))
  const company = await createCompany(owner)
  await owner.setViewportSize(PHONE)

  await visit(owner, `/companies/${company.id}/integrations/ai`)
  await openDialog(owner, owner.getByRole("main").getByTestId("instructions"))
  await settled(owner.getByRole("dialog"))
  const dialog = await box(owner.getByRole("dialog"))
  expect(Math.abs(dialog.height - PHONE.height)).toBeLessThanOrEqual(2)
  expect(dialog.top).toBe(0)
  await expectInstructionsDialog(owner, owner.getByRole("dialog"))
  await shot(owner, "instructions-phone", false)
})

// An AI app sends the user to /connect to allow it. A request the API doesn't know (expired or
// already answered) says so, with nothing to answer; a real one shows who asks, with a warning
// for an app prepza doesn't know, and Deny (the first button) sends the browser back to the app.
// Real requests come from an app's OAuth, so that one is answered in the browser.
test("the consent page asks before an AI app may use the account", async ({ signInAs }) => {
  const email = throwawayEmail("mcp-consent")
  const user = await signInAs(email)
  const main = user.getByRole("main")
  const expired = main.getByText("This link has expired or was already used.", { exact: false })

  await visit(user, "/connect?request=e2e-unknown")
  await expect(expired).toBeVisible()
  await expect(main.getByRole("button")).toHaveCount(0)

  await user.route("**/assistant/connect/e2e-request", (route) =>
    route.fulfill({
      json: {
        client_name: "E2E App",
        redirect_host: "e2e.example.com",
        known_client: false,
        read_only: false,
      },
    })
  )
  await user.route("**/assistant/connect/e2e-request/deny", (route) =>
    // An app's address is absolute (the page never follows anything else).
    route.fulfill({ json: { redirect_url: new URL("/?error=access_denied", user.url()).href } })
  )
  await visit(user, "/connect?request=e2e-request")
  // Who asks: the app, where it goes back to, and the account it would use.
  await expect(main.getByRole("heading", { level: 1 })).toContainText("E2E App")
  await expect(main).toContainText("e2e.example.com")
  await expect(main).toContainText(email)
  // The warning for an app prepza doesn't know, and Deny and Allow.
  await expect(main.getByRole("status")).toBeVisible()
  await expect(main.getByRole("button")).toHaveCount(2)
  await shot(user, "consent")
  // Changes off: the app may only read.
  await main.getByRole("switch").click()
  await expect(main.getByRole("switch")).not.toBeChecked()
  await shot(user, "consent-read-only")
  await setScheme(user, "dark")
  await shot(user, "consent-read-only-dark")
  await main.getByRole("switch").click()
  await shot(user, "consent-dark")
  await setScheme(user, "light")
  await main.getByRole("button").first().click()
  await expect(user).toHaveURL(/\/\?error=access_denied$/)

  // Allowed with changes off: the approval asks for read only.
  const approvals: unknown[] = []
  await user.route("**/assistant/connect/e2e-request/approve", (route) => {
    approvals.push(route.request().postDataJSON())

    return route.fulfill({ json: { redirect_url: new URL("/?code=e2e", user.url()).href } })
  })
  await visit(user, "/connect?request=e2e-request")
  await main.getByRole("switch").click()
  await main.getByRole("button").last().click()
  await expect(user).toHaveURL(/\/\?code=e2e$/)
  expect(approvals).toEqual([{ read_only: true }])

  // An app that asked only to read: no switch to turn changes on.
  await user.route("**/assistant/connect/e2e-reader", (route) =>
    route.fulfill({
      json: {
        client_name: "E2E Reader",
        redirect_host: "e2e.example.com",
        known_client: true,
        read_only: true,
      },
    })
  )
  await visit(user, "/connect?request=e2e-reader")
  await expect(main.getByRole("button")).toHaveCount(2)
  await expect(main.getByRole("switch")).toHaveCount(0)

  // A request that runs out while the card is open says it expired, not "something went wrong".
  await user.route("**/assistant/connect/e2e-expiring", (route) =>
    route.fulfill({
      json: {
        client_name: "E2E App",
        redirect_host: "e2e.example.com",
        known_client: false,
        read_only: false,
      },
    })
  )
  await user.route("**/assistant/connect/e2e-expiring/approve", (route) =>
    route.fulfill({ status: 404, json: { detail: "Not found" } })
  )
  await visit(user, "/connect?request=e2e-expiring")
  await main.getByRole("button").last().click()
  await expect(expired).toBeVisible()
  await expect(main.getByRole("button")).toHaveCount(0)
})

// Allow completes the connection for real: an app on the user's computer registers and asks
// prepza through /authorize, as Claude Code does; Allow sends the browser back to the app with a
// code and the state it sent, and the app exchanges the code for its tokens. The app's own page
// isn't there, so the browser's return to it is answered by the test.
test("Allow on the consent page connects the AI app", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("mcp-allow"))
  const uid = await uidOf(owner)
  const company = await createCompany(owner)
  const callback = "http://127.0.0.1:53682/callback"
  const name = "E2E Local App"
  const registered = await owner.request.post(`${FRONTEND_URL}/register`, {
    data: {
      client_name: name,
      redirect_uris: [callback],
      token_endpoint_auth_method: "none",
      grant_types: ["authorization_code", "refresh_token"],
      response_types: ["code"],
    },
  })
  expect(registered.status()).toBe(201)
  const clientId: string = (await registered.json()).client_id
  const verifier = randomBytes(32).toString("base64url")
  const challenge = createHash("sha256").update(verifier).digest("base64url")
  await owner.route(`${callback}*`, (route) => route.fulfill({ body: "Back in the app" }))

  try {
    const query = new URLSearchParams({
      response_type: "code",
      client_id: clientId,
      redirect_uri: callback,
      code_challenge: challenge,
      code_challenge_method: "S256",
      state: "e2e-state",
    })
    await visit(owner, `/authorize?${query}`)
    await expect(owner).toHaveURL(/\/connect\?request=/)
    const main = owner.getByRole("main")
    await expect(main.getByRole("heading", { level: 1 })).toContainText(name)
    // No warning: no unknown app.
    await expect(main.getByRole("status")).toHaveCount(0)
    await shot(owner, "consent-local-app")
    await main.getByRole("button").last().click()
    // The answer names its issuer (RFC 9207) after the code and the app's state.
    await expect(owner).toHaveURL(
      /^http:\/\/127\.0\.0\.1:53682\/callback\?code=[^&]+&state=e2e-state&iss=http%3A%2F%2Flocalhost%3A8090$/
    )
    const code = new URL(owner.url()).searchParams.get("code") ?? ""

    // The app's side: the code buys its tokens, once.
    const exchange = () =>
      owner.request.post(`${FRONTEND_URL}/token`, {
        form: {
          grant_type: "authorization_code",
          code,
          redirect_uri: callback,
          client_id: clientId,
          code_verifier: verifier,
        },
      })
    const tokens = await exchange()
    expect(tokens.status()).toBe(200)
    const granted = await tokens.json()
    expect(granted.access_token).toMatch(/^pzm_/)
    // Allowed with changes on (the default): everything.
    expect(granted.scope).toBe("prepza")
    expect((await exchange()).status()).toBe(400)

    // The user sees the app connected.
    await visit(owner, `/companies/${company.id}/integrations/ai`)
    const app = owner.getByRole("main").getByRole("listitem").filter({ hasText: name })
    await expect(app.getByRole("button")).toBeVisible()
    await shot(owner, "apps-after-allow")
  } finally {
    await deleteAiConnections(uid, [clientId])
  }
})
