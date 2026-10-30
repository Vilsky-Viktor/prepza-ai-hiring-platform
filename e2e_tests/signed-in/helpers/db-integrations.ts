import { randomUUID } from "node:crypto";

import { GREENHOUSE_E2E_SECRET } from "../constants";
import { withDatabase } from "./db";
import { env } from "./env";
import { fernetEncrypt } from "./fernet";

/** An ATS connection for a throwaway company, saved straight into the ats database (a real one
 * needs an ATS account), with one job linked to `interviewId`. Workable's key is a placeholder,
 * so anything that calls Workable with it marks it broken; Greenhouse's is sealed for real, as
 * its page shows the web hook's secret key from it. Deleting the company deletes both (the ats
 * service handles its company.deleted event). */
export async function addAtsConnection(
  companyId: string,
  interviewId: string,
  candidates: { invited?: number; notInvited?: number } = {},
  provider:
    | "workable"
    | "greenhouse"
    | "teamtailor"
    | "recruitee"
    | "breezy" = "workable",
) {
  // Sealed for real where the page reads them (the web hook's address and secret key).
  const sealed = {
    workable: null,
    greenhouse: {
      client_id: "e2e",
      client_secret: "e2e",
      webhook_secret: GREENHOUSE_E2E_SECRET,
    },
    teamtailor: { host: "https://api.teamtailor.com", key: "e2e" },
    recruitee: { company: "e2e-acme", token: "e2e" },
    breezy: {
      company: "e2e",
      token: "e2e",
      webhook_id: "e2e",
      webhook_secret: "e2e",
    },
  }[provider];
  const credentials = sealed
    ? fernetEncrypt(env("ATS_ENCRYPTION_KEY"), JSON.stringify(sealed))
    : "placeholder";
  const account = {
    workable: "e2e-acme",
    greenhouse: "",
    teamtailor: "E2E Acme",
    recruitee: "e2e-acme",
    breezy: "E2E Acme",
  }[provider];

  await withDatabase("ats", async (client) => {
    const connection = await client.query(
      `INSERT INTO ats_connections (id, company_id, provider, account, credentials, status,
         created_by, created_at)
       VALUES (gen_random_uuid(), $1, $2, $3, $4, 'connected', 'e2e', now())
       RETURNING id`,
      [companyId, provider, account, credentials],
    );
    const link = await client.query(
      `INSERT INTO ats_job_links (id, company_id, connection_id, interview_id, job_id, job_name,
         stage_id, stage_name, created_at)
       VALUES (gen_random_uuid(), $1, $2, $3, 'E2E01', 'E2E Backend developer', 'assessment',
         'Assessment', now())
       RETURNING id`,
      [companyId, connection.rows[0].id, interviewId],
    );
    // Candidates the ATS "sent" for the job: invited, and not invited for lack of credits.
    const statuses = [
      ...Array(candidates.invited ?? 0).fill(["invited", null]),
      ...Array(candidates.notInvited ?? 0).fill(["failed", "credits"]),
    ];

    for (const [index, [status, reason]] of statuses.entries()) {
      await client.query(
        `INSERT INTO ats_candidates (id, company_id, connection_id, interview_id, link_id,
           candidate_id, email, status, reason, created_at)
         VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, $8, now())`,
        [
          companyId,
          connection.rows[0].id,
          interviewId,
          link.rows[0].id,
          `e2e-${index}`,
          `e2e-${index}@example.com`,
          status,
          reason,
        ],
      );
    }
  });
}

/** A Slack channel for a throwaway company, saved straight into the notifications database (a
 * real one needs prepza's Slack app and a workspace). Its web hook is a placeholder: nothing is
 * posted with it. Deleting the company deletes it. */
