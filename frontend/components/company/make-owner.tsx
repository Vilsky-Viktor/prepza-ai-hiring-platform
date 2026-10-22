"use client"

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
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { bdi } from "@/lib/bidi"
import type { CompanyMember } from "@/types/company"

/** Asks the owner to confirm handing the company to an admin, who becomes its owner; the owner
 * becomes an admin, so the page is read again for what they may do now. */
export function MakeOwner({
  companyId,
  member,
  open,
  onOpenChange,
}: {
  companyId: string
  member: CompanyMember
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const t = useTranslations("members")
  const common = useTranslations("common")
  const router = useRouter()
  const [busy, setBusy] = useState(false)
  const email = member.email

  async function confirm() {
    setBusy(true)

    try {
      await apiFetch(
        `/companies/members/${member.id}/owner?company_id=${companyId}`,
        { method: "POST" }
      )
      toast.success(t.rich("madeOwner", { email, ...bdi }))
      onOpenChange(false)
      router.refresh()
    } catch (error) {
      toast.error(apiErrorMessage(error, t("makeOwnerFailed")))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !busy && onOpenChange(next)}>
      <DialogContent showCloseButton={false}>
        <DialogHeader className="gap-4">
          <DialogTitle className="no-dot mb-2">
            {t.rich("makeOwnerTitle", { email, ...bdi })}
          </DialogTitle>
          <DialogDescription>{t("makeOwnerText")}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose
            render={
              <Button
                variant="outline"
                className="h-10 px-5 text-base"
                disabled={busy}
              />
            }
          >
            {common("cancel")}
          </DialogClose>
          <Button
            className="h-10 px-5 text-base"
            disabled={busy}
            onClick={confirm}
          >
            {t("makeOwner")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
