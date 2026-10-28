"use client"

import { usePathname, useRouter, useSearchParams } from "next/navigation"
import { useTranslations } from "next-intl"
import { useEffect } from "react"
import { toast } from "sonner"

/** Back from Slack: says how connecting went (the callback's ?slack=), then drops it from the
 * address so a reload doesn't say it again. */
export function SlackReturned() {
  const t = useTranslations("slack")
  const result = useSearchParams().get("slack")
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!result) {
      return
    }

    if (result === "connected") {
      toast.success(t("connected"), { id: "slack" })
    } else if (result === "failed") {
      toast.error(t("connectFailed"), { id: "slack" })
    }

    router.replace(pathname)
  }, [result, router, pathname, t])

  return null
}
