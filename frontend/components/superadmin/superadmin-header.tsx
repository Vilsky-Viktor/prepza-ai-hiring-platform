"use client"

import { cn } from "cn"
import Link from "next/link"
import { useTranslations } from "next-intl"
import type { ReactNode } from "react"

import { TabNav } from "@/components/tab-nav"

// The tabs with tabs of their own: each one's path under its tab and its label's message.
const SUBTABS = {
  questions: [
    { id: "flagged", label: "flagged" },
    { id: "replaced", label: "replaced" },
    { id: "patterns", label: "patterns" },
  ],
  stats: [
    { id: "general", label: "statsGeneral" },
    { id: "ai-costs", label: "aiCosts" },
  ],
} as const

/** The admin zone's title and tabs, as a company's pages have them, with `action` on the right.
 * Questions and stats have their own row of tabs under them: `sub` is the one open. */
export function SuperadminHeader({
  current,
  sub,
  action,
}: {
  current:
    | "templates"
    | "questions"
    | "pass-rates"
    | "verification"
    | "support"
    | "stats"
    | "controls"
    | "news"
    | "campaigns"
  sub?: "flagged" | "replaced" | "patterns" | "general" | "ai-costs"
  action?: ReactNode
}) {
  const t = useTranslations("superadmin")

  return (
    <div className="space-y-4">
      {/* On phones the action takes its own line under the title, at full width. */}
      <div className="flex min-h-14 items-center max-sm:flex-wrap">
        <h1 className="min-w-0 flex-1 font-heading text-3xl font-medium tracking-tight max-sm:basis-full">
          {t("zone")}
        </h1>
        {action && (
          <div className="max-sm:my-4 max-sm:basis-full max-sm:*:w-full">
            {action}
          </div>
        )}
      </div>
      <TabNav
        items={[
          {
            id: "templates",
            href: "/superadmin/templates",
            label: t("templates"),
          },
          { id: "news", href: "/superadmin/news", label: t("news") },
          {
            id: "campaigns",
            href: "/superadmin/campaigns",
            label: t("campaigns"),
          },
          {
            id: "questions",
            href: "/superadmin/questions/flagged",
            label: t("questions"),
          },
          {
            id: "pass-rates",
            href: "/superadmin/pass-rates",
            label: t("passRates"),
          },
          {
            id: "verification",
            href: "/superadmin/verification",
            label: t("verification"),
          },
          {
            id: "support",
            href: "/superadmin/support",
            label: t("support"),
          },
          {
            id: "stats",
            href: "/superadmin/stats/general",
            label: t("stats"),
          },
          {
            id: "controls",
            href: "/superadmin/controls",
            label: t("controls"),
          },
        ]}
        current={current}
      />
      {sub && (current === "questions" || current === "stats") && (
        // The open tab's own tabs: pills on a band of the row's line colour, softened, hanging
        // from that line, so they read as part of the row; the open one in the page's colour.
        <nav
          aria-label={t(current)}
          className="-mt-4 flex gap-2 rounded-b-2xl bg-border/50 p-2"
        >
          {SUBTABS[current].map(({ id, label }) => (
            <Link
              key={id}
              href={`/superadmin/${current}/${id}`}
              aria-current={id === sub ? "page" : undefined}
              className={cn(
                "rounded-full px-4 py-1.5 text-base lowercase transition-colors",
                id === sub
                  ? "bg-background text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {t(label)}
            </Link>
          ))}
        </nav>
      )}
    </div>
  )
}
