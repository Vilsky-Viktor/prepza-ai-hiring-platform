import { randomUUID } from "node:crypto";

import { withDatabase } from "./db";

// Every row these helpers add has an event id starting with this, so it's found and removed.
const PREFIX = "e2e-";
// The service that makes each kind of call the tests add (billing accepts only real services).
const SERVICE: Record<string, string> = {
  assistant_message: "assistant",
  interview_generation: "generation",
};

export type AiCall = {
  action: string;
  category: string;
  cost: number;
  at: Date;
  companyId?: string;
  userId?: string;
  // What the call was for (a generation, a conversation): an action's units count these.
  subjectId?: string;
};

/** AI calls for a throwaway company or user, saved straight into billing's ai_usage as billing
 * saves the ai.used events the services publish (a real one costs OpenAI money).
 * deleteAiRows deletes them. */
export async function addAiCalls(calls: AiCall[]) {
  await withDatabase("billing", async (client) => {
    for (const call of calls) {
      await client.query(
        `INSERT INTO ai_usage (id, event_id, occurred_at, action, service, model, input_tokens,
           cached_input_tokens, output_tokens, audio_seconds, cost, company_id, user_id,
           subject_id, outcome, category)
         VALUES (gen_random_uuid(), $1, $2, $3, $9, 'gpt-6-luna', 1000, 0, 100, 0, $4, $5,
           $6, $7, 'ok', $8)`,
        [
          `${PREFIX}${randomUUID()}`,
          call.at,
          call.action,
          call.cost,
          call.companyId ?? null,
          call.userId ?? null,
          call.subjectId ?? null,
          call.category,
          SERVICE[call.action] ?? "generation",
        ],
      );
    }
  });
}

/** Refusals of limit `limit` for a throwaway company and user, saved straight into billing's
 * limit_hits as billing saves the limit.hit events. deleteAiRows deletes them. */
export async function addLimitHits(
  limit: string,
  count: number,
  at: Date,
  companyId: string,
  userId: string,
) {
  await withDatabase("billing", async (client) => {
    for (let index = 0; index < count; index++) {
      await client.query(
        `INSERT INTO limit_hits (id, event_id, occurred_at, "limit", kind, scope, company_id,
           user_id)
         VALUES (gen_random_uuid(), $1, $2, $3, 'ours', 'company', $4, $5)`,
        [`${PREFIX}${randomUUID()}`, at, limit, companyId, userId],
      );
    }
  });
}

/** Deletes the AI calls and limit hits of a throwaway company or user. */
export async function deleteAiRows(companyId: string, userId: string) {
  await withDatabase("billing", async (client) => {
    for (const table of ["ai_usage", "limit_hits"]) {
      await client.query(
        `DELETE FROM ${table} WHERE event_id LIKE '${PREFIX}%'
           AND (company_id = $1 OR user_id = $2)`,
        [companyId, userId],
      );
    }
  });
}

/** The database's clock now, to tell the changes a test made from older ones. */
export async function billingNow(): Promise<Date> {
  return withDatabase("billing", async (client) => {
    const result = await client.query("SELECT now() AS now");

    return result.rows[0].now as Date;
  });
}

/** Deletes the history entries of limit `name` made since `since` (a test's own changes). */
export async function deleteLimitChanges(name: string, since: Date) {
  await withDatabase("billing", (client) =>
    client.query("DELETE FROM limit_changes WHERE name = $1 AND changed_at >= $2", [
      name,
      since,
    ]),
  );
}
