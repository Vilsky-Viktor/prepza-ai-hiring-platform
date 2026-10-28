"use client"

import { cn } from "cn"
import { GaugeIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"

import { CornerSign } from "@/components/common/corner-sign"
import { Dotted } from "@/components/common/dot"
import { useAdminName } from "@/hooks/use-admin-name"
import { useLimitAmount } from "@/features/superadmin/components/ai-budgets"
import { LimitChanges } from "@/features/superadmin/components/limit-changes"
import { LimitField } from "@/features/superadmin/components/limit-field"
import { Badge } from "@/components/ui/badge"
import { SIGN_CARD } from "@/config/cards"
import { apiFetch } from "@/lib/api"
import type { Limit, LimitChange, Limits } from "@/types/superadmin"

/** Every limit of ours on the controls page, as the switches' cards, grouped by the service
 * that enforces it: its value to edit (an unpaid one beside its paid one), its default, window
 * and hits of the last days (a plain value, which nothing counts against, only its default);
 * then our providers' limits, read-only, and the history of changes. */
export function LimitSettings({
  initial,
  initialChanges,
}: {
  initial: Limits
  initialChanges: LimitChange[]
}) {
  const t = useTranslations("superadmin")
  const amount = useLimitAmount()
  const named = useAdminName()
  const [limits, setLimits] = useState(initial)
  const [changes, setChanges] = useState(initialChanges)
  const services = [...new Set(limits.limits.map((limit) => limit.service))]
  const units = Object.fromEntries(
    limits.limits
      .flatMap((limit) => [limit, limit.unpaid])
      .filter((limit) => limit)
      .map((limit) => [limit!.name, limit!.unit])
  )

  async function saved(next: Limits) {
    setLimits(next)
    setChanges(
      await apiFetch<LimitChange[]>("/billing/superadmin/limits/changes")
    )
  }

  function facts(limit: Limit) {
    if (!limit.counted) {
      return [t("limitDefault", { value: amount(limit.default, limit.unit) })]
    }

    return [
      limit.window ? named("limitWindows", limit.window) : t("limitAtOnce"),
      named("limitScopes", limit.scope),
      t("limitDefault", { value: amount(limit.default, limit.unit) }),
      t("limitRecentHits", { count: limit.hits, days: limits.hits_days }),
    ]
  }

  function fields(limit: Limit) {
    if (!limit.unpaid) {
      return (
        <LimitField
          key={`${limit.name}-${limit.value}`}
          limit={limit}
          label={named("limitNames", limit.name)}
          onSaved={saved}
        />
      )
    }

    return (
      <div className="space-y-2">
        {[limit, limit.unpaid].map((shown, index) => (
          <div key={shown.name} className="flex items-center gap-3">
            <span className="w-14 text-sm text-muted-foreground">
              {index === 0 ? t("limitPaid") : t("limitUnpaid")}
            </span>
            <LimitField
              key={`${shown.name}-${shown.value}`}
              limit={shown}
              label={named("limitNames", shown.name)}
              onSaved={saved}
            />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className={cn(SIGN_CARD, "space-y-4")}>
      <CornerSign>
        <GaugeIcon className="text-primary" />
      </CornerSign>
      <div className="flex items-center gap-4 text-base">
        <span className="min-w-0 flex-1 space-y-1">
          <span className="block font-medium">{t("limitsTitle")}</span>
          <span className="block text-sm text-muted-foreground">
            {t("limitsText")}
          </span>
        </span>
      </div>
      {services.map((service) => (
        <div key={service} className="space-y-1">
          <h3 className="pt-3 text-sm font-medium text-muted-foreground">
            {named("limitServices", service)}
          </h3>
          <ul className="divide-y">
            {limits.limits
              .filter((limit) => limit.service === service)
              .map((limit) => (
                <li
                  key={limit.name}
                  data-testid={`limit-${limit.name}`}
                  className="flex flex-wrap items-center justify-between gap-3 py-5"
                >
                  <span className="min-w-0 space-y-0.5">
                    <span className="flex flex-wrap items-center gap-2">
                      {named("limitNames", limit.name)}
                      {limit.audience === "unpaid" && !limit.unpaid && (
                        <Badge
                          variant="outline"
                          className="h-6 px-2 text-xs font-light"
                        >
                          {t("limitUnpaid")}
                        </Badge>
                      )}
                    </span>
                    <span className="block text-sm text-muted-foreground">
                      <Dotted items={facts(limit)} />
                    </span>
                  </span>
                  {fields(limit)}
                </li>
              ))}
          </ul>
        </div>
      ))}
      <div className="space-y-1">
        <h3 className="pt-3 text-sm font-medium text-muted-foreground">
          {t("limitsProvidersTitle")}
        </h3>
        <ul className="divide-y">
          {limits.providers.map((limit) => (
            <li
              key={limit.name}
              className="flex flex-wrap items-center justify-between gap-3 py-5"
            >
              <span>{named("limitNames", limit.name)}</span>
              <span className="text-sm text-muted-foreground">
                {t("limitRecentHits", {
                  count: limit.hits,
                  days: limits.hits_days,
                })}
              </span>
            </li>
          ))}
        </ul>
      </div>
      <LimitChanges changes={changes} units={units} />
    </div>
  )
}
