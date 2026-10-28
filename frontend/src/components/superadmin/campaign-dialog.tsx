"use client"

import dynamic from "next/dynamic"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { FloatingInput } from "@/components/ui/floating-field"
import { LabeledField } from "@/components/labeled-field"
import { PillSelect } from "@/components/common/pill-select"
import { CampaignAudience } from "@/components/superadmin/campaign-audience"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { WarningCard } from "@/components/common/warning-card"
import { LANGUAGE_NAMES, type Locale } from "@/config/i18n"
import {
  MAX_CAMPAIGN_BUTTON_LENGTH,
  MAX_CAMPAIGN_SUBJECT_LENGTH,
  MAX_CAMPAIGN_TEXT_LENGTH,
} from "@/config/limits"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { campaignForm } from "@/lib/campaigns"
import type { Campaign, CampaignKind } from "@/types/campaigns"

// The rich text editor (TipTap) is large and only this dialog uses it: loaded when it opens.
const TextEditor = dynamic(
  () => import("@/components/text-editor").then((module) => module.TextEditor),
  { ssr: false }
)

const KINDS: CampaignKind[] = ["updates", "promotions", "notices"]
const PATH = "/notifications/superadmin/campaigns"

/** Writes a campaign, as the news tab's dialog writes a post: a new one in English (its kind,
 * audience, subject, text with its styles and an optional button), or `campaign` in `language`:
 * in English with its kind, audience and button link too, in another language only its texts.
 * An important notice says first what it's for. The API checks the limits, the audience and the
 * link. */
export function CampaignDialog({
  open,
  onOpenChange,
  campaign,
  language = "en",
  onSaved,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  campaign?: Campaign
  language?: string
  onSaved: (campaign: Campaign) => void
}) {
  const t = useTranslations("superadmin")
  const common = useTranslations("common")
  const english = language === "en"
  const initial = campaignForm(campaign, language)
  const [kind, setKind] = useState<CampaignKind>(initial.kind)
  const [audience, setAudience] = useState(initial.audience)
  const [subject, setSubject] = useState(initial.subject)
  const [text, setText] = useState(initial.text)
  const [button, setButton] = useState(initial.button)
  const [link, setLink] = useState(initial.link)
  const [saving, setSaving] = useState(false)

  async function save(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true)
    const body = { subject, text, button: button || null }

    try {
      const saved = await apiFetch<Campaign>(
        !campaign
          ? PATH
          : english
            ? `${PATH}/${campaign.id}`
            : `${PATH}/${campaign.id}/texts/${language}`,
        {
          method: campaign ? "PUT" : "POST",
          body: JSON.stringify(
            english
              ? {
                  ...body,
                  kind,
                  groups: audience.groups,
                  editors_only: audience.editorsOnly,
                  company_ids: audience.companies.map((company) => company.id),
                  link: link || null,
                }
              : body
          ),
        }
      )
      onSaved(saved)
      onOpenChange(false)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("campaignSaveFailed")))
    } finally {
      setSaving(false)
    }
  }

  const name = LANGUAGE_NAMES[language as Locale]

  return (
    <Dialog open={open} onOpenChange={(next) => !saving && onOpenChange(next)}>
      <DialogContent showCloseButton={false} className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>
            {!campaign
              ? t("newCampaign")
              : english
                ? t("editCampaign")
                : t("editCampaignIn", { language: name })}
          </DialogTitle>
          <DialogDescription>
            {english
              ? t("campaignInEnglish")
              : t("campaignInLanguage", { language: name })}
          </DialogDescription>
        </DialogHeader>
        <form id="campaign" onSubmit={save} className="min-w-0 space-y-4">
          {english && (
            <PillSelect
              label={t("campaignKind")}
              value={kind}
              options={KINDS.map((value) => ({
                value,
                label: t(`campaignKinds.${value}`),
              }))}
              onChange={(value) => {
                setKind(value as CampaignKind)

                // Only an important notice goes to some companies only.
                if (value !== "notices") {
                  setAudience({ ...audience, companies: [] })
                }
              }}
            />
          )}
          {english && kind === "notices" && (
            <WarningCard>{t("campaignNoticeWarning")}</WarningCard>
          )}
          {english && (
            <CampaignAudience
              kind={kind}
              value={audience}
              onChange={setAudience}
            />
          )}
          <FloatingInput
            label={t("campaignSubject")}
            required
            maxLength={MAX_CAMPAIGN_SUBJECT_LENGTH}
            placeholder={t("campaignSubjectPlaceholder")}
            value={subject}
            onChange={(event) => setSubject(event.target.value)}
          />
          {/* The editor names itself (aria-label); the label shows its name. */}
          <LabeledField label={t("campaignText")}>
            <TextEditor
              value={text}
              onChange={setText}
              label={t("campaignText")}
              placeholder={t("campaignTextPlaceholder")}
            />
            <p
              aria-live="polite"
              className="text-end text-sm text-muted-foreground tabular-nums"
            >
              {t("charactersLeft", {
                count: MAX_CAMPAIGN_TEXT_LENGTH - text.length,
              })}
            </p>
          </LabeledField>
          <FloatingInput
            label={t("campaignButton")}
            maxLength={MAX_CAMPAIGN_BUTTON_LENGTH}
            value={button}
            onChange={(event) => setButton(event.target.value)}
          />
          {english && (
            <FloatingInput
              label={t("campaignLink")}
              placeholder={t("campaignLinkPlaceholder")}
              value={link}
              onChange={(event) => setLink(event.target.value)}
            />
          )}
        </form>
        <DialogFooter>
          <DialogClose
            render={
              <Button
                variant="outline"
                className="h-10 px-5 text-base"
                disabled={saving}
              />
            }
          >
            {common("cancel")}
          </DialogClose>
          <Button
            type="submit"
            form="campaign"
            className="h-10 px-5 text-base"
            disabled={saving}
          >
            {saving ? common("saving") : common("save")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
