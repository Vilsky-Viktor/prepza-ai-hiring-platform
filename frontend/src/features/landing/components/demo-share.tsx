"use client"

import { cn } from "cn"
import { DownloadIcon, Share2Icon } from "lucide-react"
import { useTranslations } from "next-intl"

import { DEMO_PRESSED } from "@/features/landing/components/demo-panel"
import { CHAT_APPS } from "@/components/common/chat-apps"
import {
  DemoEmailField,
  DemoPopup,
} from "@/features/landing/components/demo-popup"
import { buttonVariants } from "@/components/ui/button"

/** A report's two actions (features/company/components/report-actions.tsx), as the page's icon
 * buttons (components/common/icon-button.tsx) for the landing: download its PDF and share it,
 * the pointer's "download" and "share", the one `pressed` pressed in. */
export function DemoReportActions({
  pressed,
}: {
  pressed: "download" | "share" | null
}) {
  const action = (name: "download" | "share", icon: React.ReactNode) => (
    <span
      data-demo-target={name}
      className={buttonVariants({
        variant: "ghost",
        size: "icon",
        className: cn(
          "size-12 shrink-0 text-muted-foreground",
          pressed === name && `bg-surface text-foreground ${DEMO_PRESSED}`
        ),
      })}
    >
      {icon}
    </span>
  )

  return (
    <span className="flex shrink-0 items-center">
      {action("download", <DownloadIcon className="size-6" />)}
      {action("share", <Share2Icon className="size-6" />)}
    </span>
  )
}

/** The share popup, small, over the whole panel while `open`: its title and the chat apps that
 * get a text summary, the recipient's email (`email` as typed so far, a caret while `typing`),
 * then cancel and "send PDF" (the pointer's "whatsApp", "email" and "send"). `pressed` names what's
 * being clicked. */
export function DemoSharePopup({
  open,
  email,
  typing,
  pressed,
}: {
  open: boolean
  email: string
  typing: boolean
  pressed: "send" | "whatsApp" | null
}) {
  const t = useTranslations("report")
  const common = useTranslations("common")

  return (
    <DemoPopup open={open}>
      <div className="flex items-center justify-between gap-3 max-sm:flex-col">
        <p className="font-heading text-xl leading-none font-medium">
          {t("shareTitle")}
        </p>
        <div className="flex flex-wrap items-center justify-center gap-0.5">
          <span className="me-1.5 text-sm text-muted-foreground lowercase max-sm:basis-full max-sm:text-center">
            {t("orSummary")}
          </span>
          {CHAT_APPS.map(({ name, Icon }, index) => (
            <span
              key={name}
              data-demo-target={index === 0 ? "whatsApp" : undefined}
              className={cn(
                "flex size-10 items-center justify-center rounded-xl text-muted-foreground transition-shadow",
                index === 0 &&
                  pressed === "whatsApp" &&
                  `bg-surface text-foreground ${DEMO_PRESSED}`
              )}
            >
              <Icon className="size-6" />
            </span>
          ))}
        </div>
      </div>
      <DemoEmailField
        target="email"
        email={email}
        typing={typing}
        placeholder="manager@example.com"
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
          data-demo-target="send"
          className={buttonVariants({
            className: cn(
              "h-9 px-4 text-base transition-opacity",
              !email && "opacity-50",
              pressed === "send" && DEMO_PRESSED
            ),
          })}
        >
          <span>
            {t.rich("send", {
              name: (chunks) => <span className="normal-case">{chunks}</span>,
            })}
          </span>
        </span>
      </div>
    </DemoPopup>
  )
}
