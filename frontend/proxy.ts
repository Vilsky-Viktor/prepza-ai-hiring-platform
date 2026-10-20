import { NextResponse, type NextRequest } from "next/server"

import { TOKEN_COOKIE } from "@/constants/auth"
import { LOCALE_COOKIE, LOCALE_COOKIE_MAX_AGE } from "@/constants/i18n"
import {
  MAINTENANCE_HEADER,
  MAINTENANCE_OPEN_PAGES,
} from "@/constants/maintenance"
import { LOCALE_HEADER } from "@/constants/seo"
import { EMBED_PAGE } from "@/constants/embed"
import { contentSecurityPolicy } from "@/lib/csp"
import { embedAncestors } from "@/lib/embed"
import { isPrivatePath, splitLocale } from "@/lib/locale-path"
import { maintenanceState } from "@/lib/maintenance"

/** A fresh nonce for every page; Next.js adds it to its own scripts from the request header.
 * While maintenance mode is on, every page is the maintenance screen, except for superadmins and
 * the unsubscribe and legal pages (MAINTENANCE_OPEN_PAGES).
 * A page under a language prefix (/de/pricing) is served from its page in that language; private
 * pages are kept out of search results. No site may frame a page, but a company's own its
 * embedded interview. */
export async function proxy(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64")
  const embedded = EMBED_PAGE.exec(request.nextUrl.pathname)
  const policy = contentSecurityPolicy(
    nonce,
    process.env.NODE_ENV === "development",
    embedded ? await embedAncestors(embedded[1]) : undefined
  )
  const requestHeaders = new Headers(request.headers)
  requestHeaders.set("x-nonce", nonce)
  requestHeaders.set("Content-Security-Policy", policy)

  const maintenance = await maintenanceState(
    request.cookies.get(TOKEN_COOKIE)?.value
  )
  requestHeaders.set(MAINTENANCE_HEADER, maintenance)
  const localized = splitLocale(request.nextUrl.pathname)

  // Only the proxy names the address's language; a visitor's own header is dropped.
  requestHeaders.delete(LOCALE_HEADER)

  if (localized) {
    requestHeaders.set(LOCALE_HEADER, localized.locale)
  }

  // A public page's language comes from its address (or the visitor's chosen one), never from
  // the browser's, so its plain address is the English page that search engines index.
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

  // A first visit through a language's address keeps that language on the next pages, whose
  // links have no prefix; a chosen language (the cookie) is never changed.
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

// Pages only: not the API (/api/..., but /api-docs is a page), static files or link prefetches.
// Nor the hosted embed script (/embed/v1.js): companies' sites load it as it is, also during
// maintenance, when the frame it makes shows the maintenance screen.
export const config = {
  matcher: [
    {
      source: "/((?!api/|embed/|_next/static|_next/image|favicon.ico|icon.svg).*)",
      missing: [
        { type: "header", key: "next-router-prefetch" },
        { type: "header", key: "purpose", value: "prefetch" },
      ],
    },
  ],
}
