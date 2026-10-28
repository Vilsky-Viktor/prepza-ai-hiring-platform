"use client"

import { useTranslations } from "next-intl"
import { useEffect } from "react"
import { toast } from "sonner"

import {
  REFERRAL_CODE,
  REFERRAL_COOKIE,
  REFERRAL_DAYS,
  REFERRAL_PARAM,
} from "@/config/referral"

/** A referral link asks before it's kept: the cookie serves the referral, not the page the
 * visitor asked for, so it's set only once they agree (EU cookie consent). */
export function ReferralNotice() {
  const t = useTranslations("referral")

  useEffect(() => {
    const code = new URLSearchParams(window.location.search).get(REFERRAL_PARAM)
    const kept = document.cookie
      .split("; ")
      .some((cookie) => cookie.startsWith(`${REFERRAL_COOKIE}=`))

    if (!code || !REFERRAL_CODE.test(code) || kept) {
      return
    }

    const secure = window.location.protocol === "https:" ? "; secure" : ""
    toast(t("keepTitle"), {
      // One notice, however often the page mounts.
      id: REFERRAL_COOKIE,
      description: t("keepText"),
      duration: Infinity,
      action: {
        label: t("keep"),
        onClick: () => {
          document.cookie = `${REFERRAL_COOKIE}=${code}; path=/; max-age=${REFERRAL_DAYS * 24 * 60 * 60}; samesite=lax${secure}`
        },
      },
      cancel: { label: t("dontKeep"), onClick: () => {} },
    })
  }, [t])

  return null
}
