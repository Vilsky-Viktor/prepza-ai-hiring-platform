"use client"

import { SquarePenIcon } from "lucide-react"
import Link from "next/link"
import { useTranslations } from "next-intl"
import { useEffect, useState, type ReactNode } from "react"

import { AutoTopUpSetting } from "@/components/common/auto-top-up"
import { CustomTopUp } from "@/components/common/custom-top-up"
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
import { apiFetch } from "@/lib/api"
import { bdi } from "@/lib/bidi"
import type { Catalog } from "@/types/billing"

/** The top-up button and its dialog: any number of candidates, and the automatic top-up, for
 * `companyId`'s credits, priced in the currency the company pays in (billing's catalog for it,
 * read as the dialog opens), which it names, with a link to change it. */
export function TopUpDialog({
  title,
  companyId,
  card,
}: {
  // Whose credits: "Your credits" or the company's name.
  title: string
  companyId: string
  // Opens from this card (a balance in a page header) instead of a button.
  card?: ReactNode
}) {
  const t = useTranslations("billing")
  const [open, setOpen] = useState(false)
  const [catalog, setCatalog] = useState<Catalog | null>(null)

  useEffect(() => {
    if (open) {
      apiFetch<Catalog>(`/companies/companies/${companyId}/billing/catalog`)
        .then(setCatalog)
        .catch(() => {})
    }
  }, [open, companyId])

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        data-testid="top-up"
        render={
          card ? (
            <button
              type="button"
              className="cursor-pointer rounded-xl border px-4 py-2 text-end whitespace-nowrap transition-colors hover:bg-surface max-sm:text-center"
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
          <DialogTitle>
            {t.rich("topUpTitle", { name: title, ...bdi })}
          </DialogTitle>
          <DialogDescription className="text-base">
            {t("topUpNote")} {t("taxes")}
          </DialogDescription>
        </DialogHeader>
        {catalog && (
          <>
            <CustomTopUp
              catalog={catalog}
              companyId={companyId}
              onOpened={() => setOpen(false)}
            />
            <AutoTopUpSetting catalog={catalog} companyId={companyId} card />
            {/* Which currency it's charged in, before paying, with the way to change it. */}
            <p
              className="text-center text-sm text-muted-foreground"
              data-testid="pays-in"
              data-currency={catalog.currency}
            >
              {t("paysIn", { currency: catalog.currency })}
              <Button
                variant="ghost"
                size="icon-xs"
                className="-my-1 ms-1 align-middle text-muted-foreground hover:text-foreground"
                aria-label={t("paysInChange")}
                tooltip={t("paysInChange")}
                render={<Link href={`/companies/${companyId}/billing`} />}
                nativeButton={false}
                onClick={() => setOpen(false)}
              >
                <SquarePenIcon className="size-3.5" />
              </Button>
            </p>
          </>
        )}
        <DialogFooter showCloseButton />
      </DialogContent>
    </Dialog>
  )
}
