import type { ErrorEvent } from "@sentry/nextjs"
import { describe, expect, it } from "vitest"

import { sentryOptions } from "@/lib/sentry"

const scrub = (event: object) => sentryOptions().beforeSend(event as ErrorEvent)

describe("sentryOptions", () => {
  it("keeps every link's secret token and email out of an error report", () => {
    const event = {
      request: { url: "https://prepza.ai/unsubscribe?token=abc.def&x=1" },
      breadcrumbs: [
        { data: { url: "/api/notifications/unsubscribe/abc.def" } },
        {
          message:
            "Opened /embedded/s3cret and /invite/t0k3n for ann@example.com",
        },
        { data: { url: "/api/companies/links/l1nk/start" } },
      ],
    }

    expect(scrub(event)).toEqual({
      request: { url: "https://prepza.ai/unsubscribe?token=[token]&x=1" },
      breadcrumbs: [
        { data: { url: "/api/notifications/unsubscribe/[token]" } },
        { message: "Opened /embedded/[token] and /invite/[token] for [email]" },
        { data: { url: "/api/companies/links/[token]/start" } },
      ],
    })
  })
})
