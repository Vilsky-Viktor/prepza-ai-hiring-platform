"use client"

import { KeyRoundIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { useLocalTime } from "@/hooks/use-local-time"
import { ConfirmDialog } from "@/components/common/confirm-dialog"
import { CopyValue } from "@/components/common/copy-field"
import { IconButton } from "@/components/common/icon-button"
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
import { timeTag } from "@/lib/time-tag"

/** Rolling a web hook's signing secret, for owners and admins: asked first, then the new secret,
 * shown this once to copy, as when the web hook was added. The api service keeps the old one
 * signing too for a while, and says until when. */
export function RollSecret({ path }: { path: string }) {
  const t = useTranslations("api")
  const common = useTranslations("common")
  const localTime = useLocalTime()
  const [asking, setAsking] = useState(false)
  const [busy, setBusy] = useState(false)
  const [rolled, setRolled] = useState<{
    secret: string
    previous_until: string
  } | null>(null)

  async function roll() {
    setBusy(true)

    try {
      setRolled(await apiFetch(path, { method: "POST" }))
      setAsking(false)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("rollSecretFailed")))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <IconButton label={t("rollSecret")} onClick={() => setAsking(true)}>
        <KeyRoundIcon className="size-6" />
      </IconButton>
      <ConfirmDialog
        open={asking}
        onOpenChange={setAsking}
        title={t("rollSecretTitle")}
        text={t("rollSecretText")}
        confirm={t("rollSecret")}
        busy={busy}
        onConfirm={roll}
      />
      <Dialog
        open={rolled !== null}
        onOpenChange={(open) => !open && setRolled(null)}
      >
        <DialogContent showCloseButton={false} className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>{t("newSecretTitle")}</DialogTitle>
            <DialogDescription>
              {rolled &&
                t.rich("newSecretText", {
                  until: localTime.dateTime(rolled.previous_until),
                  ...timeTag(rolled.previous_until),
                })}
            </DialogDescription>
          </DialogHeader>
          {rolled && (
            <CopyValue
              value={rolled.secret}
              label={t("copySecret")}
              copied={t("secretCopied")}
            />
          )}
          <DialogFooter>
            <DialogClose render={<Button className="h-10 px-5 text-base" />}>
              {common("close")}
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
