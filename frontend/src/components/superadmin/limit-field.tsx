"use client"

import { RotateCcwIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { IconButton } from "@/components/common/icon-button"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import type { Limit, Limits } from "@/types/superadmin"

const PATH = "/billing/superadmin/limits"

/** One limit's value, editable: Save sends it (the API refuses one out of the limit's bounds),
 * and once it differs from its default, a button sets it back. `label` names the field (paid or
 * unpaid beside each other). The API answers with every limit, which `onSaved` takes. */
export function LimitField({
  limit,
  label,
  onSaved,
}: {
  limit: Limit
  label: string
  onSaved: (limits: Limits) => void
}) {
  const t = useTranslations("superadmin")
  const [value, setValue] = useState(String(limit.value))
  const [busy, setBusy] = useState(false)
  const unit =
    limit.unit === "seconds"
      ? t("limitSecondsUnit")
      : limit.unit === "percent"
        ? "%"
        : null

  async function send(init: RequestInit) {
    setBusy(true)

    try {
      const saved = await apiFetch<Limits>(`${PATH}/${limit.name}`, init)
      onSaved(saved)
      const shown = saved.limits
        .flatMap((found) => [found, found.unpaid])
        .find((found) => found?.name === limit.name)
      setValue(String(shown?.value ?? limit.default))
      toast.success(t("limitSaved"))
    } catch (error) {
      toast.error(apiErrorMessage(error, t("limitFailed")))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form
      className="flex items-center gap-2"
      onSubmit={(event) => {
        event.preventDefault()
        send({ method: "PUT", body: JSON.stringify({ value: Number(value) }) })
      }}
    >
      <span className="relative">
        <Input
          required
          type="number"
          step="any"
          min={limit.lowest}
          max={limit.highest}
          aria-label={label}
          value={value}
          onChange={(event) => setValue(event.target.value)}
          className={`h-8 w-32 text-sm tabular-nums ${unit ? "pe-8" : ""}`}
        />
        {unit && (
          <span className="pointer-events-none absolute end-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
            {unit}
          </span>
        )}
      </span>
      <Button
        type="submit"
        variant="outline"
        size="sm"
        className="h-8 px-3 text-sm"
        disabled={busy || value === String(limit.value)}
      >
        {t("limitSave")}
      </Button>
      {limit.changed && (
        <IconButton
          label={t("limitReset")}
          disabled={busy}
          className="size-8"
          onClick={() => send({ method: "DELETE" })}
        >
          <RotateCcwIcon aria-hidden className="size-4" />
        </IconButton>
      )}
    </form>
  )
}
