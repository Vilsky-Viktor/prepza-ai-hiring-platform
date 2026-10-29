import { NextResponse, type NextRequest } from "next/server"

import { TOKEN_COOKIE } from "@/config/auth"
import { LOCALE_COOKIE, LOCALE_COOKIE_MAX_AGE } from "@/config/i18n"
import {
  MAINTENANCE_HEADER,
  MAINTENANCE_OPEN_PAGES,
} from "@/config/maintenance"
import { LOCALE_HEADER, PLAIN_ADDRESS_HEADER } from "@/config/seo"
import { EMBED_PAGE } from "@/config/embed"
import { contentSecurityPolicy, newNonce } from "@/lib/csp"
import { embedAncestors } from "@/lib/embed"
import {
  hasLanguageVersions,
  isPrivatePath,
  splitLocale,
} from "@/lib/locale-path"
import { maintenanceState } from "@/lib/maintenance"

/** A fresh nonce for every page; Next.js adds it to its own scripts from the request header.
 * While maintenance mode is on, every page is the maintenance screen, except for superadmins and
 * the unsubscribe and legal pages (MAINTENANCE_OPEN_PAGES).
 * A page under a language prefix (/de/pricing) is served from its page in that language; private
 * pages are kept out of search results. No site may frame a page, but a company's allowed
 * domains its embedded interview. */
export async function proxy(request: NextRequest) {
  const nonce = newNonce()
  const embedded = EMBED_PAGE.exec(request.nextUrl.pathname)
  // Asked together: who may frame an embedded interview, and whether maintenance is on.
  const [ancestors, maintenance] = await Promise.all([
    embedded
      ? embedAncestors(
          embedded[1],
          request.nextUrl.searchParams.get("origin"),
          request.headers.get("referer")
        )
      : undefined,
    maintenanceState(request.cookies.get(TOKEN_COOKIE)?.value),
  ])
  const policy = contentSecurityPolicy(
    nonce,
    process.env.NODE_ENV === "development",
    ancestors
  )
  const requestHeaders = new Headers(request.headers)
  requestHeaders.set("x-nonce", nonce)
  requestHeaders.set("Content-Security-Policy", policy)

  requestHeaders.set(MAINTENANCE_HEADER, maintenance)
  const localized = splitLocale(request.nextUrl.pathname)

  // Only the proxy names the address's language; a visitor's own headers are dropped.
  requestHeaders.delete(LOCALE_HEADER)
  requestHeaders.delete(PLAIN_ADDRESS_HEADER)

  if (localized) {
    requestHeaders.set(LOCALE_HEADER, localized.locale)
  } else if (hasLanguageVersions(request.nextUrl.pathname)) {
    // The plain address of a page with language versions is always its English one.
    requestHeaders.set(PLAIN_ADDRESS_HEADER, "1")
  }

  // A public page's language comes from its address, never from the browser's, so its plain
  // address is the English page that search engines index.
  if (!isPrivatePath(request.nextUrl.pathname)) {
    requestHeaders.delete("accept-language")
  }

  const closed =
    maintenance === "closed" &&
    !MAINTENANCE_OPEN_PAGES.includes(
      localized?.path ?? request.nextUrl.pathname
    )
  const response = closed
    ? NextResponse.rewrite(new URL("/maintenance", request.url), {
        status: 503,
        request: { headers: requestHeaders },
      })
    : localized
      ? NextResponse.rewrite(
          new URL(`${localized.path}${request.nextUrl.search}`, request.url),
          { request: { headers: requestHeaders } }
        )
      : NextResponse.next({ request: { headers: requestHeaders } })
  response.headers.set("Content-Security-Policy", policy)

  if (isPrivatePath(request.nextUrl.pathname)) {
    response.headers.set("X-Robots-Tag", "noindex")
  }

  // A first visit through a language's address keeps that language on the pages with one
  // address (signed-in ones, the legal pages); a chosen language (the cookie) is never changed.
  if (localized && !request.cookies.has(LOCALE_COOKIE)) {
    response.cookies.set(LOCALE_COOKIE, localized.locale, {
      maxAge: LOCALE_COOKIE_MAX_AGE,
      sameSite: "lax",
      secure: request.nextUrl.protocol === "https:",
      path: "/",
    })
  }

  return response
}

// Pages only: not the API (/api/..., but /api-docs is a page), Next's files, link prefetches or
// the files in public/ (each folder and file, tests/lib/proxy-matcher.test.ts). Nor the hosted
// embed script (/embed/v1.js): companies' sites load it as it is, also during maintenance, when
// the frame it makes shows the maintenance screen. A link to a language's address (/de/pricing)
// is prefetched through the proxy too: only its rewrite finds the page (every language but
// English, as LOCALES lists them).
export const config = {
  matcher: [
    {
      source:
        "/((?!api/|embed/|_next/|favicon.ico|icon.svg|icon.png|about/|ats/|documents/|examples/|integrations/|samples/).*)",
      missing: [
        { type: "header", key: "next-router-prefetch" },
        { type: "header", key: "purpose", value: "prefetch" },
      ],
    },
    {
      source:
        "/(ru|uk|es|pt|de|fr|it|pl|nl|tr|ar|he|fa|ja|zh|ko|hi|id|th|vi|fil|et)(/.*)?",
    },
  ],
}
