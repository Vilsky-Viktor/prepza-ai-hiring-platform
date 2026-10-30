import { afterEach, expect, it, vi } from "vitest"

import { contentSecurityPolicy, newNonce, ownSocketOrigin } from "@/lib/csp"

afterEach(() => {
  vi.unstubAllEnvs()
})

// Locally the sign-in emulator is allowed on any host at its port, so a phone that opened the
// site by the computer's address can sign in.
it("allows the sign-in emulator on any host, locally", () => {
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL", "http://localhost:9199")
  const policy = contentSecurityPolicy("nonce", true)

  expect(policy).toMatch(/connect-src [^;]*http:\/\/\*:9199/)
  expect(policy).toMatch(/frame-src [^;]*http:\/\/\*:9199/)
})

it("has no emulator without one", () => {
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL", "")
  const policy = contentSecurityPolicy("nonce", false)

  expect(policy).not.toContain("9199")
})

// Voice mode plays Mira's clips from blob addresses; without this Chrome refuses every one.
it("lets the page play audio from blob addresses", () => {
  expect(contentSecurityPolicy("nonce", false)).toMatch(/media-src [^;]*blob:/)
})

// Voice mode's speech detector runs on WebAssembly; the policy allows compiling it, never eval.
it("lets WebAssembly compile but keeps eval out of production", () => {
  const scripts = contentSecurityPolicy("nonce", false).match(
    /script-src [^;]*/
  )?.[0]

  expect(scripts).toContain("'wasm-unsafe-eval'")
  expect(scripts).not.toContain("'unsafe-eval'")
})

// Production's pages ask for https everywhere; the local stack, plain http with the sign-in
// emulator (a production build too, as the browser tests run), doesn't.
it("upgrades insecure requests in production only", () => {
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL", "")
  expect(contentSecurityPolicy("nonce", false)).toContain(
    "upgrade-insecure-requests"
  )
  expect(contentSecurityPolicy("nonce", true)).not.toContain(
    "upgrade-insecure-requests"
  )

  vi.stubEnv("NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL", "http://localhost:9199")
  expect(contentSecurityPolicy("nonce", false)).not.toContain(
    "upgrade-insecure-requests"
  )
})

it("lets no one frame a page, but a company's own site its embedded interview", () => {
  expect(contentSecurityPolicy("nonce", false)).toContain(
    "frame-ancestors 'none'"
  )
  expect(
    contentSecurityPolicy("nonce", false, "acme.com *.acme.com")
  ).toContain("frame-ancestors acme.com *.acme.com")
})

it("makes a nonce of 128 random bits, new for every page", () => {
  const nonces = Array.from({ length: 50 }, () => newNonce())

  expect(new Set(nonces).size).toBe(50)
  for (const nonce of nonces) {
    expect(atob(nonce)).toHaveLength(16)
  }
})

// Voice mode's live listening connects to the site's own WebSocket, which 'self' doesn't cover
// in every browser: the request's host is named, with its port when the gateway forwards it.
it.each([
  [{ host: "prepza.ai" }, "wss://prepza.ai"],
  [
    {
      host: "localhost",
      "x-forwarded-host": "localhost:8082",
      "x-forwarded-proto": "http",
    },
    "ws://localhost:8082",
  ],
  // Anything that isn't a host never reaches the policy.
  [{ host: "evil.test; script-src *" }, ""],
])("allows the site's own WebSocket from %j", (headers, origin) => {
  expect(ownSocketOrigin(new Headers(headers))).toBe(origin)
})

it("names the site's own WebSocket in connect-src", () => {
  expect(
    contentSecurityPolicy("nonce", false, "'none'", "wss://prepza.ai")
  ).toMatch(/connect-src 'self' wss:\/\/prepza\.ai /)
})
