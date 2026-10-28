import type { CandidateReportData, InterviewReportData } from "@/types/company"

// Made-up data for the landing's report samples (scripts/report-samples.sh): no real company or
// person. The company's name says it's an example, so the PDFs do too.
const COMPANY = "Acme Hiring (example)"
const TITLE = "Backend Developer"
const PASS_MARK = 70
const CREATED_AT = "2026-10-01T09:00:00Z"

/** One candidate's report, as the candidate's page builds it from their scorecard. */
export const CANDIDATE_SAMPLE: CandidateReportData = {
  company: COMPANY,
  logoUrl: null,
  verifiedDomain: null,
  title: TITLE,
  email: "alex.morgan@example.com",
  name: "Alex Morgan",
  grade: 77,
  passed: true,
  passMark: PASS_MARK,
  sections: [
    topic("1", "HTTP APIs and REST", 88, {}),
    topic("2", "Databases and SQL", 76, {}),
    topic("3", "Concurrency and async code", 64, { fast_answers: 2 }),
    topic("4", "Testing and debugging", 82, { tab_leaves: 1 }),
    topic("5", "System design basics", 74, {}),
  ],
}

/** The report of all the test's candidates, best grade first and those without one after, as
 * the API returns it. */
export const INTERVIEW_SAMPLE: InterviewReportData = {
  title: TITLE,
  company: COMPANY,
  logo_url: null,
  verified_domain: null,
  pass_mark: PASS_MARK,
  candidates: [
    candidate("a1", "priya.shah@example.com", "Priya Shah", 91, {}),
    candidate("a2", "alex.morgan@example.com", "Alex Morgan", 77, {
      tab_leaves: 1,
      fast_answers: 2,
    }),
    candidate("a3", "daniel.kim@example.com", "Daniel Kim", 72, {}),
    candidate("a4", "sofia.rossi@example.com", "Sofia Rossi", 63, {
      copies: 1,
    }),
    candidate("a5", "liam.oconnor@example.com", "Liam O'Connor", 48, {}),
    candidate("a6", "noah.becker@example.com", "Noah Becker", null, {
      progress: 40,
    }),
    candidate("a7", "emma.lopez@example.com", null, null, { progress: 0 }),
  ],
}

type Signals = { tab_leaves?: number; copies?: number; fast_answers?: number }

function topic(id: string, title: string, score: number, signals: Signals) {
  return {
    id,
    topic_title: title,
    final_score: score,
    passed: score >= PASS_MARK,
    tab_leaves: 0,
    copies: 0,
    fast_answers: 0,
    ...signals,
  }
}

function candidate(
  id: string,
  email: string,
  name: string | null,
  grade: number | null,
  extra: Signals & { progress?: number }
) {
  const progress = extra.progress ?? 100

  return {
    id,
    email,
    name,
    status: grade == null ? (progress ? "in_process" : "invited") : "finished",
    progress,
    grade,
    passed: grade == null ? null : grade >= PASS_MARK,
    tab_leaves: 0,
    copies: 0,
    fast_answers: 0,
    flagged: false,
    extra_time: 0,
    can_resend: false,
    revokable: false,
    created_at: CREATED_AT,
    ...extra,
  }
}
