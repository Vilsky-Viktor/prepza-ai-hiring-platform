import { afterEach, beforeEach, expect, it, vi } from "vitest"

const getAuth = vi.fn(() => ({ name: "auth" }))
const initializeAuth = vi.fn(() => ({ name: "framed" }))
const inMemoryPersistence = { type: "NONE" }
const connectAuthEmulator = vi.fn()

vi.mock("firebase/app", () => ({ initializeApp: vi.fn(() => ({})) }))
vi.mock("firebase/auth", () => ({
  getAuth,
  initializeAuth,
  inMemoryPersistence,
  connectAuthEmulator,
}))

beforeEach(() => {
  vi.resetModules()
  vi.clearAllMocks()
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.unstubAllEnvs()
})

// The emulator is reached on the host the page was opened from: a phone on the local network
// reaches the computer's emulator, not its own.
it("loads Firebase Auth once, on first use, against the emulator when set", async () => {
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL", "http://localhost:9099")
  vi.stubGlobal("window", { location: { hostname: "192.168.1.25" } })
  const { firebaseAuth } = await import("@/lib/firebase")

  expect(getAuth).not.toHaveBeenCalled()
  const [first, second] = await Promise.all([firebaseAuth(), firebaseAuth()])

  expect(first).toBe(second)
  expect(await firebaseAuth()).toBe(first)
  expect(getAuth).toHaveBeenCalledTimes(1)
  expect(connectAuthEmulator).toHaveBeenCalledWith(
    first,
    "http://192.168.1.25:9099",
    { disableWarnings: true }
  )
})

// In a company's site's frame, the guest's sign-in stays in memory, not in the frame's
// partitioned storage.
it("keeps a framed page's sign-in in memory", async () => {
  const top = {}
  vi.stubGlobal("window", {
    top,
    self: {},
    location: { hostname: "localhost" },
  })
  const { firebaseAuth } = await import("@/lib/firebase")

  expect(await firebaseAuth()).toEqual({ name: "framed" })
  expect(initializeAuth).toHaveBeenCalledWith(
    {},
    { persistence: inMemoryPersistence }
  )
  expect(getAuth).not.toHaveBeenCalled()
})
