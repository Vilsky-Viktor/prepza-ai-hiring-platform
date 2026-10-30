"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"

import { DEMO_PRESSED } from "@/features/landing/components/demo-panel"
import { DemoEmailField } from "@/features/landing/components/demo-popup"
import { buttonVariants } from "@/components/ui/button"

/** What the home page's box (components/common/start-test.tsx) asks a first-time user once the
 * description is sent, small: the question, the company's name (`name` as typed so far, a caret
 * while `typing`, `name` for the pointer), then cancel on the start side and continue
 * (`continue`) on the end side, dimmed until there's a name and pressed in while `pressed`. */
export function DemoFirstCompany({
  name,
  typing,
  pressed,
}: {
  name: string
  typing: boolean
  pressed: boolean
}) {
  const t = useTranslations("start")
  const common = useTranslations("common")

  return (
    <div className="flex flex-1 flex-col gap-4 p-2 text-base">
      <p className="font-heading text-xl font-medium">{t("firstCompany")}</p>
      <DemoEmailField
        target="name"
        className="bg-background"
        email={name}
        typing={typing}
        placeholder={t("companyName")}
      />
      <div className="flex items-center justify-between gap-3 pt-1">
        <span
          className={buttonVariants({
            variant: "ghost",
            className: "h-11 px-4 text-base",
          })}
        >
          {common("cancel")}
        </span>
        <span
          data-demo-target="continue"
          className={buttonVariants({
            className: cn(
              "h-11 px-6 text-base transition-opacity",
              !name && "opacity-50",
              pressed && DEMO_PRESSED
            ),
          })}
        >
          {t("continue")}
        </span>
      </div>
    </div>
  )
}
