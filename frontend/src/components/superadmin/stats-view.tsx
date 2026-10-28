"use client"

import { useEffect, useState } from "react"

import { StatsCards } from "@/components/superadmin/stats-cards"
import { StatsPicker } from "@/components/superadmin/stats-picker"
import { STATS_SOURCES } from "@/config/stats"
import { useStatsChoice } from "@/hooks/use-stats-choice"
import { apiFetch } from "@/lib/api"
import type { Stats } from "@/types/superadmin"

type Source = (typeof STATS_SOURCES)[number]

/** The stats tab: the choice the browser kept from last time (this month at first), and each
 * service's numbers for it, asked again whenever the choice changes. A service that doesn't
 * answer leaves its cards with a dash. */
export function StatsView() {
  const { choice, query, change } = useStatsChoice()
  const [stats, setStats] = useState<Record<Source, Stats | null> | null>(null)

  useEffect(() => {
    if (query === null) {
      return
    }

    let current = true

    Promise.all(
      STATS_SOURCES.map((source) =>
        apiFetch<Stats>(`/${source}/superadmin/stats${query}`).catch(() => null)
      )
    ).then(([library, companies, rounds, billing]) => {
      if (current) {
        setStats({ library, companies, rounds, billing })
      }
    })

    return () => {
      current = false
    }
  }, [query])

  return (
    <div className="space-y-4">
      {choice && <StatsPicker choice={choice} onChange={change} />}
      <StatsCards
        stats={
          stats ?? {
            library: null,
            companies: null,
            rounds: null,
            billing: null,
          }
        }
      />
    </div>
  )
}
