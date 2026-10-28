"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"

import {
  DemoEmailField,
  DemoPopup,
} from "@/features/landing/components/demo-popup"
import { buttonVariants } from "@/components/ui/button"

/** The invite dialog (features/company/components/invite-candidate.tsx), small, over the
 * whole panel while `open`: its title, the candidate's email (`email` as typed so far, a caret
 * while `typing`), then cancel and invite, ringed while `pressed`. */
export function DemoInvitePopup({
  open,
  email,
  typing,
  pressed,
  emailRef,
  sendRef,
}: {
  open: boolean
  email: string
  typing: boolean
  pressed: boolean
  emailRef: React.Ref<HTMLDivElement>
  sendRef: React.Ref<HTMLSpanElement>
}) {
  const t = useTranslations("interviews")
  const common = useTranslations("common")

  return (
    <DemoPopup open={open}>
      <p className="font-heading text-xl leading-none font-medium">
        {t("newCandidate")}
      </p>
      <DemoEmailField
        ref={emailRef}
        email={email}
        typing={typing}
        placeholder="candidate@example.com"
      />
      <div className="flex justify-end gap-2">
        <span
          className={buttonVariants({
            variant: "outline",
            className: "h-9 px-4 text-base",
          })}
        >
          {common("cancel")}
        </span>
        <span
          ref={sendRef}
          className={buttonVariants({
            className: cn(
              "h-9 px-4 text-base transition-opacity",
              !email && "opacity-50",
              pressed && "ring-3 ring-ring/50"
            ),
          })}
        >
          {t("invite")}
        </span>
      </div>
    </DemoPopup>
  )
}
