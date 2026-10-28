import type { CandidateReportData, Scorecard } from "@/types/company"

/** What a candidate's PDF report shows, from their scorecard: never the questions. */
export function candidateReportData(card: Scorecard): CandidateReportData {
  return {
    company: card.company,
    logoUrl: card.logo_url,
    verifiedDomain: card.verified_domain,
    title: card.title,
    email: card.email,
    name: card.name,
    grade: card.grade,
    passed: card.passed,
    passMark: card.pass_mark,
    language: card.language,
    sections: card.sessions.map((session) => ({
      id: session.id,
      topic_title: session.topic_title,
      final_score: session.final_score,
      passed: session.passed,
      tab_leaves: session.tab_leaves,
      copies: session.copies,
      fast_answers: session.fast_answers,
    })),
  }
}