export async function addSlackConnection(companyId: string) {
  await withDatabase("notifications", (client) =>
    client.query(
      `INSERT INTO slack_connections (company_id, team, channel, webhook, token, kinds, status,
         created_by, created_at)
       VALUES ($1, 'E2E Acme', '#hiring', 'placeholder', 'placeholder',
         '["candidate_finished", "ats_not_invited", "invite_undelivered", "auto_top_up_failed"]',
         'connected', 'e2e', now())`,
      [companyId],
    ),
  );
}

/** A notification for a throwaway company, saved straight into the notifications database, as
 * the notifications service saves one it's asked for. Deleting the company deletes it. */
export async function addCompanyNotification(
  companyId: string,
  kind: string,
  link: string,
  data: Record<string, unknown>,
) {
  await withDatabase("notifications", (client) =>
    client.query(
      `INSERT INTO notifications (id, event_id, recipient, recipient_id, kind, link, data,
         created_at)
       VALUES (gen_random_uuid(), gen_random_uuid()::text, 'company', $1, $2, $3, $4, now())`,
      [companyId, kind, link, JSON.stringify(data)],
    ),
  );
}

/** Marks a throwaway company's web hook as failing, as the api service does after days of
 * retries, without waiting for them. */
export async function markWebhookFailing(url: string, companyId: string) {
  await withDatabase("api", (client) =>
    client.query(
      "UPDATE webhooks SET failing = true WHERE url = $1 AND company_id = $2",
      [url, companyId],
    ),
  );
}

/** Who made a throwaway company's API key or web hook, as the api service keeps it for their
 * data export; null once they deleted their account (its user.deleted event handled). */
export async function integrationMaker(table: "api_keys" | "webhooks", id: string) {
  return withDatabase("api", async (client) => {
    const found = await client.query(`SELECT created_by FROM ${table} WHERE id = $1`, [id]);

    return found.rows[0]?.created_by as string | null | undefined;
  });
}

/** Marks a throwaway company's ATS connection broken, as the ats service does when the ATS
 * refuses its key. */
export async function markAtsBroken(companyId: string) {
  await withDatabase("ats", (client) =>
    client.query(
      "UPDATE ats_connections SET status = 'broken' WHERE company_id = $1",
      [companyId],
    ),
  );
}

/** AI apps connected to a throwaway user's account, saved straight into the assistant database
 * (a real one needs an AI app going through OAuth): an app and one connection each, the first
 * named the latest. Their tokens are random hashes nothing holds. deleteAiConnections deletes
 * them. */
export async function addAiConnections(userId: string, names: string[]) {
  await withDatabase("assistant", async (client) => {
    for (const [index, name] of names.entries()) {
      const clientId = `e2e-${randomUUID()}`;
      await client.query(
        "INSERT INTO oauth_clients (client_id, info, created_at) VALUES ($1, $2, now())",
        [
          clientId,
          JSON.stringify({
            client_id: clientId,
            client_name: name,
            redirect_uris: [],
          }),
        ],
      );
      await client.query(
        `INSERT INTO mcp_grants (id, user_id, client_id, client_name, redirect_host, created_at,
           access_hash, access_expires_at, refresh_hash, refresh_expires_at)
         VALUES (gen_random_uuid(), $1, $2, $3, 'e2e.example.com',
           now() - make_interval(hours => $4), $5, now() + interval '1 hour', $6,
           now() + interval '30 days')`,
        [userId, clientId, name, index, randomUUID(), randomUUID()],
      );
    }
  });
}

/** Deletes a throwaway user's AI apps and connections that addAiConnections made, and the apps
 * a test registered itself (`clientIds`). */
export async function deleteAiConnections(userId: string, clientIds: string[] = []) {
  await withDatabase("assistant", async (client) => {
    await client.query("DELETE FROM mcp_grants WHERE user_id = $1", [userId]);
    // The tests' apps left without a connection (disconnected on the page or just now).
    await client.query(
      `DELETE FROM oauth_clients WHERE (client_id LIKE 'e2e-%' OR client_id = ANY($1))
         AND client_id NOT IN (SELECT client_id FROM mcp_grants)`,
      [clientIds],
    );
  });
}
