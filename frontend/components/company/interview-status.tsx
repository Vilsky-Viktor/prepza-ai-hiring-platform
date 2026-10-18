"use client"

import { useTranslations } from "next-intl"

import { Badge } from "@/components/ui/badge"

/** A test's status as companies decides it: new, in process or hired. Hired stands out. A
 * `label` shows in place of the status's name (the landing's picture of a new interview). */
export function InterviewStatus({
  status,
  label,
}: {
  status: string
  label?: string
}) {
  const t = useTranslations("interviewStatus")

  return (
    <Badge
      variant={status === "hired" ? "default" : "outline"}
      className="h-7 shrink-0 px-3 text-sm font-light"
    >
      {label ?? t(status)}
    </Badge>
  )
}
