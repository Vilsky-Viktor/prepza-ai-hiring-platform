"use client"

import { Trash2Icon } from "lucide-react"
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

/** Removes a member, or withdraws an invite they haven't accepted yet, after a confirmation. */
export function RemoveMember({
  companyId,
  member,
  onRemoved,
}: {
  companyId: string
  member: CompanyMember
  onRemoved: () => void
}) {
  const t = useTranslations("members")
  const common = useTranslations("common")
  const [busy, setBusy] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const email = member.email

  async function remove() {
    setBusy(true)

    try {
      await apiFetch(
        `/companies/members/${member.id}?company_id=${companyId}`,
        { method: "DELETE" }
      )
      toast.success(t.rich("removed", { email, ...bdi }))
      onRemoved()
    } catch (error) {
      toast.error(apiErrorMessage(error, t("removeFailed")))
      setBusy(false)
      setConfirming(false)
    }
  }

  return (
    <>
      {/* An icon, like removing a candidate; the confirmation names the member. */}
      <Button
        variant="ghost"
        size="icon"
        className="size-12 shrink-0 text-muted-foreground hover:text-destructive"
        aria-label={t("remove")}
        disabled={busy}
        onClick={() => setConfirming(true)}
      >
        <Trash2Icon className="size-6" />
      </Button>
      <Dialog
        open={confirming}
        onOpenChange={(open) => {
          if (!open && !busy) {
            setConfirming(false)
          }
        }}
      >
        <DialogContent showCloseButton={false}>
          <DialogHeader className="gap-4">
            <DialogTitle className="no-dot mb-2">
              {t("removeTitle")}
            </DialogTitle>
            <DialogDescription>
              {t.rich(member.joined ? "removeText" : "removeInviteText", {
                email,
                ...bdi,
              })}
            </DialogDescription>
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
              {common("keep")}
            </DialogClose>
            <Button
              variant="destructive"
              className="h-10 px-5 text-base"
              disabled={busy}
              onClick={remove}
            >
              {t("removeConfirm")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
