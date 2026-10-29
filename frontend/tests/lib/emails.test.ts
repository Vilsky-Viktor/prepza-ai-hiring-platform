import { describe, expect, it, vi } from "vitest"

import { apiFetch } from "@/lib/api"
import { saveEmailPreferences, signInEmailChanges } from "@/lib/emails"

vi.mock("@/lib/api", () => ({ apiFetch: vi.fn(async () => ({})) }))

describe("signInEmailChanges", () => {
  it("asks for product updates unless the opt-out is ticked", () => {
    expect(signInEmailChanges({ noUpdates: false, promotions: false })).toEqual(
      { updates: true }
    )
    expect(signInEmailChanges({ noUpdates: true, promotions: false })).toEqual({
      updates: false,
    })
  })

  it("asks for promotions only when ticked, so nothing turns them off", () => {
    expect(signInEmailChanges({ noUpdates: true, promotions: true })).toEqual({
      updates: false,
      promotions: true,
    })
  })
})

describe("saveEmailPreferences", () => {
  it("sends the changes with where they were made", async () => {
    await saveEmailPreferences({ updates: true }, "sign_in")

    expect(apiFetch).toHaveBeenCalledWith("/accounts/me/email-preferences", {
      method: "PUT",
      body: JSON.stringify({ changes: { updates: true }, source: "sign_in" }),
    })
  })
})
