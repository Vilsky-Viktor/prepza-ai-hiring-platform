"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"

import { SHOWN_LINE_PROBLEMS } from "@/config/invites"
import type { BulkInviteResult } from "@/types/company"
import { bdi } from "@/lib/bidi"
import { hasMessage } from "@/lib/messages"

/** What the invite dialog couldn't do, in red: the API's refusal (`error`), each line it
 * couldn't use with its reason (the first few, then how many more), and why emails weren't
 * invited. Centered under a centered tab (`center`). Always in the page as a live region
 * (role="status"), so screen readers announce what appears in it; empty, it takes no room. */
export function InviteProblems({
  error,
  problems,
  skipped,
  center = false,
}: {
  error: string
  problems: BulkInviteResult["problems"]
  skipped: BulkInviteResult["skipped"]
  center?: boolean
}) {
  const t = useTranslations("interviews")
  const reasons = [...new Set(skipped.map((row) => row.reason))]
  const more = problems.length - SHOWN_LINE_PROBLEMS
  const rows = [
    ...(error ? [error] : []),
    ...problems.slice(0, SHOWN_LINE_PROBLEMS).map((row) => {
      const key = `lineProblems.${row.reason}` as const

      return hasMessage(t, key)
        ? t.rich(key, { line: row.line, ...bdi })
        : row.line
    }),
    ...(more > 0 ? [t("lineProblems.more", { count: more })] : []),
    ...reasons.map((reason) => {
      const key = `skip.${reason}` as const
      const count = skipped.filter((row) => row.reason === reason).length

      return hasMessage(t, key) ? t(key, { count }) : reason
    }),
  ]

  return (
    // Empty, it cancels the form's gap above it.
    <div role="status" className="empty:-mt-3">
      {rows.length > 0 && (
        <ul
          className={cn(
            "space-y-1 px-6 text-sm break-words text-destructive",
            center && "text-center"
          )}
        >
          {rows.map((row, index) => (
            <li key={index}>{row}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
