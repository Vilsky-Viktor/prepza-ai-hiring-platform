"use client"

import { CopyIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { toast } from "sonner"

import { InputAction } from "@/components/input-action"
import { useOrigin } from "@/lib/origin"

/** A link on this site (`path`), in a read-only field with a copy button. */
export function CopyField({ path }: { path: string }) {
  const common = useTranslations("common")
  const origin = useOrigin()

  return (
    <CopyValue
      value={origin ? `${origin}${path}` : ""}
      label={common("copyLink")}
      copied={common("linkCopied")}
    />
  )
}

/** Any text to paste elsewhere, in a read-only field with a copy button named `label`. */
export function CopyValue({
  value,
  label,
  copied,
}: {
  value: string
  label: string
  copied: string
}) {
  async function copy(event: React.FormEvent) {
    event.preventDefault()

    if (!value) {
      return
    }

    await navigator.clipboard.writeText(value)
    toast.success(copied)
  }

  return (
    <form onSubmit={copy} className="flex">
      <InputAction
        readOnly
        value={value}
        aria-label={label}
        action={label}
        disabled={!value}
        icon={<CopyIcon className="size-5" />}
        onFocus={(event) => event.target.select()}
      />
    </form>
  )
}
