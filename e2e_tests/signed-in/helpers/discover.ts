import type { Page } from "@playwright/test"

import { api } from "./api"
import { withDatabase } from "./db"
import { addTemplate } from "./db-library"

type Interview = { set_id: string }

/** Makes a throwaway company one that has topped up, as Discover asks billing: a purchase row,
 * which outlives the company (bookkeeping), so the test removes it with unmarkPaid. */
export async function markPaid(companyId: string) {
  await withDatabase("billing", (client) =>
    client.query(
      `INSERT INTO purchases (id, transaction_id, product, quantity, owner_type, owner_id,
         currency, total_minor)
       VALUES (gen_random_uuid(), $1, 'topup_50', 50, 'company', $2, 'USD', 10000)`,
      [`txn_e2e${companyId.replaceAll("-", "")}`, companyId]
    )
  )
}

/** Removes the purchase markPaid made. */
export async function unmarkPaid(companyId: string) {
  await withDatabase("billing", (client) =>
    client.query("DELETE FROM purchases WHERE owner_type = 'company' AND owner_id = $1", [
      companyId,
    ])
  )
}

/** A throwaway practice template whose one topic matches the interview's first topic, as
 * Discover matches them (library's practice_matches.py): the interview's level, and both topics
 * given the same embedding, one no real topic is near, so only the test's own template matches
 * (the embedding job, which needs OpenAI, fills only topics that have none). Deleting the
 * template and the company removes both. */
export async function matchingTemplate(owner: Page, interviewId: string) {
  const { set_id: setId } = await api<Interview>(
    owner,
    "GET",
    `/companies/interviews/${interviewId}`
  )
  const templateId = await addTemplate("E2E open to offers", 3, "practice")
  const topicId = await withDatabase("library", async (client) => {
    const column = await client.query(
      `SELECT format_type(atttypid, atttypmod) AS type FROM pg_attribute
       WHERE attrelid = 'topics'::regclass AND attname = 'embedding'`
    )
    const dimensions = Number(/\((\d+)\)/.exec(column.rows[0].type)![1])
    const embedding = `[${Array(dimensions).fill("-0.5").join(",")}]`
    await client.query(
      "UPDATE sets SET level = (SELECT level FROM sets WHERE id = $1) WHERE id = $2",
      [setId, templateId]
    )
    await client.query(
      `UPDATE topics SET embedding = $3 WHERE id IN (
         (SELECT id FROM topics WHERE set_id = $1 ORDER BY position LIMIT 1),
         (SELECT id FROM topics WHERE set_id = $2))`,
      [setId, templateId, embedding]
    )
    const topic = await client.query("SELECT id FROM topics WHERE set_id = $1", [templateId])

    return topic.rows[0].id as string
  })

  return { templateId, topicId }
}

/** A finished, timed practice round of the user's on the template's topic with this grade
 * (0–100), saved straight into the rounds database, as a round played through the app ends;
 * its id, the round's page's. */
export async function addPracticeResult(
  userId: string,
  templateId: string,
  topicId: string,
  score: number
): Promise<string> {
  return withDatabase("rounds", async (client) => {
    const round = await client.query(
      `INSERT INTO sessions (id, user_id, topic_id, interview_set_id, candidate_invite_id,
         topic_title, status, questions, final_score, question_seconds, started_at, finished_at,
         preview, practice)
       VALUES (gen_random_uuid(), $1, $2, $3, gen_random_uuid(), 'E2E topic', 'finished', '[]',
         $4, 30, now(), now(), false, true)
       RETURNING candidate_invite_id`,
      [userId, topicId, templateId, score]
    )

    return round.rows[0].candidate_invite_id as string
  })
}

/** The user's practice rounds on the template, which deleting the template leaves behind. */
export async function deletePracticeResults(userId: string, templateId: string) {
  await withDatabase("rounds", (client) =>
    client.query("DELETE FROM sessions WHERE user_id = $1 AND interview_set_id = $2", [
      userId,
      templateId,
    ])
  )
}

/** Turns Open to offers on for the user signed in on `page`, with this LinkedIn profile, as the
 * card does: with the wording's version the API gives. */
export async function openToOffers(page: Page, linkedin: string) {
  const { consent_version } = await api<{ consent_version: string }>(
    page,
    "GET",
    "/rounds/open-to-offers"
  )
  await api(page, "PUT", "/rounds/open-to-offers", {
    linkedin_url: linkedin,
    consent_version,
  })
}

/** The ids of the people an interview's Discover tab lists, read as its owner. */
export async function discovered(owner: Page, interviewId: string) {
  const people = await api<{ id: string }[]>(
    owner,
    "GET",
    `/companies/interviews/${interviewId}/discover?limit=100`
  )

  return people.map((person) => person.id)
}
