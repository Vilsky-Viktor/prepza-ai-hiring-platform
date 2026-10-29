import { API_URL } from "./constants"
import { env } from "./helpers/env"
import { RUN } from "./helpers/users"

// After every run, the run's throwaway accounts (tagged with RUN, helpers/users.ts) are deleted
// the way a user deletes theirs in settings, which also deletes the companies they alone own and
// their data in every service. Another run's are left alone while it may still be running, so
// runs at the same time don't delete each other's users; what a stopped run left behind goes once
// it's older than STALE_MS. Only the tests' own addresses match: owners on reserved domains that
// receive no mail, invitees on Resend's test domain.
const THROWAWAY =
  /^(e2e-owner-[0-9a-f-]+@(example\.com|e2e-[0-9a-f]+\.test)|delivered\+e2e-[a-z0-9-]+@resend\.dev)$/
// Longer than a whole run of the suite takes.
const STALE_MS = 6 * 60 * 60 * 1000
const AUTH_URL = process.env.AUTH_URL ?? "http://firebase-auth:9199"
const IDENTITY = `${AUTH_URL}/identitytoolkit.googleapis.com/v1`
// The emulator takes "owner" as an admin's token.
const ADMIN = { Authorization: "Bearer owner", "Content-Type": "application/json" }
const PASSWORD = "e2e-cleanup"
// How often, and how long apart, what's left is counted again while deletions land.
const LEFT_CHECKS = 10
const LEFT_CHECK_MS = 3_000

type EmulatorUser = { localId: string; email?: string; createdAt?: string }

/** This run's account, or one a stopped run left behind long enough ago. */
function ours(user: EmulatorUser, now: number) {
  return (user.email ?? "").includes(`-${RUN}-`) || now - Number(user.createdAt ?? 0) > STALE_MS
}

async function identity(path: string, body: object, admin = false) {
  const response = await fetch(`${IDENTITY}/${path}`, {
    method: "POST",
    headers: admin ? ADMIN : { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    throw new Error(`emulator ${path} -> ${response.status}`, { cause: await response.text() })
  }

  return response.json()
}

async function throwawayUsers(project: string): Promise<EmulatorUser[]> {
  const users: EmulatorUser[] = []
  let page = ""

  do {
    const response = await fetch(
      `${IDENTITY}/projects/${project}/accounts:batchGet?maxResults=1000${page}`,
      { headers: ADMIN }
    )
    const body = await response.json()
    users.push(
      ...(body.users ?? []).filter(
        (user: EmulatorUser) => THROWAWAY.test(user.email ?? "") && ours(user, Date.now())
      )
    )
    page = body.nextPageToken ? `&nextPageToken=${body.nextPageToken}` : ""
  } while (page)

  return users
}

/** Signs in as the user (a password set by the emulator's admin, since they joined through the
 * emulator's Google page), deletes their account through the API, then the emulator user. */
async function deleteUser(project: string, user: EmulatorUser) {
  await identity(
    `projects/${project}/accounts:update`,
    { localId: user.localId, password: PASSWORD },
    true
  )
  const { idToken } = await identity("accounts:signInWithPassword?key=demo", {
    email: user.email,
    password: PASSWORD,
    returnSecureToken: true,
  })
  const deleted = await fetch(`${API_URL}/accounts/me`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${idToken}` },
  })

  if (!deleted.ok && deleted.status !== 404) {
    throw new Error(`deleting ${user.email} -> ${deleted.status}`)
  }

  // Deleting the account through the API may already have removed its sign-in.
  await identity(`projects/${project}/accounts:delete`, { localId: user.localId }, true).catch(
    (error: Error) => {
      if (!String(error.cause ?? "").includes("USER_NOT_FOUND")) {
        throw error
      }
    }
  )
}

export default async function teardown() {
  const project = env("FIREBASE_PROJECT_ID")
  // Invitees first, so each owner's company is deleted last, with its candidates gone.
  const users = (await throwawayUsers(project)).sort(
    (a, b) => Number(a.email?.startsWith("e2e-owner-")) - Number(b.email?.startsWith("e2e-owner-"))
  )
  const failed: string[] = []

  for (const user of users) {
    try {
      await deleteUser(project, user)
    } catch (error) {
      failed.push(String(error))
    }
  }

  // An account's deletion reaches its sign-in through an event: count what's left of these
  // accounts once it has. Only these: another account may have aged past STALE_MS meanwhile.
  const ids = new Set(users.map((user) => user.localId))
  const remaining = async () =>
    (await throwawayUsers(project)).filter((user) => ids.has(user.localId)).length
  let left = await remaining()

  for (let tries = 0; left > 0 && tries < LEFT_CHECKS; tries++) {
    await new Promise((resolve) => setTimeout(resolve, LEFT_CHECK_MS))
    left = await remaining()
  }

  console.log(`clean-up: ${users.length - left} throwaway accounts deleted, ${left} left`)

  if (left > 0) {
    throw new Error(`throwaway accounts left after clean-up:\n${failed.join("\n")}`)
  }
}
