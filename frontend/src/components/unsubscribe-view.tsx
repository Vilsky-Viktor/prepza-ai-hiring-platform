"use client"

import Link from "next/link"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { useAuth } from "@/providers/auth-provider"
import { Button } from "@/components/ui/button"
import { LinkStatus } from "@/components/link-status"
import { apiFetch } from "@/lib/api"
import { bdi } from "@/lib/bidi"
import { useLinkData } from "@/hooks/use-link-data"
import type { UnsubscribeLink } from "@/types/notifications"

/** Says what the link stops and asks to confirm: opening it changes nothing, as mail scanners
 * open links too. Confirming posts the link; the API checks it and applies it. */
export function UnsubscribeView({ token }: { token: string }) {
  const t = useTranslations("unsubscribe")
  const { user } = useAuth()
  const [saving, setSaving] = useState(false)
  const [done, setDone] = useState(false)
  const path = `/notifications/unsubscribe/${encodeURIComponent(token)}`
  const { data: link, status, retry } = useLinkData<UnsubscribeLink>(path)

  async function confirm() {
    setSaving(true)

    try {
      await apiFetch(path, { method: "POST" })
      setDone(true)
    } catch {
      toast.error(t("failed"))
      setSaving(false)
    }
  }

  if (status !== "ready" || !link) {
    return (
      <LinkStatus
        status={status === "ready" ? "loading" : status}
        invalid={t("invalid")}
        onRetry={retry}
      />
    )
  }

  return (
    <div className="w-full space-y-8 text-center">
      <div className="space-y-4">
        <h1 className="font-heading text-4xl font-medium tracking-tight text-balance sm:text-5xl">
          {done ? t("done") : t("title")}
        </h1>
        <p className="text-base text-pretty text-muted-foreground">
          {t.rich(`what.${link.type}`, { company: link.company ?? "", ...bdi })}
        </p>
      </div>
      {!done ? (
        <Button
          className="h-12 px-6 text-base"
          disabled={saving}
          onClick={confirm}
        >
          {t("confirm")}
        </Button>
      ) : user ? (
        <Button
          variant="outline"
          className="h-12 px-6 text-base"
          render={<Link href="/settings" />}
          nativeButton={false}
        >
          {t("settings")}
        </Button>
      ) : null}
    </div>
  )
}
