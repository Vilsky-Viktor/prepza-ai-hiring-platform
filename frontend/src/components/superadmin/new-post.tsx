"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"

import { NewsDialog } from "@/components/superadmin/news-dialog"
import { Button } from "@/components/ui/button"

/** The news tab's "New post" button, opening an empty post; the list shows it once saved. */
export function NewPost() {
  const t = useTranslations("superadmin")
  const router = useRouter()
  const [open, setOpen] = useState(false)

  return (
    <>
      <Button
        className="h-12 shrink-0 px-6 text-base"
        onClick={() => setOpen(true)}
        data-testid="new-post"
      >
        {t("newPost")}
      </Button>
      {/* Mounted only while open, so each new post starts empty with today's date. */}
      {open && (
        <NewsDialog
          open
          onOpenChange={setOpen}
          onSaved={() => router.refresh()}
        />
      )}
    </>
  )
}
