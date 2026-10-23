"use client"

import { cn } from "cn"
import { SparklesIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { useAssistant } from "@/components/assistant/assistant-provider"
import { Button } from "@/components/ui/button"

/** "ask mira", all lowercase: opens the assistant's panel, signed in or not. The size of the demos button,
 * its brand-blue border circled by a bright arc, like the header's. */
export function AskAgentButton({ className }: { className?: string }) {
  const t = useTranslations("landing")
  const toggle = useAssistant()

  return (
    <Button
      variant="ghost"
      className={cn(
        "agent-border h-12 gap-2 px-6 text-base lowercase",
        className
      )}
      onClick={toggle}
      data-assistant-toggle
    >
      <SparklesIcon aria-hidden className="size-5 text-primary" />
      {/* One flex item, so the name sits a single space from "ask". */}
      <span>{t("askAgent")}</span>
    </Button>
  )
}
