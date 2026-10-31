import { withSentryConfig } from "@sentry/nextjs/config"
import type { NextConfig } from "next"
import createNextIntlPlugin from "next-intl/plugin"

import { EMBED_SCRIPT_HEADERS } from "./src/config/embed"
import { REPORT_SAMPLES_HEADERS } from "./src/config/report-samples"
import {
  DOCUMENT_HEADERS,
  PICTURE_HEADERS,
  VAD_HEADERS,
} from "./src/config/static-files"

const nextConfig: NextConfig = {
  output: "standalone",
  // No X-Powered-By header: it only tells attackers what the site runs on.
  poweredByHeader: false,
  // Responses go out uncompressed: Cloud CDN compresses them, with Brotli for browsers that take
  // it, which it can't do for a response already gzipped here (the gateway, locally).
  compress: false,
  // Version skew protection: the commit CI builds the image from (a build argument). A page left
  // open across a deploy then reloads in full on its next navigation instead of asking the new
  // server for the old build's files. Unset in development, where it does nothing.
  deploymentId: process.env.SENTRY_RELEASE || undefined,
  // Into the browser's code too, under its own name (only NEXT_PUBLIC_ names go there by
  // themselves); read when the site is built. Not secret: it only allows sending error reports.
  env: {
    FRONTEND_SENTRY_DSN: process.env.FRONTEND_SENTRY_DSN ?? "",
  },
  // The dev server serves its scripts to a phone on the local network too (development only).
  allowedDevOrigins: ["192.168.*.*", "10.*.*.*", "172.*.*.*"],
  // The preview pictures' font files and the developer docs' MCP examples, read at request
  // time, go into the standalone server.
  outputFileTracingIncludes: {
    "/preview": ["./assets/fonts/**"],
    "/opengraph-image": ["./assets/fonts/**"],
    "/api-docs": ["./content/mcp/**"],
  },
  // Titles, canonical addresses and hreflang always go in the <head>, for every visitor and
  // crawler: Next.js would otherwise stream a slow page's metadata into the body, which only
  // crawlers that run JavaScript read.
  htmlLimitedBots: /.*/,
  // The dev server keeps its last 30 compiled pages for 15 minutes: recompiling one it dropped
  // after a minute reloads the page that's open, closing its dialogs (the browser tests' flakes),
  // while keeping every page for an hour grew it past 7 GB.
  onDemandEntries: {
    maxInactiveAge: 15 * 60 * 1000,
    pagesBufferLength: 30,
  },
  // Companies' pages moved from /company to /companies; links in emails and notifications sent
  // before still work.
  async redirects() {
    return [
      { source: "/company", destination: "/companies", permanent: true },
      {
        source: "/company/:path*",
        destination: "/companies/:path*",
        permanent: true,
      },
    ]
  },
  async headers() {
    return [
      { source: "/embed/:file*", headers: EMBED_SCRIPT_HEADERS },
      { source: "/samples/:file*", headers: REPORT_SAMPLES_HEADERS },
      // Files in public/; "+" so the /documents, /about and /features pages themselves aren't matched.
      { source: "/ats/:file+", headers: PICTURE_HEADERS },
      { source: "/integrations/:file+", headers: PICTURE_HEADERS },
      { source: "/about/:file+", headers: PICTURE_HEADERS },
      { source: "/features/:file+", headers: PICTURE_HEADERS },
      { source: "/icon.png", headers: PICTURE_HEADERS },
      { source: "/documents/:file+", headers: DOCUMENT_HEADERS },
      { source: "/examples/:file+", headers: DOCUMENT_HEADERS },
      { source: "/vad/:file+", headers: VAD_HEADERS },
    ]
  },
  // In `pnpm dev` there is no gateway in front of Next, so proxy the API to it.
  async rewrites() {
    if (!process.env.API_URL) {
      return []
    }

    return [
      {
        source: "/api/:path*",
        destination: `${process.env.API_URL}/api/:path*`,
      },
    ]
  },
}

// Errors reach Sentry through /monitoring on our own domain, so ad blockers don't drop them and
// the Content-Security-Policy needs no new origin. Source maps upload only with SENTRY_AUTH_TOKEN.
// next-intl reads the interface language per request in src/i18n/request.ts.
const withNextIntl = createNextIntlPlugin()

export default withSentryConfig(withNextIntl(nextConfig), {
  tunnelRoute: "/monitoring",
  silent: true,
  telemetry: false,
})
