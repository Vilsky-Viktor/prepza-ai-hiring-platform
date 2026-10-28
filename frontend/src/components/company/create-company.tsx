"use client"

import { cn } from "cn"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

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
import { MAX_COMPANY_NAME_LENGTH } from "@/constants/limits"
import { COMPANIES_CHANGED } from "@/constants/notifications"
import { useHumanCheck } from "@/hooks/use-human-check"
import { apiErrorMessage, apiFetch, serviceRefusal } from "@/lib/api"
import { refreshVerification } from "@/lib/auth"
import { humanHeaders } from "@/lib/human-check"
import type { Company } from "@/types/company"

export function CreateCompany({ templateId }: { templateId?: string }) {
  const t = useTranslations("company")
  const common = useTranslations("common")
  const router = useRouter()
  const [open, setOpen] = useState(false)
  // Ready once the dialog with its form opens.
  useHumanCheck(open)
  const [name, setName] = useState("")
  const [saving, setSaving] = useState(false)
  // The server's reason the name can't be used (it's taken), shown under the field.
  const [nameError, setNameError] = useState<string | null>(null)

  function handleOpen(next: boolean) {
    if (saving) {
      return
    }

    setOpen(next)

    if (!next) {
      setName("")
      setNameError(null)
    }
  }

  async function create(event: React.FormEvent) {
    event.preventDefault()

    if (!name.trim() || saving) {
      return
    }

    setSaving(true)
    // An email verified since signing in counts at once (a company needs a verified one).
    await refreshVerification()

    try {
      const company = await apiFetch<Company>("/companies/companies", {
        method: "POST",
        body: JSON.stringify({ name: name.trim() }),
        headers: await humanHeaders(),
      })
      // The bell hears the new company at once.
      window.dispatchEvent(new Event(COMPANIES_CHANGED))
      // Choosing where to use a free test: the new company opens on that test.
      router.replace(
        templateId
          ? `/companies/${company.id}/templates/${templateId}`
          : `/companies/${company.id}/interviews`
      )
    } catch (error) {
      // A name taken or as many companies owned as one may (409), or a name too short (422),
      // is said under the field.
      const refused = serviceRefusal(error, [409, 422])

      if (refused) {
        setNameError(refused)
      } else {
        toast.error(apiErrorMessage(error, t("createFailed")))
      }

      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogTrigger
        data-testid="new-company"
        render={<Button className="h-12 px-6 text-base max-sm:w-full" />}
      >
        {t("new")}
      </DialogTrigger>
      <DialogContent showCloseButton={false} className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("new")}</DialogTitle>
        </DialogHeader>
        <form id="create-company-form" onSubmit={create}>
          <div
            className={cn(
              "relative rounded-xl border border-transparent transition-colors focus-within:border-ring-gradient",
              nameError && "border-destructive focus-within:border-destructive"
            )}
          >
            <Input
              required
              maxLength={MAX_COMPANY_NAME_LENGTH}
              placeholder={t("name")}
              aria-label={t("name")}
              value={name}
              onChange={(event) => {
                setName(event.target.value)
                setNameError(null)
              }}
              aria-invalid={nameError !== null}
              aria-describedby={nameError ? "company-name-error" : undefined}
              className="h-16 border-0 px-6 text-lg focus-visible:ring-0 md:text-lg"
            />
          </div>
          {nameError && (
            <p
              id="company-name-error"
              role="alert"
              className="px-6 pt-2 text-sm text-destructive"
            >
              {nameError}
            </p>
          )}
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
            form="create-company-form"
            className="h-10 px-5 text-base"
            disabled={saving || !name.trim()}
          >
            {t("create")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
