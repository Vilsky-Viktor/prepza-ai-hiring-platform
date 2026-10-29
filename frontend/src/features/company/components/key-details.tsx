"use client"

import { useTranslations } from "next-intl"

import { Dot } from "@/components/common/dot"
import { useLocalTime } from "@/hooks/use-local-time"
import type { ApiKey } from "@/types/api-access"

/** A key's dates and where it may be used from, in a line: on its row and on its page. */
export function KeyDetails({ apiKey }: { apiKey: ApiKey }) {
  const t = useTranslations("api")
  const localTime = useLocalTime()

  return (
    <>
      {t.rich("created", localTime.dateValues(apiKey.created_at))}
      <Dot />
      {apiKey.expired ? (
        <span className="text-destructive">{t("expired")}</span>
      ) : apiKey.expires_at ? (
        t.rich("expires", localTime.dateValues(apiKey.expires_at))
      ) : (
        t("neverExpires")
      )}
      <Dot />
      {apiKey.last_used_at
        ? t.rich("lastUsed", localTime.dateValues(apiKey.last_used_at))
        : t("neverUsed")}
      <Dot />
      {apiKey.allowed_ips.length
        ? t("ipCount", { count: apiKey.allowed_ips.length })
        : t("anyIp")}
    </>
  )
}
