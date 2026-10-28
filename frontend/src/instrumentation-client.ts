import * as Sentry from "@sentry/nextjs"

import { sentryOptions } from "@/lib/sentry"

Sentry.init(sentryOptions())

// Traces navigations between pages.
export const onRouterTransitionStart = Sentry.captureRouterTransitionStart
