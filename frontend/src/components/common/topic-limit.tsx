"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { Input } from "@/components/ui/input"
import { apiErrorMessage, apiFetch } from "@/lib/api"

export function TopicLimit({
  path,
  count,
  limit,
}: {
  path: string
  count: number
  limit: number | null
}) {
  const t = useTranslations("questions")
  const router = useRouter()
  const saved = String(limit ?? count)
  const [value, setValue] = useState(saved)
  const [saving, setSaving] = useState(false)

  async function save() {
    const number = Number(value.trim())

    if (value.trim() === saved) {
      return
    }

    if (!Number.isInteger(number) || number < 0 || number > count) {
      toast.error(t("limitRange", { count }))
      setValue(saved)

      return
    }

    setSaving(true)

    try {
      await apiFetch(path, {
        method: "PUT",
        body: JSON.stringify({ limit: number }),
      })
      router.refresh()
    } catch (error) {
      setValue(saved)
      toast.error(apiErrorMessage(error, t("limitFailed")))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Input
      type="number"
      inputMode="numeric"
      min={0}
      max={count}
      value={value}
      disabled={saving}
      aria-label={t("limit")}
      // "What's next" focuses the first one.
      data-topic-limit
      // A transparent border at rest keeps the 1px the focus border draws in.
      className="h-9 w-14 [appearance:textfield] border-transparent px-1 text-center text-base font-semibold text-foreground tabular-nums md:text-base [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
      onChange={(event) => setValue(event.target.value)}
      onBlur={save}
      onKeyDown={(event) => {
        if (event.key === "Enter") {
          event.currentTarget.blur()
        }
      }}
    />
  )
}
