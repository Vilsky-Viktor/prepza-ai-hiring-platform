import * as Sentry from "@sentry/nextjs"

import { sentryOptions } from "@/lib/sentry"

export function register() {
  Sentry.init(sentryOptions())
}

// Errors in server components, route handlers and the proxy.
export const onRequestError = Sentry.captureRequestError
