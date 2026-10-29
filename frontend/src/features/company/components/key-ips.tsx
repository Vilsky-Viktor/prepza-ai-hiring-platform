"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"

import { AllowedList } from "@/features/company/components/allowed-list"
import { apiFetch } from "@/lib/api"
import type { ApiKey } from "@/types/api-access"

/** A key's allowed IPs on its page: the addresses it may be used from, which owners and admins
 * add and take off; none means any address. */
export function KeyIps({
  companyId,
  apiKey,
  canEdit,
}: {
  companyId: string
  apiKey: ApiKey
  canEdit: boolean
}) {
  const t = useTranslations("api")
  const router = useRouter()

  async function save(entries: string[]) {
    const saved = await apiFetch<ApiKey>(
      `/v1/manage/keys/${apiKey.id}/allowed-ips?company_id=${companyId}`,
      { method: "PUT", body: JSON.stringify({ allowed_ips: entries }) }
    )
    router.refresh()

    return saved.allowed_ips
  }

  return (
    <AllowedList
      entries={apiKey.allowed_ips}
      label={t("ipAddress")}
      empty={t("anyIp")}
      removeLabel={(entry) => t("removeEntry", { entry })}
      failed={t("allowedIpsFailed")}
      canEdit={canEdit}
      save={save}
    />
  )
}
