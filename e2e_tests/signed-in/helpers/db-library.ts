import { withDatabase } from "./db";

/** A throwaway template with one topic of `questions` questions in `pool`, saved straight into
 * the library database (a real one needs an OpenAI generation). A company can copy it only with
 * at least 10 company questions (MIN_COPY_QUESTIONS in services/library); practice uses only
 * practice ones. German, so
 * nothing that picks English templates to make interviews from (templatesBySize, the load
 * tests) takes it. Its right answers hold `inline code`. Its `level` gives a company's test
 * made from it its seconds a question. */
export async function addTemplate(
  title: string,
  questions: number,
  pool: "company" | "practice" = "company",
  level: "basic" | "medium" | "hard" = "basic",
): Promise<string> {
  return withDatabase("library", async (client) => {
    const set = await client.query(
      `INSERT INTO sets (id, kind, owner_type, owner_id, title, source_text, level, language,
         requirements, topic_count, created_at)
       VALUES (gen_random_uuid(), 'template', 'platform', 'prepza', $1, 'E2E', $2, 'de',
         '[]', 1, now())
       RETURNING id`,
      [title, level],
    );
    const id = set.rows[0].id;
    const topic = await client.query(
      `INSERT INTO topics (id, set_id, position, title, subtopics)
       VALUES (gen_random_uuid(), $1, 0, 'E2E topic', '[]') RETURNING id`,
      [id],
    );
    const options = JSON.stringify([
      { answer: "Check `if is_member:` first", correct: true },
      { answer: "Skip the check", correct: false },
    ]);

    for (let position = 0; position < questions; position++) {
      await client.query(
        `INSERT INTO questions (id, topic_id, position, text, options, stage, pool)
         VALUES (gen_random_uuid(), $1, $2, $3, $4, 'private', $5)`,
        [topic.rows[0].id, position, `E2E question ${position + 1}?`, options, pool],
      );
    }

    return id;
  });
}

/** Deletes a template addTemplate made; its topics and questions go with it, and the companies'
 * copies stay. */
export async function deleteTemplate(id: string) {
  await withDatabase("library", (client) =>
    client.query("DELETE FROM sets WHERE id = $1", [id]),
  );
}

/** Keeps `oldText` as a replaced version of the first question of a template addTemplate made,
 * as the verifier does when it replaces a question (that needs OpenAI). Deleting the template
 * deletes it too. */
export async function addReplacedVersion(templateId: string, oldText: string) {
  await withDatabase("library", (client) =>
    client.query(
      `INSERT INTO question_revisions (id, question_id, text, options, answers, correct,
         option_picks, likes, dislikes, reports, replaced_at)
       SELECT gen_random_uuid(), q.id, $2, '[{"answer": "Old right", "correct": true},
         {"answer": "Old wrong", "correct": false}]', 4, 1, '{}', 0, 3, '[]', now()
       FROM questions q JOIN topics t ON t.id = q.topic_id
       WHERE t.set_id = $1 AND q.position = 0`,
      [templateId, oldText],
    ),
  );
}

/** `count` finished practice rounds of a throwaway user on `templateId`, one a day apart
 * (the newest now), saved straight into the rounds database; deleting the account deletes
 * them. */
export async function addPracticeRounds(
  userId: string,
  templateId: string,
  count: number,
) {
  await withDatabase("rounds", async (client) => {
    for (let index = 0; index < count; index++) {
      await client.query(
        `INSERT INTO sessions (id, user_id, topic_id, interview_set_id, candidate_invite_id,
           topic_title, status, questions, final_score, started_at, finished_at, preview, practice)
         VALUES (gen_random_uuid(), $1, gen_random_uuid(), $2, gen_random_uuid(), 'E2E topic',
           'finished', '[{}, {}]', NULL, now() - make_interval(days => $3),
           now() - make_interval(days => $3), false, true)`,
        [userId, templateId, index],
      );
    }
  });
}

// A multi-answer ("select all that apply") question of multiAnswerTemplate's: three of its four
// options are right, so ticking two of them and nothing wrong earns two thirds of its point.
export const MULTI_QUESTION = "E2E: which of these are prime numbers?";
export const MULTI_RIGHT = ["2", "3", "5"];
export const MULTI_WRONG = "9";

/** A throwaway template with one topic: `company` questions companies copy and `practice` ones
 * for free practice, a third of each multi-answer (MULTI_QUESTION, numbered after the first),
 * the rest single-answer with four options; saved straight into the library database, as
 * addTemplate's. With 15 of each, a draw of 10 holds exactly its share (1 at 10%), so the
 * question after the multi-answer one is single-answer. */
export async function multiAnswerTemplate(
  title: string,
  company = 15,
  practice = 15,
): Promise<string> {
  return withDatabase("library", async (client) => {
    const set = await client.query(
      `INSERT INTO sets (id, kind, owner_type, owner_id, title, source_text, level, language,
         requirements, topic_count, created_at)
       VALUES (gen_random_uuid(), 'template', 'platform', 'prepza', $1, 'E2E', 'basic', 'de',
         '[]', 1, now())
       RETURNING id`,
      [title],
    );
    const id = set.rows[0].id;
    const topic = await client.query(
      `INSERT INTO topics (id, set_id, position, title, subtopics)
       VALUES (gen_random_uuid(), $1, 0, 'E2E topic', '[]') RETURNING id`,
      [id],
    );
    const single = JSON.stringify([
      { answer: "Right", correct: true },
      { answer: "Wrong one", correct: false },
      { answer: "Wrong two", correct: false },
      { answer: "Wrong three", correct: false },
    ]);
    const multi = JSON.stringify([
      ...MULTI_RIGHT.map((answer) => ({ answer, correct: true })),
      { answer: MULTI_WRONG, correct: false },
    ]);
    const pools = [
      ...Array(company).fill("company"),
      ...Array(practice).fill("practice"),
    ];

    for (const [position, pool] of pools.entries()) {
      const isMulti = position % 3 === 0;
      const text = isMulti
        ? `${MULTI_QUESTION} (${position + 1})`
        : `E2E question ${position + 1}?`;
      await client.query(
        `INSERT INTO questions (id, topic_id, position, text, options, stage, pool)
         VALUES (gen_random_uuid(), $1, $2, $3, $4, 'private', $5)`,
        [topic.rows[0].id, position, text, isMulti ? multi : single, pool],
      );
    }

    return id;
  });
}

/** Adds `extra` to the end of every question of a template addTemplate made, before a company
 * copies it, so its questions run long. */
export async function lengthenQuestions(templateId: string, extra: string) {
  await withDatabase("library", (client) =>
    client.query(
      `UPDATE questions q SET text = q.text || ' ' || $2
       FROM topics t WHERE t.id = q.topic_id AND t.set_id = $1`,
      [templateId, extra],
    ),
  );
}
