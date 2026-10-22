"use client"

import dynamic from "next/dynamic"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { LabeledField } from "@/components/labeled-field"
import { PillSelect } from "@/components/pill-select"
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
import { Input } from "@/components/ui/input"
import { LANGUAGE_NAMES, type Locale } from "@/constants/i18n"
import {
  MAX_CAMPAIGN_BUTTON_LENGTH,
  MAX_CAMPAIGN_SUBJECT_LENGTH,
  MAX_CAMPAIGN_TEXT_LENGTH,
} from "@/constants/limits"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { campaignForm } from "@/lib/campaigns"
import type { Campaign } from "@/types/campaigns"
import { GRAY_FIELD } from "@/constants/fields"

// The rich text editor (TipTap) is large and only this dialog uses it: loaded when it opens.
const TextEditor = dynamic(
  () => import("@/components/text-editor").then((module) => module.TextEditor),
  { ssr: false }
)

const KINDS = ["updates", "promotions"] as const
const PATH = "/notifications/superadmin/campaigns"

/** Writes a campaign, as the news tab's dialog writes a post: a new one in English (its kind,
 * subject, text with its styles and an optional button), or `campaign` in `language`: in English with its kind
 * and button link too, in another language only its texts. The API checks the limits and the
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
  const [kind, setKind] = useState<string>(initial.kind)
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
            english ? { ...body, kind, link: link || null } : body
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
              onChange={setKind}
            />
          )}
          <LabeledField label={t("campaignSubject")}>
            <Input
              required
              maxLength={MAX_CAMPAIGN_SUBJECT_LENGTH}
              placeholder={t("campaignSubjectPlaceholder")}
              value={subject}
              onChange={(event) => setSubject(event.target.value)}
              className={`h-14 ${GRAY_FIELD}`}
            />
          </LabeledField>
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
          <LabeledField label={t("campaignButton")}>
            <Input
              maxLength={MAX_CAMPAIGN_BUTTON_LENGTH}
              value={button}
              onChange={(event) => setButton(event.target.value)}
              className={`h-14 ${GRAY_FIELD}`}
            />
          </LabeledField>
          {english && (
            <LabeledField label={t("campaignLink")}>
              <Input
                placeholder={t("campaignLinkPlaceholder")}
                value={link}
                onChange={(event) => setLink(event.target.value)}
                className={`h-14 ${GRAY_FIELD}`}
              />
            </LabeledField>
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
