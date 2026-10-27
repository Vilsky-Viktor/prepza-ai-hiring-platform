import { createHash, createHmac, randomUUID } from "node:crypto"

import { withDatabase } from "./db"
import { env } from "./env"

/** An address as the notifications service keeps it on its suppression list: never in the
 * clear, but its hash keyed with PERSON_HASH_KEY (services/notifications/app/helpers/
 * unsubscribe.py address_hash, prepza_common.auth.person_hash). */
function addressHash(email: string) {
  const digest = createHash("sha256").update(email.trim().toLowerCase()).digest("hex")

  return createHmac("sha256", env("PERSON_HASH_KEY")).update(digest).digest("hex")
}

/** Puts a throwaway address on the suppression list, as a hard bounce (or `reason`) does. */
export async function suppress(email: string, reason = "bounced") {
  await withDatabase("notifications", (client) =>
    client.query(
      `INSERT INTO suppressed_addresses (address, reason, created_at) VALUES ($1, $2, now())
       ON CONFLICT DO NOTHING`,
      [addressHash(email), reason]
    )
  )
}

/** Whether the address is on the suppression list; the test's own row is removed when asked. */
export async function isSuppressed(email: string, remove = false) {
  return withDatabase("notifications", async (client) => {
    const found = await client.query("SELECT 1 FROM suppressed_addresses WHERE address = $1", [
      addressHash(email),
    ])

    if (remove) {
      await client.query("DELETE FROM suppressed_addresses WHERE address = $1", [addressHash(email)])
    }

    return found.rowCount === 1
  })
}

/** A DPA notice already sent to one throwaway user only, about `version` (a version not in
 * force yet): it emails no one, and the legal banner concerns that user alone. Its id, or null
 * when a notice of that version exists already (a real one, never touched). */
export async function sentDpaNotice(version: string, userId: string) {
  const id = randomUUID()

  return withDatabase("notifications", async (client) => {
    const added = await client.query(
      `INSERT INTO bulk_sends (id, kind, about, asked_by, created_at, prepared_at, finished_at)
       VALUES ($1, 'legal_dpa', $2, 'e2e', now(), now(), now()) ON CONFLICT DO NOTHING`,
      [id, version]
    )

    if (added.rowCount !== 1) {
      return null
    }

    await client.query(
      `INSERT INTO bulk_recipients (send_id, user_id, status, attempts, sent_at)
       VALUES ($1, $2, 'sent', 1, now())`,
      [id, userId]
    )

    return id
  })
}

/** Deletes the test's notice, its recipient with it. */
export async function deleteNotice(id: string) {
  await withDatabase("notifications", (client) =>
    client.query("DELETE FROM bulk_sends WHERE id = $1", [id])
  )
}
