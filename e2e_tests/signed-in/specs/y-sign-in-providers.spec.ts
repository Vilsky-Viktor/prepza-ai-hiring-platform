import { expect, test } from "../fixtures"
import { signIn, type SignInProvider, tokenOf } from "../helpers/sign-in"
import { ownerEmail } from "../helpers/users"

// Each way to sign in opens its provider's page in a popup that hands the sign-in back to the
// site, which the site's Cross-Origin-Opener-Policy (same-origin-allow-popups) must allow.
const PROVIDERS: [SignInProvider, string][] = [
  ["google", "google.com"],
  ["linkedin", "oidc.linkedin"],
  ["github", "github.com"],
]

for (const [provider, claim] of PROVIDERS) {
  test(`signing in with ${provider} through its popup works`, async ({ browser }) => {
    const page = await signIn(browser, ownerEmail(), {}, undefined, provider)
    const payload = (await tokenOf(page)).split(".")[1]
    const token = JSON.parse(Buffer.from(payload, "base64url").toString())

    expect(token.firebase.sign_in_provider).toBe(claim)
    await page.context().close()
  })
}

test("pages keep other sites' windows out but let the sign-in popups answer", async ({
  signInAs,
}) => {
  // Signed in on the companies page; loading it again gives its headers.
  const page = await signInAs(ownerEmail())
  const response = await page.reload()

  expect(response?.headers()["cross-origin-opener-policy"]).toBe("same-origin-allow-popups")
})
