import http from "k6/http"

import { AUTH_URL, EMAIL_TAG, PASSWORD, PROJECT_ID } from "./config.js"
import { api } from "./http.js"

const IDENTITY = `${AUTH_URL}/identitytoolkit.googleapis.com/v1`
// The emulator takes "owner" as an admin's token.
const ADMIN = { headers: { Authorization: "Bearer owner", "Content-Type": "application/json" } }
// Only accounts made by a load run match: owners on a reserved domain that receives no mail,
// candidates on Resend's test domain, which delivers to nobody (like e2e_tests/flow.py).
const THROWAWAY = /^(delivered\+)?load-[a-z0-9]+-(owner|candidate)-\d+@(example\.com|resend\.dev)$/

function identity(path, body, extra = {}) {
  const response = http.post(`${IDENTITY}/${path}`, JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
    ...extra,
    tags: { phase: "auth" },
  })

  if (response.status !== 200) {
    throw new Error(`emulator ${path} -> ${response.status} ${response.body}`)
  }

  return response.json()
}

/** A company owner's address: each its own inbox, since welcome credits come once per inbox. */
export function ownerEmail(run, index) {
  return `${EMAIL_TAG}${run}-owner-${index}@example.com`
}

export function candidateEmail(run, index) {
  return `delivered+${EMAIL_TAG}${run}-candidate-${index}@resend.dev`
}

export function signIn(email) {
  return identity("accounts:signInWithPassword?key=demo", {
    email,
    password: PASSWORD,
    returnSecureToken: true,
  }).idToken
}

/** A new emulator user with a verified email, as Google sign-in gives; their ID token. */
export function signUp(email) {
  const user = identity("accounts:signUp?key=demo", {
    email,
    password: PASSWORD,
    returnSecureToken: true,
  })
  identity(
    `projects/${PROJECT_ID}/accounts:update`,
    { localId: user.localId, emailVerified: true },
    ADMIN
  )

  return signIn(email)
}

/** The emulator's load-test accounts, of one run or of every run. */
export function throwawayEmails(run) {
  const emails = []
  let page = ""

  do {
    const response = http.get(
      `${IDENTITY}/projects/${PROJECT_ID}/accounts:batchGet?maxResults=1000${page}`,
      { ...ADMIN, tags: { phase: "auth" } }
    )
    const body = response.json()

    for (const user of body.users || []) {
      if (THROWAWAY.test(user.email || "") && (!run || user.email.includes(`-${run}-`))) {
        emails.push(user.email)
      }
    }

    page = body.nextPageToken ? `&nextPageToken=${body.nextPageToken}` : ""
  } while (page)

  return emails
}

/** Deletes the accounts the way a user does it in settings, which also deletes the companies
 * they alone own. Candidates go first, so each owner's company is gone last. How many are left. */
export function deleteAccounts(run) {
  const ownersLast = (email) => (email.includes("-owner-") ? 1 : 0)
  const emails = throwawayEmails(run).sort((a, b) => ownersLast(a) - ownersLast(b))

  for (const email of emails) {
    try {
      api("DELETE", "/accounts/me", signIn(email))
    } catch (error) {
      console.warn(`couldn't delete ${email}: ${error}`)
    }
  }

  return throwawayEmails(run).length
}
