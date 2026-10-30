"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"

import { DemoPopup } from "@/features/landing/components/demo-popup"
import { DEMO_PRESSED } from "@/features/landing/components/demo-panel"
import { INVITE_TAB_ICONS } from "@/features/company/components/invite-tab-icons"
import { TabNav } from "@/components/common/tab-nav"
import { buttonVariants } from "@/components/ui/button"
import { FloatingInput } from "@/components/ui/floating-field"
import { DEMO_INVITE_NAME } from "@/config/create-demo"
import { INVITE_TABS } from "@/config/invites"

const NOTHING = () => {}

/** The invite dialog (features/company/components/invite-candidate.tsx), over the whole frame
 * while `open`: its title, its real tabs (one email, a list, a file) with the first open, the
 * candidate's email (`email` as typed so far, its field in use while `typing`; the pointer's
 * "email") and name, then cancel and invite (the pointer's "sendInvite"),
 * pressed in while `pressed`. */
export function DemoInvitePopup({
  open,
  email,
  typing,
  pressed,
}: {
  open: boolean
  email: string
  typing: boolean
  pressed: boolean
}) {
  const t = useTranslations("interviews")
  const common = useTranslations("common")

  return (
    <DemoPopup open={open}>
      <p className="font-heading text-xl leading-none font-medium">
        {t("newCandidate")}
      </p>
      <TabNav
        items={INVITE_TABS.map((id) => ({
          id,
          label: t(`inviteTab.${id}`),
          icon: INVITE_TAB_ICONS[id],
        }))}
        current="one"
        onSelect={NOTHING}
      />
      <div className="space-y-3">
        <span data-demo-target="email" className="block">
          <FloatingInput
            label={t("candidateEmail")}
            placeholder="candidate@example.com"
            value={email}
            readOnly
            className={cn(typing && "border-ring")}
          />
        </span>
        <FloatingInput
          label={t("candidateName")}
          placeholder={DEMO_INVITE_NAME}
          value=""
          readOnly
        />
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
          data-demo-target="sendInvite"
          className={buttonVariants({
            className: cn(
              "h-10 px-5 text-base transition-opacity",
              !email && "opacity-50",
              pressed && DEMO_PRESSED
            ),
          })}
        >
          {t("invite")}
        </span>
      </div>
    </DemoPopup>
  )
}
