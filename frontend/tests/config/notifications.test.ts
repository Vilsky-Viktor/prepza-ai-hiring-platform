import { describe, expect, it } from "vitest"

import { NOTIFICATION_LOOKS } from "@/config/notifications"
import en from "../../messages/en.json"

describe("the bell's notification kinds", () => {
  it("gives every kind the services send a look and a text", () => {
    expect(Object.keys(NOTIFICATION_LOOKS).sort()).toEqual(
      Object.keys(en.notifications.kinds).sort()
    )
  })

  it("shows a paused automatic top-up as a problem to act on", () => {
    expect(NOTIFICATION_LOOKS.auto_top_up_paused.alert).toBe(true)
    expect(NOTIFICATION_LOOKS.auto_top_up_price_change.alert).toBe(false)
    expect(NOTIFICATION_LOOKS.auto_top_up_on.alert).toBe(false)
  })
})
