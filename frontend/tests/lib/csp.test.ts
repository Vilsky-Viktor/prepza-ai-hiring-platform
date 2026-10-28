import { afterEach, expect, it, vi } from "vitest"

import { contentSecurityPolicy, newNonce } from "@/lib/csp"

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
