import { describe, expect, it } from "vitest"

import { candidateReportData } from "@/lib/candidate-report-data"
import type { Scorecard } from "@/types/company"

const card = {
  id: "i1",
  email: "ann@example.com",
  name: "Ann",
  status: "finished",
  extra_time: 0,
  extra_time_options: [],
  can_edit: true,
  can_resend: false,
  revokable: false,
  invite_token: null,
  title: "Backend",
  company: "Acme",
  logo_url: null,
  verified_domain: null,
  grade: 80,
  passed: true,
  pass_mark: 70,
  language: "ar",
  pledged_at: null,
  sessions: [
    {
      id: "s1",
      topic_title: "SQL",
      status: "finished",
      final_score: 80,
      passed: true,
      tab_leaves: 1,
      copies: 0,
      fast_answers: 2,
      review: [],
    },
  ],
} satisfies Scorecard

describe("candidateReportData", () => {
  it("keeps the result and the interview's language, never the questions", () => {
    const report = candidateReportData(card)

    expect(report.language).toBe("ar")
    expect(report.passMark).toBe(70)
    expect(report.sections).toEqual([
      {
        id: "s1",
        topic_title: "SQL",
        final_score: 80,
        passed: true,
        tab_leaves: 1,
        copies: 0,
        fast_answers: 2,
      },
    ])
  })
})
