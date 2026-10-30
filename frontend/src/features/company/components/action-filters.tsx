"use client"

import { usePathname, useRouter, useSearchParams } from "next/navigation"
import { useTranslations } from "next-intl"

import { FloatingInput } from "@/components/ui/floating-field"
import { PillSelect } from "@/components/common/pill-select"
import { ACTION_GROUPS } from "@/config/action-log"
import { dayStart, today } from "@/lib/format"
import type { CompanyMember } from "@/types/company"

// "Anyone" and "All actions" in the menus.
const ANY = "any"

/** The action log's filters: a member, a group of actions, and the days from and to (the
 * viewer's own days, sent as the moments they start and end). The choice lives in the address,
 * so the server renders the first page filtered. */
export function ActionFilters({ members }: { members: CompanyMember[] }) {
  const t = useTranslations("actionLog")
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const from = searchParams.get("from")
  // The last day shown: the one before the moment `to` (its end).
  const to = searchParams.get("to")

  function choose(name: string, value: string | null) {
    const params = new URLSearchParams(searchParams)

    if (value === null || value === ANY) {
      params.delete(name)
    } else {
      params.set(name, value)
    }

    router.replace(`${pathname}?${params}`, { scroll: false })
  }

  return (
    <div
      className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
      data-testid="action-filters"
    >
      <PillSelect
        label={t("member")}
        value={searchParams.get("member_id") ?? ANY}
        options={[
          { value: ANY, label: t("anyMember") },
          ...members.map((member) => ({
            value: member.id,
            label: member.email,
          })),
        ]}
        onChange={(value) => choose("member_id", value)}
      />
      <PillSelect
        label={t("action")}
        value={searchParams.get("group") ?? ANY}
        options={[
          { value: ANY, label: t("anyAction") },
          ...ACTION_GROUPS.map((group) => ({
            value: group,
            label: t(`groups.${group}`),
          })),
        ]}
        onChange={(value) => choose("group", value)}
      />
      <DayField
        label={t("from")}
        value={from ? today(new Date(from)) : ""}
        onChange={(day) => choose("from", day ? dayStart(day) : null)}
      />
      <DayField
        label={t("to")}
        value={to ? today(new Date(new Date(to).getTime() - 1)) : ""}
        onChange={(day) => choose("to", day ? dayStart(day, 1) : null)}
      />
    </div>
  )
}

/** A day picked in a floating-label date field. */
export function DayField({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (day: string) => void
}) {
  return (
    <FloatingInput
      label={label}
      type="date"
      value={value}
      onChange={(event) => onChange(event.target.value)}
    />
  )
}
