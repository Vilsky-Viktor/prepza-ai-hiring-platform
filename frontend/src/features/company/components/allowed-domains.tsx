"use client"

import { cn } from "cn"
import { LaptopIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { CornerSign } from "@/components/common/corner-sign"
import { AllowedList } from "@/features/company/components/allowed-list"
import { Switch } from "@/components/ui/switch"
import { SIGN_CARD } from "@/config/cards"
import { apiErrorMessage, apiFetch } from "@/lib/api"

type Saved = { domains: string[]; allow_localhost: boolean }

/** The API page's SDK tab: the company's allowed domains, the sites that may embed its interviews
 * with the SDK (nothing else uses them), then whether localhost may too (to try it on the
 * developer's own computer), as the AI apps switch's card. Owners and admins change both;
 * every change saves at once. Verification has nothing to do with it. On phones the switch's card
 * spans the screen. */
export function AllowedDomains({
  companyId,
  domains,
  allowLocalhost,
  canEdit,
}: {
  companyId: string
  domains: string[]
  allowLocalhost: boolean
  canEdit: boolean
}) {
  const t = useTranslations("api")
  const [saved, setSaved] = useState<Saved>({
    domains,
    allow_localhost: allowLocalhost,
  })
  const [saving, setSaving] = useState(false)

  async function save(next: Saved) {
    const kept = await apiFetch<Saved>(
      `/companies/companies/${companyId}/allowed-domains`,
      { method: "PUT", body: JSON.stringify(next) }
    )
    setSaved(kept)

    return kept
  }

  async function toggle(on: boolean) {
    setSaving(true)

    try {
      await save({ ...saved, allow_localhost: on })
    } catch (error) {
      toast.error(apiErrorMessage(error, t("allowedDomainsFailed")))
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="space-y-6">
      <p className="text-base text-muted-foreground">
        {t("allowedDomainsText")}
      </p>
      <AllowedList
        entries={saved.domains}
        label={t("domain")}
        hint={t("domainHint")}
        empty={t("noDomains")}
        removeLabel={(entry) => t("removeEntry", { entry })}
        failed={t("allowedDomainsFailed")}
        canEdit={canEdit}
        save={async (entries) =>
          (await save({ ...saved, domains: entries })).domains
        }
      />
      <label
        className={cn(
          SIGN_CARD,
          "flex cursor-pointer items-center gap-4 text-base max-sm:-mx-6 max-sm:rounded-none"
        )}
      >
        <CornerSign>
          <LaptopIcon className="text-primary" />
        </CornerSign>
        <span className="min-w-0 flex-1 space-y-1">
          <span className="block font-medium lowercase">
            {t("localhostTitle")}
            <span className="text-primary">.</span>
          </span>
          <span className="block text-sm text-muted-foreground">
            {t("localhostText")}
          </span>
        </span>
        <Switch
          checked={saved.allow_localhost}
          disabled={saving || !canEdit}
          onCheckedChange={toggle}
        />
      </label>
    </section>
  )
}
