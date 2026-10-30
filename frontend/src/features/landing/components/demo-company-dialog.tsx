"use client"

import { cn } from "cn"
import { CheckIcon, PlusIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { DEMO_PRESSED } from "@/features/landing/components/demo-panel"
import { DemoPopup } from "@/features/landing/components/demo-popup"
import { buttonVariants } from "@/components/ui/button"
import { FloatingInput } from "@/components/ui/floating-field"
import { DEMO_OTHER_COMPANY } from "@/config/create-demo"

// A company card: grey, its border shown once chosen.
const CARD =
  "flex w-full items-center gap-3 rounded-xl border border-transparent bg-surface p-4 text-start text-base transition-colors"

/** The window the home page's box opens once the description is sent
 * (components/common/start-company-dialog.tsx), small, over the dimmed box while `open`: which
 * company the interview is for, the user's company chosen at first and a new one (the
 * pointer's "newCompany"); once `adding`, the new one chosen and its name field fading in under
 * them, its room kept from the start so the window never changes size (`name` as typed so far,
 * ringed while `typing`; the pointer's "name"); then cancel and continue (the pointer's
 * "continue"), pressed in while `pressed`. */
export function DemoCompanyDialog({
  open,
  adding,
  name,
  typing,
  pressed,
}: {
  open: boolean
  adding: boolean
  name: string
  typing: boolean
  pressed: boolean
}) {
  const t = useTranslations("start")
  const common = useTranslations("common")

  return (
    <DemoPopup open={open}>
      <p className="font-heading text-xl leading-none font-medium">
        {t("whichCompany")}
      </p>
      {/* As the real list, with the scrollbar's room at its end. */}
      <div className="-me-4 space-y-4 p-1 pe-5">
        <div className="space-y-2">
          <span className={cn(CARD, !adding && "border-ring")}>
            <CheckIcon
              className={cn(
                "size-4 shrink-0",
                adding ? "invisible" : "text-primary"
              )}
            />
            <span className="min-w-0 truncate">{DEMO_OTHER_COMPANY}</span>
          </span>
          <span
            data-demo-target="newCompany"
            className={cn(CARD, adding && "border-ring")}
          >
            <PlusIcon className="size-4 shrink-0 text-muted-foreground" />
            <span className="min-w-0 truncate">{t("newCompany")}</span>
          </span>
        </div>
        <span
          data-demo-target="name"
          className={cn(
            "block transition-opacity duration-300",
            !adding && "invisible opacity-0"
          )}
        >
          <FloatingInput
            label={t("companyName")}
            value={name}
            readOnly
            className={cn(typing && "border-ring")}
          />
        </span>
      </div>
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
              adding && !name && "opacity-50",
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
