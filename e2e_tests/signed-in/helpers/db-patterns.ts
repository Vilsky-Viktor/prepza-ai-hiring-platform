import { randomUUID } from "node:crypto";

import { withDatabase } from "./db";

// How many questions showed each pattern the helpers add.
export const PATTERN_QUESTIONS = 913;

/** Patterns of `status` (proposed by default), saved straight into generation's quality_patterns
 * as the weekly job saves them (a real run costs OpenAI money), seen a day ahead so they lead the
 * tab's lists; one in use carries `evalRun`, the eval gate's run. Each text ends with `marker`, a
 * random id; deletePatterns deletes them. */
export async function addPatterns(
  marker: string,
  count: number,
  status = "proposed",
  evalRun: string | null = null,
) {
  const texts = Array.from({ length: count }, (_, index) => `Rule ${status} ${index} ${marker}.`);

  await withDatabase("generation", async (client) => {
    for (const text of texts) {
      await client.query(
        `INSERT INTO quality_patterns (id, text, flag, question_count, first_seen, last_seen,
           status, eval_run)
         VALUES ($1, $2, 'weak_options', $3, now() + interval '1 day', now() + interval '1 day', $4,
           $5)`,
        [randomUUID(), text, PATTERN_QUESTIONS, status, evalRun],
      );
    }
  });

  return texts;
}

/** A pattern's status and who reviewed it, by its text. */
export async function patternStatus(text: string) {
  return withDatabase("generation", async (client) => {
    const found = await client.query(
      "SELECT status, reviewed_by FROM quality_patterns WHERE text = $1",
      [text],
    );

    return found.rows[0] as { status: string; reviewed_by: string | null };
  });
}

export async function deletePatterns(marker: string) {
  await withDatabase("generation", (client) =>
    client.query("DELETE FROM quality_patterns WHERE text LIKE $1", [`% ${marker}.`]),
  );
}
