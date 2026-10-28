"use client"

import { cn } from "cn"
import { DownloadIcon, Share2Icon } from "lucide-react"
import { useTranslations } from "next-intl"

import { CHAT_APPS } from "@/components/common/chat-apps"
import {
  DemoEmailField,
  DemoPopup,
} from "@/features/landing/components/demo-popup"
import { buttonVariants } from "@/components/ui/button"

// A report action's icon, like the page's icon buttons, a size down.
const ACTION =
  "flex size-10 shrink-0 items-center justify-center rounded-xl text-muted-foreground transition-shadow"

/** A report's two actions, small, for the landing: download its PDF and share it; `shareRef`
 * for the pointer, the share icon `pressed` as it's clicked. */
export function DemoReportActions({
  shareRef,
  pressed,
}: {
  shareRef: React.Ref<HTMLSpanElement>
  pressed: boolean
}) {
  return (
    <span className="flex shrink-0 items-center">
      <span className={ACTION}>
        <DownloadIcon className="size-5" />
      </span>
      <span
        ref={shareRef}
        className={cn(ACTION, pressed && "bg-surface ring-3 ring-ring/50")}
      >
        <Share2Icon className="size-5" />
      </span>
    </span>
  )
}

/** The share popup, small, over the whole panel while `open`: its title and the chat apps that
 * get a text summary, the recipient's email (`email` as typed so far, a caret while `typing`),
 * then cancel and "send PDF". `pressed` names what's being clicked. */
export function DemoSharePopup({
  open,
  email,
  typing,
  pressed,
  emailRef,
  sendRef,
  whatsAppRef,
}: {
  open: boolean
  email: string
  typing: boolean
  pressed: "send" | "whatsApp" | null
  emailRef: React.Ref<HTMLDivElement>
  sendRef: React.Ref<HTMLSpanElement>
  whatsAppRef: React.Ref<HTMLSpanElement>
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
              ref={index === 0 ? whatsAppRef : undefined}
              className={cn(
                "flex size-10 items-center justify-center rounded-xl text-muted-foreground transition-shadow",
                index === 0 &&
                  pressed === "whatsApp" &&
                  "bg-surface text-foreground ring-3 ring-ring/50"
              )}
            >
              <Icon className="size-6" />
            </span>
          ))}
        </div>
      </div>
      <DemoEmailField
        ref={emailRef}
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
          ref={sendRef}
          className={buttonVariants({
            className: cn(
              "h-9 px-4 text-base transition-opacity",
              !email && "opacity-50",
              pressed === "send" && "ring-3 ring-ring/50"
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
