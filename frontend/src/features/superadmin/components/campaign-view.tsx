"use client"

import { useLocale, useTranslations } from "next-intl"
import { type ReactNode, useEffect, useState } from "react"

import { EditableTitle } from "@/components/common/editable-title"
import { PageHeader } from "@/components/common/page-header"
import { PillSelect } from "@/components/common/pill-select"
import { CampaignActions } from "@/features/superadmin/components/campaign-actions"
import { CampaignStatus } from "@/features/superadmin/components/campaign-status"
import { DeleteCampaign } from "@/features/superadmin/components/delete-campaign"
import { EditCampaign } from "@/features/superadmin/components/edit-campaign"
import { NumberCards } from "@/features/superadmin/components/number-cards"
import { Badge } from "@/components/ui/badge"
import { LANGUAGE_NAMES, LOCALES } from "@/config/i18n"
import { apiFetch } from "@/lib/api"
import { compactNumber, formatList } from "@/lib/format"
import type { Campaign, CampaignPreview } from "@/types/campaigns"

const COUNTS = [
  "pending",
  "sent",
  "skipped",
  "failed",
  "unsubscribed",
  "complained",
] as const

/** A campaign's page, laid out as a template's: its subject as the title with its kind and
 * where it stands under it, its actions, its numbers as the stats tab's cards (before sending,
 * who'd get it; after, how it went), and the email as a user in the chosen language gets it. */
export function CampaignView({
  initial,
  back,
}: {
  initial: Campaign
  back: ReactNode
}) {
  const t = useTranslations("superadmin")
  const locale = useLocale()
  const [campaign, setCampaign] = useState(initial)
  const [language, setLanguage] = useState("en")
  const [preview, setPreview] = useState<CampaignPreview | null>(null)
  const [recipients, setRecipients] = useState<number | null>(null)
  const path = `/notifications/superadmin/campaigns/${campaign.id}`

  useEffect(() => {
    apiFetch<CampaignPreview>(`${path}/preview?language=${language}`)
      .then(setPreview)
      .catch(() => setPreview(null))
  }, [path, language, campaign])

  useEffect(() => {
    if (campaign.status !== "draft") {
      return
    }

    apiFetch<{ count: number }>(`${path}/recipients`)
      .then((found) => setRecipients(found.count))
      .catch(() => setRecipients(null))
    // Again after an edit: its kind or audience may have changed.
  }, [path, campaign])

  const shown = (value: number | null | undefined) =>
    value === null || value === undefined ? "—" : compactNumber(value, locale)
  const numbers = COUNTS.map((key) => ({
    key,
    label: t(`campaignCounts.${key}`),
    value: shown(campaign.counts?.[key]),
  }))

  // Whom it goes to, a badge each: everyone, or its groups (the companies' owners and admins
  // only, when so) and the companies it's limited to.
  const audience = [
    ...(campaign.groups.length === 0 ? [t("campaignAudienceEveryone")] : []),
    ...campaign.groups.map((group) =>
      group === "members" && campaign.editors_only
        ? t("campaignAudienceEditorsOnly")
        : t(`campaignAudienceGroups.${group}`)
    ),
  ]
  // Companies' names keep their case.
  const companies =
    campaign.companies.length > 0 &&
    formatList(
      campaign.companies.map((company) => company.name),
      locale
    )

  const buttons = campaign.status === "draft" && (
    <div className="flex items-center gap-2">
      <EditCampaign
        campaign={campaign}
        language={language}
        onChanged={setCampaign}
      />
      <DeleteCampaign campaignId={campaign.id} />
    </div>
  )

  return (
    <>
      <PageHeader
        back={back}
        title={
          // A draft's edit and delete buttons on the title's line, as a template's; on phones
          // on a line of their own under the tags, centered.
          <div className="flex items-center justify-between gap-4">
            <div className="min-w-0 flex-1">
              <EditableTitle
                title={campaign.texts.en.subject}
                path=""
                editable={false}
              />
            </div>
            {buttons && <div className="max-sm:hidden">{buttons}</div>}
          </div>
        }
        tags={
          <>
            <Badge variant="outline" className="h-7 px-3 text-sm font-light">
              {t(`campaignKinds.${campaign.kind}`)}
            </Badge>
            {audience.map((label) => (
              <Badge
                key={label}
                variant="outline"
                className="h-7 px-3 text-sm font-light"
                data-testid="campaign-audience"
              >
                {label}
              </Badge>
            ))}
            {companies && (
              <Badge
                variant="outline"
                className="h-7 px-3 text-sm font-light normal-case"
                data-testid="campaign-companies"
              >
                {companies}
              </Badge>
            )}
            <CampaignStatus campaign={campaign} />
          </>
        }
      >
        {buttons && (
          <div className="flex justify-center pt-3 sm:hidden">{buttons}</div>
        )}
      </PageHeader>
      {campaign.counts && <NumberCards items={numbers} />}
      <div className="space-y-4">
        {/* The preview's language and, before sending, who'd get it on the left; sending on the
            right. */}
        <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3">
          <div className="flex flex-wrap items-center gap-x-6 gap-y-3 max-sm:w-full max-sm:justify-center">
            <PillSelect
              ariaLabel={t("campaignPreviewLanguage")}
              className="w-full sm:w-72"
              value={language}
              options={LOCALES.map((code) => ({
                value: code,
                label: LANGUAGE_NAMES[code],
                lang: code,
              }))}
              onChange={setLanguage}
            />
            {!campaign.counts && (
              <p
                className="text-lg text-muted-foreground"
                data-testid="campaign-recipients"
              >
                {t.rich("campaignRecipients", {
                  shown: shown(recipients),
                  count: recipients ?? 0,
                  number: (chunks) => (
                    <span className="font-heading text-3xl font-medium tracking-tight text-primary tabular-nums">
                      {chunks}
                    </span>
                  ),
                })}
              </p>
            )}
          </div>
          <CampaignActions
            campaign={campaign}
            language={language}
            recipients={recipients}
            onChanged={setCampaign}
          />
        </div>
        {/* The email exactly as it's sent; sandboxed, so nothing in it runs. As tall as the
            email, so the page scrolls it (a phone can't scroll inside a frame); reading its
            height needs the same origin, still without scripts. */}
        {preview && (
          <iframe
            title={preview.subject}
            srcDoc={preview.html}
            sandbox="allow-same-origin"
            onLoad={(event) => {
              const frame = event.currentTarget
              const page = frame.contentDocument?.documentElement

              if (!page) {
                return
              }

              // No scroll bar of its own; it grows as the email does (its images loading).
              page.style.overflow = "hidden"
              new ResizeObserver(() => {
                frame.style.height = `${page.scrollHeight}px`
              }).observe(page)
            }}
            className="h-[40rem] w-full rounded-xl border bg-white"
          />
        )}
      </div>
    </>
  )
}
