"use client"

import { SquarePenIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"

import { CampaignDialog } from "@/components/superadmin/campaign-dialog"
import { Button } from "@/components/ui/button"
import { LANGUAGE_NAMES, type Locale } from "@/config/i18n"
import type { Campaign } from "@/types/campaigns"

/** A draft campaign's edit button, on its title's line: writes it in the language its preview
 * shows. */
export function EditCampaign({
  campaign,
  language,
  onChanged,
}: {
  campaign: Campaign
  language: string
  onChanged: (campaign: Campaign) => void
}) {
  const t = useTranslations("superadmin")
  const [editing, setEditing] = useState(false)

  return (
    <>
      <Button
        variant="outline"
        className="h-10 px-5 text-base"
        onClick={() => setEditing(true)}
        data-testid="edit-campaign"
      >
        <SquarePenIcon />
        {language === "en"
          ? t("editCampaign")
          : t("editCampaignIn", {
              language: LANGUAGE_NAMES[language as Locale],
            })}
      </Button>
      {editing && (
        <CampaignDialog
          open
          onOpenChange={setEditing}
          campaign={campaign}
          language={language}
          onSaved={onChanged}
        />
      )}
    </>
  )
}
