"use client"

import { cn } from "cn"
import Link from "next/link"
import { useFormatter, useLocale, useTranslations } from "next-intl"

import { useLocalTime } from "@/hooks/use-local-time"
import { InvoiceLink } from "@/features/billing/components/invoice-link"
import { Dotted } from "@/components/common/dot"
import { candidateHref, type CandidateLinks } from "@/lib/candidate-links"
import { formatPrice } from "@/lib/format"
import { hasMessage } from "@/lib/messages"
import type { CreditHistoryEntry } from "@/types/company"
import { ROW_HOVER } from "@/config/lists"

/** One movement of a company's credits: what it was, when, and the credits it moved; a top-up
 * with what was paid and its invoice, a candidate's charge with the candidate and their test,
 * an adjustment with why. `api` is the company's billing routes; `links` is where a charge's
 * candidate opens (the company's page, or the admin zone's support page). */
export function HistoryRow({
  companyId,
  entry,
  api,
  links,
}: {
  companyId: string
  entry: CreditHistoryEntry
  api: string
  links: CandidateLinks
}) {
  const t = useTranslations("companyBilling")
  const format = useFormatter()
  const locale = useLocale()
  const localTime = useLocalTime()
  const candidate = entry.candidate
  const reason = `reasons.${entry.reason}` as const

  const content = (
    // On phones the amount goes under the rest, everything centered.
    <span className="flex items-center justify-between gap-4 p-6 max-sm:flex-col max-sm:text-center">
      <span className="min-w-0 space-y-1">
        {/* A candidate's charge leads with the candidate, like the candidate lists. */}
        <span className="block text-lg font-medium break-all normal-case">
          {candidate
            ? (candidate.name ?? candidate.email)
            : hasMessage(t, reason)
              ? t(reason)
              : entry.reason}
        </span>
        {candidate && (
          <span className="block text-sm break-all text-muted-foreground normal-case">
            <Dotted
              items={[
                candidate.name && candidate.email,
                candidate.interview_title,
              ]}
            />
          </span>
        )}
        {entry.note && (
          <span className="block text-sm break-words text-muted-foreground normal-case">
            {entry.note}
          </span>
        )}
        {entry.candidate_deleted && (
          <span className="block text-sm text-muted-foreground">
            {t("deletedCandidate")}
          </span>
        )}
        <span className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground max-sm:justify-center">
          <time dateTime={entry.created_at} suppressHydrationWarning>
            {localTime.date(entry.created_at)}
          </time>
          {entry.total != null && entry.currency && (
            <span className="tabular-nums">
              {formatPrice(Number(entry.total), entry.currency, locale)}
            </span>
          )}
          {entry.automatic && <span>{t("automatic")}</span>}
          {entry.invoice_id && (
            <InvoiceLink api={api} transactionId={entry.invoice_id} />
          )}
        </span>
      </span>
      <span
        className={cn(
          "shrink-0 font-heading text-2xl font-medium tabular-nums",
          entry.amount > 0 && "text-primary"
        )}
      >
        {format.number(entry.amount, { signDisplay: "exceptZero" })}
      </span>
    </span>
  )

  // A candidate's charge opens the candidate.
  return candidate ? (
    <Link
      href={candidateHref(links, companyId, candidate)}
      className={`block ${ROW_HOVER}`}
    >
      {content}
    </Link>
  ) : (
    content
  )
}
