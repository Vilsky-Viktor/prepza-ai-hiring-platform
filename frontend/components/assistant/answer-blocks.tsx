"use client"

import { cn } from "cn"
import { ArrowRightIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import {
  ActionCard,
  type CardActions,
} from "@/components/assistant/action-card"
import { BalanceTooltip } from "@/components/billing/balance-tooltip"
import {
  CandidateTable,
  InterviewTable,
} from "@/components/assistant/compact-rows"
import { LocalizedLink } from "@/components/localized-link"
import { SignInOptions } from "@/components/sign-in-options"
import { buttonVariants } from "@/components/ui/button"
import { PAGE_LABELS } from "@/constants/assistant"
import { answerParts, linkPage } from "@/lib/assistant"
import type { AssistantBlock } from "@/types/assistant"
import { WARNING_TONE } from "@/constants/tones"

type Item = Record<string, unknown>

/** A balance: the company's name when there are several, and its credits (amber when low), as
 * the company's header shows them. */
function CreditsItem({ item }: { item: Item }) {
  const t = useTranslations("company")
  const available = item.available as number

  return (
    <>
      <span className="min-w-0 truncate text-lg font-medium">
        {item.name as string | undefined}
      </span>
      <span className="shrink-0 text-base text-muted-foreground">
        <BalanceTooltip
          className={cn(
            "font-medium text-foreground tabular-nums",
            Boolean(item.low) && WARNING_TONE
          )}
          shown={available}
          balance={available}
        />{" "}
        {t("creditsLeft", { count: available })}
      </span>
    </>
  )
}

const ROW = "flex items-center justify-between gap-4 p-4"
// The blocks showing candidates: a list, or one candidate's results.
const CANDIDATE_KINDS = ["candidate_rows", "scorecard_summary"]

/** A balance's row, opening its page when it has one. */
function CreditsRow({
  item,
  href,
  onNavigate,
}: {
  item: Item
  href: string | null
  onNavigate: () => void
}) {
  if (!href) {
    return (
      <div className={ROW}>
        <CreditsItem item={item} />
      </div>
    )
  }

  return (
    <LocalizedLink
      href={href}
      onClick={onNavigate}
      className={cn(
        ROW,
        "transition-colors hover:bg-muted/50 active:bg-muted/50"
      )}
    >
      <CreditsItem item={item} />
    </LocalizedLink>
  )
}

/** What an answer's tools found: candidates and interviews as compact tables (at most 10 rows,
 * with a link to the page with all of them), balances as the company header shows them, each
 * opening its page; then links to the pages the rest came from, and a
 * sign-in card when a visitor asked to sign in. */
export function AnswerBlocks({
  blocks,
  actions,
  onNavigate,
}: {
  blocks: AssistantBlock[]
  actions: CardActions
  onNavigate: () => void
}) {
  const t = useTranslations("assistant.pages")
  const named = useTranslations("assistant.actions")
  const card = useTranslations("assistant")
  const { rows, links, signIn, cards } = answerParts(blocks)

  return (
    <div className="space-y-3">
      {rows.map(
        (block, index) =>
          block.items.length > 0 && (
            <div key={index} className="space-y-2">
              {CANDIDATE_KINDS.includes(block.kind) ? (
                <CandidateTable rows={block.items} onNavigate={onNavigate} />
              ) : block.kind === "interview" ? (
                <InterviewTable rows={block.items} onNavigate={onNavigate} />
              ) : (
                <ul className="divide-y overflow-hidden rounded-2xl border">
                  {block.items.map(({ item, href }, row) => (
                    <li key={row}>
                      <CreditsRow
                        item={item}
                        href={href}
                        onNavigate={onNavigate}
                      />
                    </li>
                  ))}
                </ul>
              )}
              {/* The page with all of the list, when there's one. */}
              {block.all && (
                <LocalizedLink
                  href={block.all}
                  onClick={onNavigate}
                  data-testid="see-all"
                  className={buttonVariants({ variant: "outline", size: "sm" })}
                >
                  {card("seeAll")}
                  <ArrowRightIcon
                    data-icon="inline-end"
                    className="rtl:-scale-x-100"
                  />
                </LocalizedLink>
              )}
            </div>
          )
      )}
      {cards.map((card) => (
        <ActionCard
          key={card.action_id}
          card={card}
          actions={actions}
          onNavigate={onNavigate}
        />
      ))}
      {signIn && (
        <div className="space-y-4 rounded-2xl border p-4">
          <p className="text-sm text-muted-foreground">{card("signInCard")}</p>
          <SignInOptions first={signIn.provider} />
        </div>
      )}
      {links.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {links.map(({ href, label, page }) => {
            const key = (page && PAGE_LABELS[page]) ?? linkPage(href)

            return (
              <LocalizedLink
                key={href}
                href={href}
                onClick={onNavigate}
                className={buttonVariants({ variant: "outline", size: "sm" })}
              >
                <span className={label ? "normal-case" : undefined}>
                  {label
                    ? named("openNamed", { name: label })
                    : key
                      ? t(key)
                      : t("open")}
                </span>
                <ArrowRightIcon
                  data-icon="inline-end"
                  className="rtl:-scale-x-100"
                />
              </LocalizedLink>
            )
          })}
        </div>
      )}
    </div>
  )
}
