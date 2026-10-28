"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import {
  BreezySteps,
  GreenhouseSteps,
  RecruiteeSteps,
  TeamtailorSteps,
  WorkableSteps,
} from "@/components/common/ats-steps"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import type { AtsProvider } from "@/config/ats"
import { apiErrorMessage, apiFetch, serviceRefusal } from "@/lib/api"

// What each ATS's connect form asks for: its fields as the API takes them, and the steps to
// find them.
const FORMS = {
  workable: {
    steps: WorkableSteps,
    fields: [
      { name: "account", label: "account", placeholder: "acme.workable.com" },
      { name: "token", label: "token", secret: true },
    ],
  },
  greenhouse: {
    steps: GreenhouseSteps,
    fields: [
      { name: "client_id", label: "clientId" },
      { name: "client_secret", label: "clientSecret", secret: true },
    ],
  },
  breezy: {
    steps: BreezySteps,
    fields: [{ name: "token", label: "apiKey", secret: true }],
  },
  recruitee: {
    steps: RecruiteeSteps,
    fields: [
      { name: "account", label: "account", placeholder: "acme.recruitee.com" },
      { name: "token", label: "rcToken", secret: true },
    ],
  },
  teamtailor: {
    steps: TeamtailorSteps,
    fields: [{ name: "key", label: "apiKey", secret: true }],
  },
} as const

/** Connect (or Reconnect): the ATS's key, checked by the API before it's saved. */
export function ConnectAts({
  companyId,
  provider,
  again,
  onConnected,
}: {
  companyId: string
  provider: AtsProvider
  again: boolean
  onConnected: () => void
}) {
  const t = useTranslations("ats")
  const common = useTranslations("common")
  const router = useRouter()
  const form = FORMS[provider.id]
  const Steps = form.steps
  const [open, setOpen] = useState(false)
  const [values, setValues] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)
  const filled = form.fields.every((field) => values[field.name])

  async function connect(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true)

    try {
      await apiFetch(`/ats/${provider.id}?company_id=${companyId}`, {
        method: "PUT",
        body: JSON.stringify(values),
      })
      setOpen(false)
      setValues({})
      onConnected()
      router.refresh()
    } catch (error) {
      // The service says why: the details refused (422), or the ATS plan lacks a feature (409).
      toast.error(
        serviceRefusal(error, [409]) ??
          apiErrorMessage(error, t("connectFailed", { ats: provider.name }))
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !saving && setOpen(next)}>
      <DialogTrigger render={<Button className="h-10 px-5 text-base" />}>
        {again ? t("reconnect") : t("connect")}
      </DialogTrigger>
      <DialogContent showCloseButton={false} className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{t("connectTitle", { ats: provider.name })}</DialogTitle>
        </DialogHeader>
        <Steps />
        <form id="connect-ats" onSubmit={connect} className="space-y-3">
          {form.fields.map((field) => (
            // The fields as in "Add member".
            <div
              key={field.name}
              className="relative rounded-xl border border-transparent transition-colors focus-within:border-ring-gradient"
            >
              <Input
                required
                type={"secret" in field ? "password" : "text"}
                autoComplete="off"
                maxLength={500}
                placeholder={
                  "placeholder" in field
                    ? field.placeholder
                    : t(field.label, { ats: provider.name })
                }
                aria-label={t(field.label, { ats: provider.name })}
                value={values[field.name] ?? ""}
                onChange={(event) =>
                  setValues({ ...values, [field.name]: event.target.value })
                }
                className="h-16 border-0 px-6 text-lg focus-visible:ring-0 md:text-lg"
              />
            </div>
          ))}
        </form>
        <DialogFooter>
          <DialogClose
            render={
              <Button
                variant="outline"
                className="h-10 px-5 text-base"
                disabled={saving}
              />
            }
          >
            {common("cancel")}
          </DialogClose>
          <Button
            type="submit"
            form="connect-ats"
            className="h-10 px-5 text-base"
            disabled={saving || !filled}
          >
            {t("connect")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
