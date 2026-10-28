import { cn } from "cn"
import { ArrowRightIcon, CheckIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { buttonVariants } from "@/components/ui/button"
import { ASK_AGENT_EMAIL, ASK_AGENT_INTERVIEW } from "@/config/ask-agent-demo"
import { CARD } from "@/config/cards"

export type DemoCardState = "pending" | "running" | "done"

/** The card the assistant shows before it invites a candidate (components/assistant/
 * action-card.tsx) as a small picture: what it will do, with the email, Confirm (`confirmRef`,
 * ringed while `pressed`) and Cancel; then Done, with the candidates' page. */
export function DemoActionCard({
  state,
  confirmRef,
  pressed,
}: {
  state: DemoCardState
  confirmRef: React.Ref<HTMLSpanElement>
  pressed: boolean
}) {
  const t = useTranslations("assistant.actions")
  const pages = useTranslations("assistant.pages")

  return (
    <li className={`space-y-3 ${CARD} text-sm`}>
      <div className="space-y-0.5">
        <p className="font-medium">{t("titles.invite_candidate")}</p>
        <p>{ASK_AGENT_INTERVIEW}</p>
      </div>
      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
        <dt className="text-muted-foreground">{t("fields.email")}</dt>
        <dd className="break-words">{ASK_AGENT_EMAIL}</dd>
      </dl>
      {state === "done" ? (
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex items-center gap-1.5 text-muted-foreground">
            <CheckIcon className="size-4" />
            {t("done")}
          </span>
          <span className={buttonVariants({ variant: "outline", size: "sm" })}>
            {pages("candidates")}
            <ArrowRightIcon
              data-icon="inline-end"
              className="rtl:-scale-x-100"
            />
          </span>
        </div>
      ) : (
        <div className="flex flex-wrap gap-2">
          <span
            ref={confirmRef}
            className={buttonVariants({
              className: cn(
                "h-9 px-4",
                state === "running" && "opacity-50",
                pressed && "ring-3 ring-ring/50"
              ),
            })}
          >
            {state === "running" ? t("running") : t("confirm")}
          </span>
          <span
            className={buttonVariants({
              variant: "outline",
              className: cn("h-9 px-4", state === "running" && "opacity-50"),
            })}
          >
            {t("cancel")}
          </span>
        </div>
      )}
    </li>
  )
}
