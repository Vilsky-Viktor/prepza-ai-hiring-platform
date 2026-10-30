"use client"

import { cn } from "cn"
import { MicIcon, XIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { DEMO_PRESSED } from "@/features/landing/components/demo-panel"
import { buttonVariants } from "@/components/ui/button"
import { DEMO_SITE } from "@/config/candidates-demo"

/** The browser's prompt for the microphone, small, at the picture's top start corner where a
 * browser shows it under its address bar: the site asking, what for, and its three answers, the
 * first (the pointer's "promptAllow") pressed in while `pressed`. Shown while `open`. */
export function DemoMicPrompt({
  open,
  pressed,
}: {
  open: boolean
  pressed: boolean
}) {
  const t = useTranslations("landing.candidates.micPrompt")
  const button = "h-8 w-full rounded-full px-4 text-sm normal-case"

  return (
    <div
      className={cn(
        "absolute start-4 top-4 z-5 w-72 space-y-3 rounded-xl bg-popover p-4 text-popover-foreground shadow-md ring-1 ring-foreground/10 transition-[opacity,translate] duration-200",
        !open && "invisible -translate-y-1 opacity-0"
      )}
    >
      <p className="flex items-center justify-between gap-3 text-sm font-medium">
        {t("asks", { site: DEMO_SITE })}
        <XIcon className="size-4 text-muted-foreground" />
      </p>
      <p className="flex items-center gap-3 text-sm">
        <MicIcon className="size-4 text-muted-foreground" />
        {t("microphone")}
      </p>
      <div className="space-y-2">
        <span
          data-demo-target="promptAllow"
          className={buttonVariants({
            variant: "outline",
            className: cn(button, pressed && DEMO_PRESSED),
          })}
        >
          {t("always")}
        </span>
        <span
          className={buttonVariants({ variant: "outline", className: button })}
        >
          {t("once")}
        </span>
        <span
          className={buttonVariants({ variant: "outline", className: button })}
        >
          {t("never")}
        </span>
      </div>
    </div>
  )
}
