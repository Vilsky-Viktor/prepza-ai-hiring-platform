"use client"

import { UsersIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { Avatar, AvatarFallback, AvatarGroup } from "@/components/ui/avatar"
import { DEMO_INVITE_CANDIDATES } from "@/constants/invite-demo"

const { from, initials, shown } = DEMO_INVITE_CANDIDATES

/** An interview's candidates, `arrived` more than it started with: their count and the latest
 * few as initials, the newest sliding in first. */
export function ArrivingCandidates({ arrived }: { arrived: number }) {
  const t = useTranslations("landing.sources")
  // The latest few, newest first, each keyed by its place in the arrivals so the rest keep
  // theirs as one comes in.
  const latest = Array.from({ length: shown }, (_, at) => from + arrived - at)

  return (
    <div className="flex items-center justify-between gap-3 border-t pt-4">
      <span className="flex items-center gap-2 text-sm text-muted-foreground tabular-nums">
        <UsersIcon className="size-4 shrink-0" />
        {/* The number a little larger than its word, so it reads as it counts up. */}
        {t.rich("candidates", {
          count: from + arrived,
          n: (chunks) => (
            <span className="text-lg font-medium text-foreground">
              {chunks}
            </span>
          ),
        })}
      </span>
      <AvatarGroup>
        {latest.map((number, at) => (
          <Avatar
            key={number}
            className={
              at === 0 && arrived > 0
                ? "animate-in duration-500 fade-in slide-in-from-left-3 motion-reduce:animate-none rtl:slide-in-from-right-3"
                : undefined
            }
          >
            <AvatarFallback className="bg-background text-xs">
              {initials[number % initials.length]}
            </AvatarFallback>
          </Avatar>
        ))}
      </AvatarGroup>
    </div>
  )
}
