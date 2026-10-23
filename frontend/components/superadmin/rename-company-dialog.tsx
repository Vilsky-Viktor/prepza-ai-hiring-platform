"use client"

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
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { MAX_COMPANY_NAME_LENGTH } from "@/constants/limits"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import type { SuperadminCompany } from "@/types/superadmin"

/** A superadmin renames a company, freeing a name an impersonator took; a name another company
 * has is refused with the API's message. */
export function RenameCompanyDialog({
  company,
  open,
  onOpenChange,
  onRenamed,
}: {
  company: Pick<SuperadminCompany, "id" | "name">
  open: boolean
  onOpenChange: (open: boolean) => void
  onRenamed: () => void
}) {
  const t = useTranslations("superadmin")
  const common = useTranslations("common")
  const [name, setName] = useState(company.name)
  const [saving, setSaving] = useState(false)

  async function save(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true)

    try {
      await apiFetch(`/companies/superadmin/companies/${company.id}/name`, {
        method: "PUT",
        body: JSON.stringify({ name }),
      })
      toast.success(t("companyRenamed"))
      onOpenChange(false)
      onRenamed()
    } catch (error) {
      toast.error(apiErrorMessage(error, t("actionFailed")))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !saving && onOpenChange(next)}>
      <DialogContent showCloseButton={false} className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("renameCompanyTitle")}</DialogTitle>
        </DialogHeader>
        <form id="rename-company-form" onSubmit={save}>
          <div className="relative rounded-xl border border-transparent transition-colors focus-within:border-ring-gradient">
            <Input
              required
              maxLength={MAX_COMPANY_NAME_LENGTH}
              aria-label={t("companyName")}
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="h-16 border-0 px-6 text-lg focus-visible:ring-0 md:text-lg"
            />
          </div>
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
            form="rename-company-form"
            className="h-10 px-5 text-base"
            disabled={saving || !name.trim() || name.trim() === company.name}
          >
            {common("save")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
