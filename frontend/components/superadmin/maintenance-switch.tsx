"use client"

import { cn } from "cn"
import { WrenchIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { CornerSign } from "@/components/corner-sign"
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
import { Switch } from "@/components/ui/switch"
import { SIGN_CARD } from "@/constants/cards"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import type { MaintenanceSwitchState } from "@/types/company"

const PATH = "/companies/superadmin/maintenance"

/** Maintenance mode, as the pause's card: while on, the site is closed to everyone but
 * superadmins. Turning it on first says how many candidates are in an interview right now. */
export function MaintenanceSwitch({ on: initial }: { on: boolean }) {
  const t = useTranslations("superadmin")
  const common = useTranslations("common")
  const [on, setOn] = useState(initial)
  const [saving, setSaving] = useState(false)
  // Set while the dialog asks to confirm: the candidates in an interview, null if not counted.
  const [confirming, setConfirming] = useState<{ running: number | null }>()

  async function save(next: boolean) {
    setSaving(true)

    try {
      const saved = await apiFetch<MaintenanceSwitchState>(PATH, {
        method: "PUT",
        body: JSON.stringify({ on: next }),
      })
      setOn(saved.on)
      setConfirming(undefined)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("maintenanceFailed")))
    } finally {
      setSaving(false)
    }
  }

  async function toggle(next: boolean) {
    if (!next) {
      await save(false)

      return
    }

    setSaving(true)

    try {
      const state = await apiFetch<MaintenanceSwitchState>(PATH)
      setConfirming({ running: state.running })
    } catch (error) {
      toast.error(apiErrorMessage(error, t("maintenanceFailed")))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={cn(SIGN_CARD, "p-5 ps-20")}>
      <CornerSign>
        <WrenchIcon className="text-primary" />
      </CornerSign>
      <label className="flex cursor-pointer items-center gap-4 text-base">
        <span className="min-w-0 flex-1 space-y-1">
          <span className="block font-medium">{t("maintenanceTitle")}</span>
          <span className="block text-sm text-muted-foreground">
            {t("maintenanceText")}
          </span>
        </span>
        <Switch checked={on} disabled={saving} onCheckedChange={toggle} />
      </label>
      <Dialog
        open={confirming !== undefined}
        onOpenChange={(open) => {
          if (!open && !saving) {
            setConfirming(undefined)
          }
        }}
      >
        <DialogContent showCloseButton={false}>
          <DialogHeader>
            <DialogTitle className="no-dot">
              {t("maintenanceConfirmTitle")}
            </DialogTitle>
            <DialogDescription>
              {confirming?.running == null
                ? t("maintenanceRunningUnknown")
                : t("maintenanceRunning", { count: confirming.running })}
            </DialogDescription>
          </DialogHeader>
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
              variant="destructive"
              className="h-10 px-5 text-base"
              disabled={saving}
              onClick={() => save(true)}
            >
              {t("maintenanceTurnOn")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
