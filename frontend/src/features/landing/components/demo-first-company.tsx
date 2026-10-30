"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"

import { DEMO_PRESSED } from "@/features/landing/components/demo-panel"
import { DemoPopup } from "@/features/landing/components/demo-popup"
import { buttonVariants } from "@/components/ui/button"
import { FloatingInput } from "@/components/ui/floating-field"

/** The window the home page's box opens once the description is sent, for a first-time user
 * (components/common/start-company-dialog.tsx), small, over the dimmed box while `open`: the
 * question, the company's name (`name` as typed so far, ringed while `typing`; the pointer's
 * "name"), then cancel and continue (the pointer's "continue"), dimmed until there's a name and
 * pressed in while `pressed`. */
export function DemoFirstCompany({
  open,
  name,
  typing,
  pressed,
}: {
  open: boolean
  name: string
  typing: boolean
  pressed: boolean
}) {
  const t = useTranslations("start")
  const common = useTranslations("common")

  return (
    <DemoPopup open={open}>
      <p className="font-heading text-xl leading-none font-medium">
        {t("firstCompany")}
      </p>
      <span data-demo-target="name" className="block">
        <FloatingInput
          label={t("companyName")}
          value={name}
          readOnly
          className={cn(typing && "border-ring")}
        />
      </span>
      <div className="flex justify-end gap-2">
        <span
          className={buttonVariants({
            variant: "outline",
            className: "h-10 px-5 text-base",
          })}
        >
          {common("cancel")}
        </span>
        <span
          data-demo-target="continue"
          className={buttonVariants({
            className: cn(
              "h-10 px-5 text-base transition-opacity",
              !name && "opacity-50",
              pressed && DEMO_PRESSED
            ),
          })}
        >
          {t("continue")}
        </span>
      </div>
    </DemoPopup>
  )
}
