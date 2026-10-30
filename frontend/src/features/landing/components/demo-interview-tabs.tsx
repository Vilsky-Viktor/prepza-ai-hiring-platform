"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"

import { MenuCount } from "@/components/common/menu-count"
import { CURRENT_TAB } from "@/config/tab-nav"

const TABS = ["topics", "candidates", "notes"] as const

/** An interview's tabs as the site's tabs show them (components/common/tab-nav.tsx), for the
 * landing: topics, candidates and notes with their `counts`, the `current` one open; `notes` is
 * the pointer's "notesTab". */
export function DemoInterviewTabs({
  current,
  counts,
}: {
  current: (typeof TABS)[number]
  counts: Partial<Record<(typeof TABS)[number], number>>
}) {
  const t = useTranslations("interviews")
  const labels = {
    topics: t("topicsTab"),
    candidates: t("candidates"),
    notes: t("notes"),
  }

  return (
    <span className="flex gap-6 border-b px-1">
      {TABS.map((tab) => (
        <span
          key={tab}
          data-demo-target={tab === "notes" ? "notesTab" : undefined}
          className={cn(
            "-mb-px flex items-center gap-2 border-b-2 pb-2 text-base whitespace-nowrap lowercase",
            tab === current
              ? CURRENT_TAB
              : "border-transparent text-muted-foreground"
          )}
        >
          {labels[tab]}
          <MenuCount count={counts[tab]} />
        </span>
      ))}
    </span>
  )
}
