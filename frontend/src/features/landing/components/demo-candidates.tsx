"use client"

import { cn } from "cn"

import { DemoCandidateSearch } from "@/features/landing/components/demo-candidate-search"
import { DemoInterviewTabs } from "@/features/landing/components/demo-interview-tabs"
import { DemoReportActions } from "@/features/landing/components/demo-share"
import { InterviewHeader } from "@/features/landing/components/interview-header"
import { CandidateRow } from "@/components/common/candidate-row"
import { SearchedList } from "@/components/common/searched-list"
import {
  DEMO_CANDIDATE_COUNT,
  DEMO_NOTE_COUNT,
  DEMO_REPORT_CANDIDATES,
  DEMO_REPORT_INTERVIEW,
} from "@/config/reports-demo"

/** An interview's candidates tab, for the landing: its header with the report's actions (the
 * one `pressed` pressed in), its tabs, and the candidates as the real list's rows, with their
 * grades and integrity signals; the row `opened` (its place) shaded as it's clicked. Each row is
 * the pointer's "row<place>". */
export function DemoCandidates({
  pressed,
  opened,
}: {
  pressed: "download" | "share" | null
  opened: number | null
}) {
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <div className="flex items-start justify-between gap-2">
        <InterviewHeader {...DEMO_REPORT_INTERVIEW} status="in_process" />
        <DemoReportActions pressed={pressed} />
      </div>
      <DemoInterviewTabs
        current="candidates"
        counts={{
          topics: DEMO_REPORT_INTERVIEW.topics,
          candidates: DEMO_CANDIDATE_COUNT,
          notes: DEMO_NOTE_COUNT,
        }}
      />
      {/* Cut off at the picture's bottom, as a long list is. */}
      <div className="min-h-0 overflow-hidden">
        <SearchedList>
          <DemoCandidateSearch />
          <ul className="min-h-0 divide-y overflow-hidden rounded-xl border searched:rounded-t-none searched:border-t-0">
            {DEMO_REPORT_CANDIDATES.map((candidate, index) => (
              <li
                key={candidate.email}
                data-demo-target={`row${index}`}
                className={cn(
                  "transition-colors [&_a>span]:py-3",
                  opened === index && "bg-surface"
                )}
              >
                <CandidateRow candidate={candidate} href="#reports" />
              </li>
            ))}
          </ul>
        </SearchedList>
      </div>
    </div>
  )
}
