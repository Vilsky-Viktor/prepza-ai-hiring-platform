"use client"

import { useEffect, useState } from "react"

import { AiCostSections } from "@/features/superadmin/components/ai-cost-sections"
import { AiBudgets } from "@/features/superadmin/components/ai-budgets"
import { LimitHitLists } from "@/features/superadmin/components/limit-hit-lists"
import { StatsPicker } from "@/features/superadmin/components/stats-picker"
import { BUDGET_SOURCES } from "@/config/ai-costs"
import { useStatsChoice } from "@/hooks/use-stats-choice"
import { apiFetch } from "@/lib/api"
import type { AiCosts, Budget, LimitHitLists as Hits } from "@/types/superadmin"

type Loaded = { costs: AiCosts | null; hits: Hits | null; budgets: Budget[] }

/** The AI costs tab: the period the browser kept (shared with the stats tab), what AI cost in it
 * and why, today's shared budgets, and the limits' hits; asked again whenever the period
 * changes. A service that doesn't answer leaves its part out. */
export function AiCostsView() {
  const { choice, query, change } = useStatsChoice()
  const [loaded, setLoaded] = useState<Loaded | null>(null)

  useEffect(() => {
    if (query === null) {
      return
    }

    let current = true

    Promise.all([
      apiFetch<AiCosts>(`/billing/superadmin/ai-costs${query}`).catch(
        () => null
      ),
      apiFetch<Hits>(`/billing/superadmin/limit-hits${query}`).catch(
        () => null
      ),
      ...BUDGET_SOURCES.map((source) =>
        apiFetch<Budget[]>(`/${source}/superadmin/budgets`).catch(() => [])
      ),
    ]).then(([costs, hits, ...budgets]) => {
      if (current) {
        setLoaded({
          costs: costs as AiCosts | null,
          hits: hits as Hits | null,
          budgets: (budgets as Budget[][]).flat(),
        })
      }
    })

    return () => {
      current = false
    }
  }, [query])

  return (
    <div className="space-y-10">
      {choice && <StatsPicker choice={choice} onChange={change} />}
      {loaded?.costs && (
        <AiCostSections
          costs={loaded.costs}
          budgets={
            <AiBudgets
              unpaid={loaded.costs.unpaid_today}
              budgets={loaded.budgets}
            />
          }
        />
      )}
      {loaded?.hits && <LimitHitLists hits={loaded.hits} />}
    </div>
  )
}
