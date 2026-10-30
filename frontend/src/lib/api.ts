import { DEFAULT_LOCALE } from "@/config/i18n"
import { firebaseAuth } from "@/lib/firebase"

/** A refused request. `fromService`: the message is the service's own (in the user's language);
 * otherwise the load balancer or the platform answered (an HTML 429, 502 or 503) and the message
 * is only for the logs. */
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public fromService = false
  ) {
    super(message)
  }
}

/** The message in an error response: a string for errors the services raise, the first of a
list when input fails validation. */
export function errorDetail(body: unknown): string | null {
  const detail = (body as { detail?: unknown } | null)?.detail

  if (typeof detail === "string") {
    return detail
  }

  const first = Array.isArray(detail) ? detail[0]?.msg : null

  return typeof first === "string" ? first.replace(/^Value error, /, "") : null
}

/** The signed-in user's token, and the interface language for the services' messages. */
export async function authHeaders(): Promise<Record<string, string>> {
  // Right after page load Firebase may still be restoring the signed-in user.
  const auth = await firebaseAuth()
  await auth.authStateReady()
  const token = await auth.currentUser?.getIdToken()
  // The page's own language: a first visit has no cookie yet.
  const language = {
    "Accept-Language": document.documentElement.lang || DEFAULT_LOCALE,
  }

  return token ? { ...language, Authorization: `Bearer ${token}` } : language
}

/** The response when it's a success; otherwise its refusal, as an ApiError. */
export async function checkedResponse(response: Response) {
  if (!response.ok) {
    const detail = errorDetail(await response.json().catch(() => null))

    throw new ApiError(
      response.status,
      detail ?? `Request failed with status ${response.status}`,
      detail !== null
    )
  }

  return response
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers as Record<string, string> | undefined),
      ...(await authHeaders()),
    },
  })
  await checkedResponse(response)

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

/** The service's own message when it refused with one of `statuses` (its rules live in the
backend, which says why); null for anything else, a page the load balancer answered too. */
export function serviceRefusal(
  error: unknown,
  statuses: number[]
): string | null {
  return error instanceof ApiError &&
    error.fromService &&
    statuses.includes(error.status)
    ? error.message
    : null
}

/** The service's own message for nothing left to use (402), rate limits (429), invalid
input (422) and a temporary pause (503); the fallback for anything else. */
export function apiErrorMessage(error: unknown, fallback: string): string {
  return serviceRefusal(error, [402, 422, 429, 503]) ?? fallback
}
