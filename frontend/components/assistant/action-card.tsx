"use client"

import { cn } from "cn"
import { ArrowRightIcon, CheckIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { LocalizedLink } from "@/components/localized-link"
import { Button, buttonVariants } from "@/components/ui/button"
import { previewValue } from "@/lib/action-values"
import { linkPage } from "@/lib/assistant"
import type { AssistantBlock } from "@/types/assistant"

export type CardActions = {
  onConfirm: (actionId: string) => void
  onCancel: (actionId: string) => void
  // While an answer streams, nothing can be confirmed.
  busy: boolean
  companyNames: Record<string, string>
}

/** An action the assistant prepared: what will happen, with exactly the values it runs with
 * (and a warning when it can't be undone), Confirm and Cancel; then how it ended, with the page
 * it made. */
export function ActionCard({
  card,
  actions,
  onNavigate,
}: {
  card: AssistantBlock
  actions: CardActions
  onNavigate: () => void
}) {
  const t = useTranslations("assistant.actions")
  const tool = card.tool ?? ""
  const state = card.state ?? "pending"
  // The company, unless the card is about it already.
  const named = card.company_id && actions.companyNames[card.company_id]
  const company = named !== card.subject ? named : null
  const fields = Object.entries(card.preview ?? {})

  return (
    <div
      className="space-y-3 rounded-2xl border p-4 text-sm"
      data-testid="action-card"
    >
      <div className="space-y-0.5">
        <p className="font-medium">
          {t.has(`titles.${tool}`) ? t(`titles.${tool}`) : t("generic")}
        </p>
        {card.subject && (
          <p className="bidi-auto break-words">{card.subject}</p>
        )}
      </div>
      {(company || fields.length > 0) && (
        <ActionFields tool={tool} company={company} fields={fields} />
      )}
      {state === "pending" && <ActionWarnings card={card} />}
      {(state === "pending" || state === "running") && (
        <ActionButtons card={card} actions={actions} />
      )}
      <ActionOutcome card={card} state={state} onNavigate={onNavigate} />
    </div>
  )
}

/** Before it's confirmed: the credits a removal gives back, and that it can't be undone. */
function ActionWarnings({ card }: { card: AssistantBlock }) {
  const t = useTranslations("assistant.actions")
  const companyText = useTranslations("company")

  return (
    <>
      {card.credits && (
        <p className="text-destructive">
          {companyText("removeCredits", {
            credits: card.credits.available,
            candidates: card.credits.candidates,
          })}
        </p>
      )}
      {card.destructive && <p className="text-destructive">{t("cantUndo")}</p>}
    </>
  )
}

/** The values an action runs with: its company, unless the card is about it already, and each
 * field under its name for this tool, else its general name, else its key. */
function ActionFields({
  tool,
  company,
  fields,
}: {
  tool: string
  company: string | null | undefined | false
  fields: [string, unknown][]
}) {
  const t = useTranslations("assistant.actions")

  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
      {company && (
        <>
          <dt className="text-muted-foreground">{t("fields.company")}</dt>
          <dd className="bidi-auto break-words">{company}</dd>
        </>
      )}
      {fields.map(([key, value]) => (
        <div key={key} className="contents">
          <dt className="text-muted-foreground">
            {t.has(`fieldsOf.${tool}.${key}`)
              ? t(`fieldsOf.${tool}.${key}`)
              : t.has(`fields.${key}`)
                ? t(`fields.${key}`)
                : key}
          </dt>
          <dd className="bidi-auto break-words whitespace-pre-wrap">
            {previewValue(key, value, t("yes"), t("no"))}
          </dd>
        </div>
      ))}
    </dl>
  )
}

/** Confirm and Cancel; neither while it runs or an answer streams. */
function ActionButtons({
  card,
  actions,
}: {
  card: AssistantBlock
  actions: CardActions
}) {
  const t = useTranslations("assistant.actions")
  const running = card.state === "running"

  return (
    <div className="flex flex-wrap gap-2">
      <Button
        variant={card.destructive ? "destructive" : "default"}
        className="h-9 px-4"
        disabled={running || actions.busy}
        onClick={() => actions.onConfirm(card.action_id!)}
      >
        {running ? t("running") : t("confirm")}
      </Button>
      <Button
        variant="outline"
        className="h-9 px-4"
        disabled={running || actions.busy}
        onClick={() => actions.onCancel(card.action_id!)}
      >
        {t("cancel")}
      </Button>
    </div>
  )
}

/** How an action ended: done, with the pages it made (by the name it made, else the page's
 * name, else "Open"); failed, with why; or cancelled. Nothing while it's pending or running. */
function ActionOutcome({
  card,
  state,
  onNavigate,
}: {
  card: AssistantBlock
  state: string
  onNavigate: () => void
}) {
  const t = useTranslations("assistant.actions")
  const pages = useTranslations("assistant.pages")

  if (state === "failed") {
    return <p className="text-destructive">{card.detail ?? t("failed")}</p>
  }

  if (state === "cancelled") {
    return <p className="text-muted-foreground">{t("cancelled")}</p>
  }

  if (state !== "done") {
    return null
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <span className="flex items-center gap-1.5 text-muted-foreground">
        <CheckIcon aria-hidden className="size-4" />
        {t("done")}
      </span>
      {card.links.map(
        (href) =>
          href && (
            <LocalizedLink
              key={href}
              href={href}
              onClick={onNavigate}
              className={cn(
                buttonVariants({ variant: "outline", size: "sm" }),
                // A name keeps its capitals in the lowercase button.
                card.result_label && "normal-case"
              )}
            >
              {card.result_label
                ? t("openNamed", { name: card.result_label })
                : pages.has(linkPage(href) ?? "")
                  ? pages(linkPage(href)!)
                  : pages("open")}
              <ArrowRightIcon
                data-icon="inline-end"
                className="rtl:-scale-x-100"
              />
            </LocalizedLink>
          )
      )}
    </div>
  )
}
