"use client"

import { useTranslations } from "next-intl"
import { useState, type ReactNode } from "react"

import { AutoTopUpSetting } from "@/components/billing/auto-top-up"
import { CustomTopUp } from "@/components/billing/custom-top-up"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import type { Catalog } from "@/types/billing"

/** The top-up button and its dialog: any number of candidates, and the automatic top-up, for
 * `companyId`'s credits. */
export function TopUpDialog({
  catalog,
  title,
  companyId,
  card,
}: {
  catalog: Catalog
  // Whose credits: "Your credits" or the company's name.
  title: string
  companyId: string
  // Opens from this card (a balance in a page header) instead of a button.
  card?: ReactNode
}) {
  const t = useTranslations("billing")
  const [open, setOpen] = useState(false)

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        data-testid="top-up"
        render={
          card ? (
            <button
              type="button"
              className="cursor-pointer rounded-xl border px-4 py-2 text-end whitespace-nowrap transition-colors hover:bg-muted max-sm:text-center"
            />
          ) : (
            <Button className="h-10 px-5" />
          )
        }
      >
        {card ?? t("topUp")}
      </DialogTrigger>
      <DialogContent
        showCloseButton={false}
        className="sm:max-w-2xl"
        data-testid="top-up-dialog"
      >
        <DialogHeader>
          <DialogTitle>{t("topUpTitle", { name: title })}</DialogTitle>
          <DialogDescription className="text-base">
            {t("topUpNote")} {t("taxes")}
          </DialogDescription>
        </DialogHeader>
        <CustomTopUp
          catalog={catalog}
          companyId={companyId}
          onOpened={() => setOpen(false)}
        />
        <AutoTopUpSetting catalog={catalog} companyId={companyId} card />
        <DialogFooter showCloseButton />
      </DialogContent>
    </Dialog>
  )
}
