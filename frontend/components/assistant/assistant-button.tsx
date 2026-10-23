"use client"

import { SparklesIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { useAssistant } from "@/components/assistant/assistant-provider"
import { useAuth } from "@/components/auth-provider"
import { Button } from "@/components/ui/button"

/** "ask mira" in the header, all lowercase: an outline pill the size of Sign in, a bright arc
 * circling its brand-blue border, that opens the assistant, signed in or not. Below md, where
 * the header is too narrow for its label, the icon alone, with the label as its name. */
export function AssistantButton() {
  const t = useTranslations("landing")
  const toggle = useAssistant()
  const { loading } = useAuth()

  if (loading) {
    return null
  }

  return (
    <Button
      variant="ghost"
      className="agent-border gap-1.5 px-4 lowercase max-md:w-8 max-md:px-0"
      aria-label={t("askAgent")}
      onClick={toggle}
      data-assistant-toggle
    >
      <SparklesIcon aria-hidden className="size-4 text-primary" />
      <span aria-hidden className="max-md:hidden">
        {t("askAgent")}
      </span>
    </Button>
  )
}
