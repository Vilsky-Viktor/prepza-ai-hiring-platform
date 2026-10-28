"use client"

import { cn } from "cn"
import { CheckCheckIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"

import { WhatsAppIcon } from "@/components/chat-icons"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DEMO_CHAT,
  DEMO_OPENED,
  DEMO_PASS_MARK,
  DEMO_REPORT_CANDIDATES,
  DEMO_REPORT_COMPANY,
  DEMO_REPORT_INTERVIEW,
  DEMO_REPORT_TOPICS,
} from "@/config/reports-demo"
import { useReportTranslate } from "@/hooks/use-report-translate"
import { reportSummary } from "@/lib/report-summary"

const candidate = DEMO_REPORT_CANDIDATES[DEMO_OPENED]

// The opened candidate's report as the app gives it to the chat summary.
const REPORT = {
  company: DEMO_REPORT_COMPANY,
  logoUrl: null,
  verifiedDomain: null,
  title: DEMO_REPORT_INTERVIEW.title,
  email: candidate.email,
  name: candidate.name,
  grade: candidate.grade,
  passed: candidate.passed,
  passMark: DEMO_PASS_MARK,
  sections: DEMO_REPORT_TOPICS.map((topic) => ({
    id: topic.title,
    topic_title: topic.title,
    final_score: topic.grade,
    passed: topic.grade >= DEMO_PASS_MARK,
    tab_leaves: topic.tab_leaves,
    copies: topic.copies,
    fast_answers: topic.fast_answers,
  })),
}

/** A WhatsApp chat, small, for the landing: the chat's name, and the report's text summary as
 * the app writes it, sent in answer to the team's question, sliding in while `shown`. */
export function DemoChat({ shown }: { shown: boolean }) {
  const t = useTranslations("landing.shareReports")
  const translate = useReportTranslate()
  const locale = useLocale()

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3">
      <div className="flex items-center gap-3 px-1 pt-1">
        <WhatsAppIcon className="size-7 text-muted-foreground" />
        <Avatar>
          <AvatarFallback className="bg-surface text-xs">
            {DEMO_CHAT.initials}
          </AvatarFallback>
        </Avatar>
        <p className="font-medium">{DEMO_CHAT.name}</p>
      </div>
      <div className="flex min-h-0 flex-1 flex-col justify-end gap-2 overflow-hidden rounded-xl bg-surface p-3 sm:p-5">
        {/* The team's question, already there. */}
        <div className="max-w-[80%] self-start rounded-xl rounded-es-sm bg-background px-4 pt-3 pb-2">
          <p className="text-sm leading-relaxed">{t("chatQuestion")}</p>
          <p className="text-end text-xs text-muted-foreground">
            {DEMO_CHAT.asked}
          </p>
        </div>
        <div
          className={cn(
            "max-w-[92%] self-end rounded-xl rounded-ee-sm bg-background px-4 pt-3 pb-2 transition-[opacity,translate] delay-300 duration-500 sm:max-w-sm",
            !shown && "translate-y-3 opacity-0"
          )}
        >
          <p className="text-sm leading-relaxed whitespace-pre-line">
            {reportSummary(REPORT, translate, locale)}
          </p>
          <p className="flex items-center justify-end gap-1 text-xs text-muted-foreground">
            {DEMO_CHAT.time}
            <CheckCheckIcon className="size-4 text-primary" />
          </p>
        </div>
      </div>
    </div>
  )
}
