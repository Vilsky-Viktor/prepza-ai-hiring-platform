import { cookies } from "next/headers"
import { getLocale } from "next-intl/server"

import {
  PUBLIC_REVALIDATE_SECONDS,
  PUBLIC_TIMEOUT_MS,
  SERVER_TIMEOUT_MS,
} from "@/config/api"
import { TOKEN_COOKIE } from "@/config/auth"
import { REFERRAL_COOKIE } from "@/config/referral"

// Signed out, not allowed, missing, or a malformed id in the URL: the page shows
// "not found" or a sign-in prompt.
const EXPECTED_MISSES = [401, 403, 404, 422]

/** Whether the visitor has a sign-in token: a signed-in page shows them the sign-in prompt
 * otherwise, then itself (not "not found", as its API calls would make it). */
export async function signedIn(): Promise<boolean> {
  return (await cookies()).has(TOKEN_COOKIE)
}

/**
 * Server-side API call, with the user's token when signed in. Null when the resource is
 * missing or not visible to the user; other failures throw so the error page shows.
 */
export async function serverFetch<T>(path: string): Promise<T | null> {
  const jar = await cookies()
  const token = jar.get(TOKEN_COOKIE)?.value
  const referral = jar.get(REFERRAL_COOKIE)?.value
  // The services' messages and texts in the page's language.
  const headers: Record<string, string> = {
    "Accept-Language": await getLocale(),
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  // As the browser's own calls do: the first visit after sign-up may happen here.
  if (referral) {
    headers.Cookie = `${REFERRAL_COOKIE}=${referral}`
  }

  return request<T>(path, {
    headers,
    cache: "no-store",
    signal: AbortSignal.timeout(SERVER_TIMEOUT_MS),
  })
}

/**
 * serverFetch for what a page adds to its main data (a company's credits, one integration's
 * state, the pause): null also when its service fails or doesn't answer, so the page shows
 * without it instead of failing.
 */
export async function optionalFetch<T>(path: string): Promise<T | null> {
  try {
    return await serverFetch<T>(path)
  } catch (error) {
    console.error(`Left out ${path}:`, error)

    return null
  }
}

/**
 * Server-side API call for data that is the same for every visitor, without the user's token:
 * kept for a few minutes, and given up on after a few seconds so a slow or sleeping service
 * doesn't hold the page. Null and errors as in serverFetch. In the interface language, or in
 * `locale` when the caller names one; `fresh` asks every time, for data a change must reach at
 * once (a deleted news post must not stay on the page).
 */
export async function publicFetch<T>(
  path: string,
  { locale, fresh = false }: { locale?: string; fresh?: boolean } = {}
): Promise<T | null> {
  return request<T>(path, {
    headers: { "Accept-Language": locale ?? (await getLocale()) },
    ...(fresh
      ? { cache: "no-store" }
      : { next: { revalidate: PUBLIC_REVALIDATE_SECONDS } }),
    signal: AbortSignal.timeout(PUBLIC_TIMEOUT_MS),
  })
}

async function request<T>(path: string, init: RequestInit): Promise<T | null> {
  const response = await fetch(`${process.env.API_URL}/api${path}`, init)

  if (EXPECTED_MISSES.includes(response.status)) {
    return null
  }

  if (!response.ok) {
    throw new Error(`API request ${path} failed with status ${response.status}`)
  }

  return response.json()
}
