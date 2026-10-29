import { randomBytes, randomUUID } from "node:crypto";

import pg from "pg";

import { env } from "./env";

// The stack's Postgres on its network (pages.sh runs the tests there).
const POSTGRES_HOST = "postgres";

export type Template = { id: string; slug: string; title: string; language: string };

// What a stopped run left behind goes once it's older than this, longer than a whole run takes,
// so runs at the same time keep each other's.
const STALE = "6 hours";

/** Runs `work` on a fresh connection to one of the stack's databases. */
async function withDatabase<T>(database: string, work: (client: pg.Client) => Promise<T>) {
  const client = new pg.Client({
    host: POSTGRES_HOST,
    user: "prepza",
    password: env("POSTGRES_PASSWORD"),
    database,
  });
  await client.connect();

  try {
    return await work(client);
  } finally {
    await client.end();
  }
}

/** A throwaway template with its own readable address, saved straight into the library database
 * (a real one needs an OpenAI generation). Each topic has a subtopic, two company questions and
 * one practice one. Its title is unique, so with at least 3 topics (MIN_INDEXABLE_TOPICS in
 * services/library) it's indexable, and with fewer it isn't. */
export async function addTemplate(language: string, topics: number): Promise<Template> {
  const key = randomUUID().slice(0, 8);
  const title = `E2E role ${key}`;
  const slug = `e2e-${key}`;

  return withDatabase("library", async (client) => {
    const set = await client.query(
      `INSERT INTO sets (id, kind, owner_type, owner_id, title, slug, source_text, level,
         language, requirements, topic_count, created_at)
       VALUES (gen_random_uuid(), 'template', 'platform', 'prepza', $1, $2, 'E2E', 'basic', $3,
         '[]', $4, now())
       RETURNING id`,
      [title, slug, language, topics],
    );
    const id = set.rows[0].id;
    const options = JSON.stringify([
      { answer: "Right", correct: true },
      { answer: "Wrong", correct: false },
    ]);

    for (let position = 0; position < topics; position++) {
      const topic = await client.query(
        `INSERT INTO topics (id, set_id, position, title, subtopics)
         VALUES (gen_random_uuid(), $1, $2, $3, '["E2E subtopic"]') RETURNING id`,
        [id, position, `E2E topic ${position + 1}`],
      );

      for (const [index, pool] of ["company", "company", "practice"].entries()) {
        await client.query(
          `INSERT INTO questions (id, topic_id, position, text, options, stage, pool)
           VALUES (gen_random_uuid(), $1, $2, $3, $4, 'private', $5)`,
          [topic.rows[0].id, index, `E2E question ${index + 1}?`, options, pool],
        );
      }
    }

    return { id, slug, title, language };
  });
}

/** Deletes a template addTemplate made; its topics and questions go with it. */
export async function deleteTemplate(id: string) {
  await withDatabase("library", (client) => client.query("DELETE FROM sets WHERE id = $1", [id]));
}

/** A throwaway news post published today, saved straight into the site database; its id. */
export async function addNewsPost(): Promise<string> {
  const key = randomUUID().slice(0, 8);

  return withDatabase("site", async (client) => {
    const post = await client.query(
      `INSERT INTO news (id, title, text, published_on)
       VALUES (gen_random_uuid(), $1, 'E2E', current_date) RETURNING id`,
      [`E2E news ${key}`],
    );

    return post.rows[0].id;
  });
}

/** Deletes a post addNewsPost made; its translations go with it. */
export async function deleteNewsPost(id: string) {
  await withDatabase("site", (client) => client.query("DELETE FROM news WHERE id = $1", [id]));
}

// Made-up companies' ids: uuids, as the opt-outs keep them, that no real company is given.
const MADE_UP_COMPANY = "00000000-e2e0-4000-8000-";

/** A made-up company's id of a test's own. */
export function madeUpCompanyId() {
  return `${MADE_UP_COMPANY}${randomBytes(6).toString("hex")}`;
}

/** Deletes the opt-outs a made-up company's unsubscribe link left (never a real id). */
export async function deleteOptOuts(companyId: string) {
  await withDatabase("notifications", (client) =>
    client.query("DELETE FROM candidate_opt_outs WHERE company_id = $1", [companyId]),
  );
}

/** Deletes what stopped runs left: their templates, news posts and made-up companies' opt-outs. */
export async function deleteLeftovers() {
  await withDatabase("library", (client) =>
    client.query(
      `DELETE FROM sets WHERE kind = 'template' AND owner_type = 'platform'
         AND slug LIKE 'e2e-%' AND source_text = 'E2E' AND created_at < now() - $1::interval`,
      [STALE],
    ),
  );
  await withDatabase("site", (client) =>
    client.query(
      `DELETE FROM news WHERE title LIKE 'E2E news %' AND text = 'E2E'
         AND created_at < now() - $1::interval`,
      [STALE],
    ),
  );
  await withDatabase("notifications", (client) =>
    client.query(
      "DELETE FROM candidate_opt_outs WHERE company_id::text LIKE $1 AND created_at < now() - $2::interval",
      [`${MADE_UP_COMPANY}%`, STALE],
    ),
  );
}
