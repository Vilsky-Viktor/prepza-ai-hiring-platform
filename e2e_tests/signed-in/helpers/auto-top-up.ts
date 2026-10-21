import { BILLING_URL } from "../constants";
import { withDatabase } from "./db";

/** What a throwaway company's running automatic top-up is set to, written as billing keeps it
 * (services/billing/app/models/billing.py AutoTopUp): $50 under 500 credits on `buyerId`'s card,
 * paused when asked. Its subscription
 * is made up, so Paddle never charges it: the test deletes the row before the company goes
 * (removeAutoTopUp), as deleting the company would ask Paddle to cancel it. */
export async function setAutoTopUp(
  companyId: string,
  buyerId: string,
  { paused = false }: { paused?: boolean },
) {
  await withDatabase("billing", (client) =>
    client.query(
      `INSERT INTO auto_top_ups (owner_type, owner_id, product, threshold, buyer_id,
         subscription_id, currency, declines, paused_at)
       VALUES ('company', $1, 'topup_50', 500, $2, $3, 'USD', $4, $5)`,
      [
        companyId,
        buyerId,
        `sub_e2e_${companyId}`,
        paused ? 4 : 0,
        paused ? new Date() : null,
      ],
    ),
  );
}

/** Removes the company's automatic top-up, so deleting the company asks Paddle nothing. */
export async function removeAutoTopUp(companyId: string) {
  await withDatabase("billing", (client) =>
    client.query(
      "DELETE FROM auto_top_ups WHERE owner_type = 'company' AND owner_id = $1",
      [companyId],
    ),
  );
}

/** Asks billing's outbox to tell the company `kind` (a bell notification and, for billing's
 * kinds, an email to its owners and admins), as billing does, and publishes it at once. */
export async function notifyCompany(
  request: { post: (url: string) => Promise<unknown> },
  companyId: string,
  kind: string,
  data: Record<string, unknown> = {},
) {
  await withDatabase("billing", (client) =>
    client.query(
      `INSERT INTO outbox (id, event_type, data, created_at, attempts)
       VALUES (gen_random_uuid(), 'notification.requested', $1, now(), 0)`,
      [
        JSON.stringify({
          recipient: "company",
          recipient_id: companyId,
          kind,
          link: `/companies/${companyId}/billing`,
          data,
          key: `${kind}:${companyId}:e2e`,
        }),
      ],
    ),
  );
  // Billing's scheduled publish, called now.
  await request.post(`${BILLING_URL}/internal/schedules/outbox`);
}
