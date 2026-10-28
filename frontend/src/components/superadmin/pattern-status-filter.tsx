"use client"

import { usePathname, useRouter } from "next/navigation"
import { useTranslations } from "next-intl"

import { PillSelect } from "@/components/pill-select"
import { PATTERN_STATUSES, type PatternStatus } from "@/config/patterns"

/** Which patterns the tab lists, by status; the choice lives in the address (`?status=`), so the
 * server renders the first page of them. */
export function PatternStatusFilter({ current }: { current: PatternStatus }) {
  const t = useTranslations("superadmin")
  const router = useRouter()
  const pathname = usePathname()

  return (
    <PillSelect
      ariaLabel={t("patternStatusLabel")}
      value={current}
      options={PATTERN_STATUSES.map((status) => ({
        value: status,
        label: t(`patternStatus.${status}`),
      }))}
      onChange={(status) =>
        router.replace(`${pathname}?status=${status}`, { scroll: false })
      }
    />
  )
}
