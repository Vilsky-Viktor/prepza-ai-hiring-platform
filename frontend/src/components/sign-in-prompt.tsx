"use client"

import { useTranslations } from "next-intl"

import { SignInOptions } from "@/components/sign-in-options"
import { CARD } from "@/config/cards"

/** A page that only asks to sign in: a title and the ways to sign in right there. */
export function SignInPrompt() {
  const t = useTranslations("signIn")

  return (
    <div
      className={`mx-auto flex w-full max-w-md flex-col items-center gap-6 ${CARD} text-center`}
    >
      <h2 className="font-heading text-2xl font-medium tracking-tight">
        {t("title")}
      </h2>
      <div className="w-full">
        <SignInOptions />
      </div>
    </div>
  )
}
