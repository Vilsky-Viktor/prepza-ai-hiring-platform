"use client"

import { Trash2Icon } from "lucide-react"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

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
import { apiFetch } from "@/lib/api"
import { bdi, bdiText } from "@/lib/bidi"
import type { CompanyCredits } from "@/types/billing"

export function RemoveCompany({
  companyId,
  name,
  onRemoved,
}: {
  companyId: string
  name: string
  // Takes it out of the list at once (pages loaded past the first aren't refreshed).
  onRemoved?: () => void
}) {
  const t = useTranslations("company")
  const common = useTranslations("common")
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [removing, setRemoving] = useState(false)
  // The company's credits, read when the dialog opens: they're lost with it.
  const [credits, setCredits] = useState<CompanyCredits | null>(null)

  function openDialog() {
    setCredits(null)
    setOpen(true)
    apiFetch<CompanyCredits>(`/companies/companies/${companyId}/credits`)
      .then(setCredits)
      .catch(() => {})
  }

  async function remove() {
    setRemoving(true)

    try {
      await apiFetch(`/companies/companies/${companyId}`, { method: "DELETE" })
      setOpen(false)
      onRemoved?.()
      router.refresh()
    } catch {
      toast.error(t("removeFailed"))
    } finally {
      setRemoving(false)
    }
  }

  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        className="size-12 text-muted-foreground hover:text-destructive"
        aria-label={t.markup("removeLabel", { name, ...bdiText })}
        tooltip={t("remove")}
        onClick={openDialog}
      >
        <Trash2Icon className="size-6" />
      </Button>
      <Dialog
        open={open}
        onOpenChange={(next) => {
          if (!removing) {
            setOpen(next)
          }
        }}
      >
        <DialogContent showCloseButton={false}>
          <DialogHeader className="gap-4">
            <DialogTitle className="no-dot mb-2">
              {t.rich("removeTitle", { name, ...bdi })}
            </DialogTitle>
            <DialogDescription>{t("removeText")}</DialogDescription>
            {credits && credits.available > 0 && (
              <p
                className="text-base text-destructive"
                data-testid="remove-credits"
              >
                {t("removeCredits", {
                  credits: credits.available,
                  candidates: credits.candidates,
                })}
              </p>
            )}
          </DialogHeader>
          <DialogFooter>
            <DialogClose
              render={
                <Button
                  variant="outline"
                  className="h-10 px-5 text-base"
                  disabled={removing}
                />
              }
            >
              {common("cancel")}
            </DialogClose>
            <Button
              variant="destructive"
              className="h-10 px-5 text-base"
              disabled={removing}
              onClick={remove}
            >
              {t("remove")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
