import { withDatabase } from "./db";

type Question = { id: string; seconds: number; difficulty?: number | null };

const HARD = 0.2;
const EASY = 0.9;

/** Reshapes a finished candidate's answers (only the test's own invite) into a pattern, as the
 * answer-pattern signals read it: `relayed`, every question's difficulty known (every other one
 * hard), the hard ones right and the easy ones wrong, in a flat 24-30 s that runs against what
 * each question predicts across all their sections, the longest the quickest; otherwise the
 * first half of each section's answers right, in times that follow each question's own time, and
 * no difficulty known. Returns the ids of the questions answered right. */
export async function shapeAnswers(inviteId: string, relayed: boolean): Promise<string[]> {
  return withDatabase("rounds", async (client) => {
    const sessions = await client.query<{ id: string; questions: Question[] }>(
      "SELECT id, questions FROM sessions WHERE candidate_invite_id = $1",
      [inviteId],
    );
    const right: string[] = [];
    // Every question with its section, difficulty set; the times run across all of them.
    const all = sessions.rows.flatMap((session) =>
      session.questions.map((question, index) => ({
        session: session.id,
        question: {
          ...question,
          difficulty: relayed ? (index % 2 ? HARD : EASY) : null,
        },
        first: index < session.questions.length / 2,
      })),
    );
    // What rounds expects of each: its own time, longer the harder it is.
    const expected = (question: Question) =>
      question.seconds * (2 - (question.difficulty ?? 1));
    const byTime = [...all].sort((a, b) => expected(a.question) - expected(b.question));
    const last = Math.max(1, byTime.length - 1);

    for (const [position, { session, question, first }] of byTime.entries()) {
      const correct = relayed ? question.difficulty === HARD : first;
      const seconds = relayed
        ? 30 - Math.round((6 * position) / last)
        : Math.max(3, Math.round(question.seconds * 0.6));

      if (correct) {
        right.push(question.id);
      }

      await client.query(
        `UPDATE answers SET correct = $3, score = $4, seconds = $5, timed_out = false
         WHERE session_id = $1 AND question_id = $2`,
        [session, question.id, correct, correct ? 100 : 0, seconds],
      );
    }

    for (const session of sessions.rows) {
      const questions = all
        .filter((item) => item.session === session.id)
        .map((item) => item.question);
      await client.query("UPDATE sessions SET questions = $2 WHERE id = $1", [
        session.id,
        JSON.stringify(questions),
      ]);
    }

    return right;
  });
}
