"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { LabeledField } from "@/components/labeled-field"
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
import { MAX_ADJUSTMENT_NOTE } from "@/constants/limits"
import { apiErrorMessage, apiFetch, serviceRefusal } from "@/lib/api"
import { bdi } from "@/lib/bidi"

const FIELD =
  "rounded-full border border-transparent transition-colors focus-within:border-ring"
const INPUT = "h-16 border-0 px-6 text-lg focus-visible:ring-0 md:text-lg"

/** A superadmin adds credits to a company (a positive amount) or removes some (negative), with
 * the reason its history will show, confirmed on a second step. The billing service refuses an
 * amount that would take the available balance below zero; one request key per opening, so a
 * repeated click counts once. */
export function AdjustCredits({
  companyId,
  name,
}: {
  companyId: string
  name: string
}) {
  const t = useTranslations("superadmin")
  const common = useTranslations("common")
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [amount, setAmount] = useState("")
  const [note, setNote] = useState("")
  const [key, setKey] = useState("")
  const [saving, setSaving] = useState(false)
  const credits = Number(amount)
  const valid = Number.isInteger(credits) && credits !== 0 && note.trim() !== ""

  function start() {
    setAmount("")
    setNote("")
    setConfirming(false)
    setKey(crypto.randomUUID())
    setOpen(true)
  }

  async function save() {
    setSaving(true)

    try {
      await apiFetch(
        `/companies/superadmin/support/companies/${companyId}/adjustments`,
        {
          method: "POST",
          body: JSON.stringify({ amount: credits, note: note.trim(), key }),
        }
      )
      toast.success(t("adjusted"))
      setOpen(false)
      router.refresh()
    } catch (error) {
      toast.error(
        serviceRefusal(error, [409]) ??
          apiErrorMessage(error, t("actionFailed"))
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <Button
        className="h-10 px-5 text-base max-sm:flex-1"
        data-testid="adjust-credits"
        onClick={start}
      >
        {t("adjustCredits")}
      </Button>
      <Dialog open={open} onOpenChange={(next) => !saving && setOpen(next)}>
        <DialogContent showCloseButton={false} className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {confirming
                ? t.rich("adjustConfirmTitle", {
                    amount: credits,
                    name,
                    ...bdi,
                  })
                : t.rich("adjustTitle", { name, ...bdi })}
            </DialogTitle>
            <DialogDescription>
              {confirming ? note.trim() : t("adjustText")}
            </DialogDescription>
          </DialogHeader>
          {!confirming && (
            <form
              id="adjust-credits-form"
              className="space-y-3"
              onSubmit={(event) => {
                event.preventDefault()
                setConfirming(true)
              }}
            >
              <LabeledField label={t("adjustAmount")}>
                <div className={FIELD}>
                  <Input
                    required
                    type="number"
                    step={1}
                    inputMode="numeric"
                    value={amount}
                    onChange={(event) => setAmount(event.target.value)}
                    className={INPUT}
                  />
                </div>
              </LabeledField>
              <LabeledField label={t("adjustNote")}>
                <div className={FIELD}>
                  <Input
                    required
                    maxLength={MAX_ADJUSTMENT_NOTE}
                    value={note}
                    onChange={(event) => setNote(event.target.value)}
                    className={INPUT}
                  />
                </div>
              </LabeledField>
            </form>
          )}
          <DialogFooter>
            {confirming ? (
              <Button
                variant="outline"
                className="h-10 px-5 text-base"
                disabled={saving}
                onClick={() => setConfirming(false)}
              >
                {t("adjustBack")}
              </Button>
            ) : (
              <DialogClose
                render={
                  <Button variant="outline" className="h-10 px-5 text-base" />
                }
              >
                {common("cancel")}
              </DialogClose>
            )}
            {confirming ? (
              <Button
                className="h-10 px-5 text-base"
                disabled={saving}
                onClick={save}
              >
                {t("adjustConfirm")}
              </Button>
            ) : (
              <Button
                type="submit"
                form="adjust-credits-form"
                className="h-10 px-5 text-base"
                disabled={!valid}
              >
                {t("adjustNext")}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
