"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"

import { CampaignDialog } from "@/features/superadmin/components/campaign-dialog"
import { Button } from "@/components/ui/button"

/** The campaigns tab's "New campaign" button, as the news tab's "New post": it opens an empty
 * campaign, and its page once saved. */
export function NewCampaign() {
  const t = useTranslations("superadmin")
  const router = useRouter()
  const [open, setOpen] = useState(false)

  return (
    <>
      <Button
        className="h-12 shrink-0 px-6 text-base"
        onClick={() => setOpen(true)}
        data-testid="new-campaign"
      >
        {t("newCampaign")}
      </Button>
      {/* Mounted only while open, so each new campaign starts empty. */}
      {open && (
        <CampaignDialog
          open
          onOpenChange={setOpen}
          onSaved={(saved) => router.push(`/superadmin/campaigns/${saved.id}`)}
        />
      )}
    </>
  )
}
