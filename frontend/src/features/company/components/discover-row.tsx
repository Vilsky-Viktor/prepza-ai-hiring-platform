"use client"

import { CheckIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { LinkedInIcon } from "@/components/icons/brand-icons"
import { Button } from "@/components/ui/button"
import { ROUND_ICON_BUTTON } from "@/config/buttons"
import { useLocalTime } from "@/hooks/use-local-time"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { bdiText } from "@/lib/bidi"
import { formatPercent } from "@/lib/format"
import type { DiscoverPerson } from "@/types/company"

/** One person open to offers on an interview's Discover tab, laid out like a candidate's row:
 * their name with their LinkedIn profile as an icon, when they last practised and their latest
 * practice result on each of the interview's subjects (practice results, never a ranking), and,
 * for owners and admins (`canEdit`), the button that invites them as any candidate. */
export function DiscoverRow({
  person,
  invitePath,
  canEdit,
}: {
  person: DiscoverPerson
  invitePath: string
  canEdit: boolean
}) {
  const t = useTranslations("interviews")
  const locale = useLocale()
  const localTime = useLocalTime()
  const [state, setState] = useState<"idle" | "inviting" | "invited">("idle")
  const latest = person.results[0]?.finished_at
  const shownName = person.name ?? t("discoverNoName")

  async function invite() {
    setState("inviting")

    try {
      await apiFetch(invitePath, { method: "POST" })
      setState("invited")
      toast.success(
        t.markup("discoverInviteDone", { ...bdiText, name: shownName })
      )
    } catch (error) {
      setState("idle")
      toast.error(apiErrorMessage(error, t("discoverInviteFailed")))
    }
  }

  return (
    <div className="@container" data-testid="discover-row">
      <div className="flex flex-col gap-4 p-4 @xl:flex-row @xl:items-center @xl:justify-between @xl:p-6">
        <div className="min-w-0 space-y-1">
          {/* The name, and their LinkedIn profile as the LinkedIn icon after it. */}
          <p className="flex items-center gap-3 text-lg font-medium break-words">
            <bdi>{shownName}</bdi>
            <a
              href={person.linkedin_url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={t("discoverLinkedIn", { name: shownName })}
              className={`-m-1 shrink-0 p-1 transition-colors outline-none focus-visible:ring-3 focus-visible:ring-ring/50 ${ROUND_ICON_BUTTON}`}
            >
              <LinkedInIcon className="size-5" />
            </a>
          </p>
          {latest && (
            <p className="text-sm text-muted-foreground">
              <time dateTime={latest} suppressHydrationWarning>
                {t("discoverPractised", { date: localTime.date(latest) })}
              </time>
            </p>
          )}
          {/* Each matching subject's latest practice grade, labelled as practice. */}
          <div className="pt-2">
            <ul
              aria-label={t("discoverResults")}
              className="flex flex-wrap gap-2"
            >
              {person.results.map((result) => (
                <li
                  key={result.topic_title}
                  className="flex items-baseline gap-2 rounded-xl bg-surface px-3 py-1 text-sm"
                >
                  <span className="normal-case">{result.topic_title}</span>
                  <span className="font-medium tabular-nums">
                    {formatPercent(result.score, locale)}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
        {canEdit && (
          // On phones the button takes its own line, full width.
          <div className="flex shrink-0 justify-end max-sm:w-full">
            <Button
              variant={state === "invited" ? "outline" : "default"}
              className="h-10 px-5 text-base max-sm:w-full"
              disabled={state !== "idle"}
              onClick={invite}
            >
              {state === "invited" && <CheckIcon />}
              {state === "inviting"
                ? t("discoverInviting")
                : state === "invited"
                  ? t("discoverInvited")
                  : t("discoverInvite")}
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
