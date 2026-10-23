"use client"

import { useTranslations } from "next-intl"

import { Dotted } from "@/components/dot"
import { useLimitAmount } from "@/components/superadmin/ai-budgets"
import { useAdminName } from "@/hooks/use-admin-name"
import { useLocalTime } from "@/hooks/use-local-time"
import type { LimitChange } from "@/types/superadmin"

/** The latest changes of the limits, newest first: which limit, from what to what (a reset reads
 * "default"), who changed it and when. */
export function LimitChanges({
  changes,
  units,
}: {
  changes: LimitChange[]
  // Each limit's unit, by name, so a change reads as its limit does.
  units: Record<string, string>
}) {
  const t = useTranslations("superadmin")
  const amount = useLimitAmount()
  const named = useAdminName()
  const localTime = useLocalTime()
  const shown = (value: number | null | undefined, name: string) =>
    value === null || value === undefined
      ? t("limitDefaultValue")
      : amount(value, units[name])

  return (
    <div className="space-y-1">
      <h3 className="pt-3 text-sm font-medium text-muted-foreground">
        {t("limitChangesTitle")}
      </h3>
      {changes.length === 0 ? (
        <p className="py-3 text-sm text-muted-foreground">
          {t("limitNoChanges")}
        </p>
      ) : (
        <ul className="divide-y" data-testid="limit-changes">
          {changes.map((change) => (
            <li
              key={`${change.name}-${change.changed_at}`}
              className="space-y-0.5 py-5"
            >
              <span className="block">
                {t("limitChange", {
                  name: named("limitNames", change.name),
                  from: shown(change.old_value, change.name),
                  to: shown(change.new_value, change.name),
                })}
              </span>
              <span className="block text-sm text-muted-foreground">
                <Dotted
                  items={[
                    change.changed_by_email,
                    <time key="changed" dateTime={change.changed_at}>
                      {localTime.dateTime(change.changed_at)}
                    </time>,
                  ]}
                />
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
