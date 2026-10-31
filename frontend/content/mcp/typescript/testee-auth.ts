// Signs your agent in to testee's MCP server, shared by the examples.
// npm install @modelcontextprotocol/sdk@1.32.1
import { existsSync, readFileSync, writeFileSync } from "node:fs"
import { createServer } from "node:http"

import {
  auth,
  type OAuthClientProvider,
} from "@modelcontextprotocol/sdk/client/auth.js"
import type {
  OAuthClientInformationMixed,
  OAuthTokens,
} from "@modelcontextprotocol/sdk/shared/auth.js"

export const TESTEE_MCP = process.env.TESTEE_MCP ?? "https://testee.ai/mcp"
const REDIRECT = "http://localhost:8765/callback"
const STORE = "testee-tokens.json"

function kept(): Record<string, any> {
  return existsSync(STORE) ? JSON.parse(readFileSync(STORE, "utf8")) : {}
}

function keep(key: string, value: unknown) {
  writeFileSync(STORE, JSON.stringify({ ...kept(), [key]: value }))
}

/** The tokens in a file: each refresh replaces both, so the new ones must be kept. */
class FileProvider implements OAuthClientProvider {
  redirectUrl = REDIRECT
  clientMetadata = { client_name: "My agent", redirect_uris: [REDIRECT] }

  clientInformation = () => kept().client
  saveClientInformation = (info: OAuthClientInformationMixed) =>
    keep("client", info)
  tokens = () => kept().tokens
  saveTokens = (tokens: OAuthTokens) => keep("tokens", tokens)
  saveCodeVerifier = (verifier: string) => keep("verifier", verifier)
  codeVerifier = () => kept().verifier

  redirectToAuthorization(url: URL) {
    console.log(`Open this page to allow the agent: ${url}`)
  }
}

/** The code testee's consent page sends back to this computer once you allow the agent. */
function waitForCode(): Promise<string> {
  return new Promise((resolve) => {
    const server = createServer((request, response) => {
      const code = new URL(request.url ?? "", REDIRECT).searchParams.get("code")
      response.end("Signed in to testee. You can close this tab.")

      if (code) {
        server.close()
        resolve(code)
      }
    }).listen(8765)
  })
}

/** With TESTEE_API_KEY set, the agent signs in with that company API key (a server, no
 * browser); otherwise as you, allowing it once in the browser. */
export async function signIn(): Promise<{
  authProvider?: OAuthClientProvider
  headers?: Record<string, string>
}> {
  const key = process.env.TESTEE_API_KEY

  if (key) {
    return { headers: { Authorization: `Bearer ${key}` } }
  }

  const provider = new FileProvider()

  if ((await auth(provider, { serverUrl: TESTEE_MCP })) === "REDIRECT") {
    const authorizationCode = await waitForCode()
    await auth(provider, { serverUrl: TESTEE_MCP, authorizationCode })
  }

  return { authProvider: provider }
}
