"use client"

import { useLocale, useTranslations } from "next-intl"
import { useEffect, useState } from "react"

import { CompanyPicker } from "@/components/superadmin/company-picker"
import { Checkbox } from "@/components/ui/checkbox"
import { SEARCH_DELAY_MS } from "@/config/lists"
import { apiFetch } from "@/lib/api"
import { compactNumber } from "@/lib/format"
import type {
  AudienceGroup,
  CampaignAudience as Audience,
  CampaignKind,
} from "@/types/campaigns"

const GROUPS: AudienceGroup[] = ["members", "candidates", "learners"]
const BOX = "size-6 shrink-0 [&_[data-slot=checkbox-indicator]>svg]:size-4"

/** One ticked row of the audience's list, as Slack's notification kinds are (slack-kinds.tsx):
 * its name, a line under it, and its box at the end. */
function Choice({
  name,
  note,
  checked,
  onChange,
  testId,
}: {
  name: string
  note?: string
  checked: boolean
  onChange: (checked: boolean) => void
  testId: string
}) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-4">
      <span className="space-y-0.5">
        <span className="block text-base">{name}</span>
        {note && (
          <span className="block text-sm text-muted-foreground">{note}</span>
        )}
      </span>
      <Checkbox
        className={BOX}
        checked={checked}
        onCheckedChange={(on) => onChange(on === true)}
        data-testid={testId}
      />
    </label>
  )
}

/** Whom a campaign goes to: everyone, or any of the groups (companies' people, candidates,
 * learners); of companies, their owners and admins only, and for an important notice some
 * companies only. Under it, how many it would reach now, as the service counts them. */
export function CampaignAudience({
  kind,
  value,
  onChange,
}: {
  kind: CampaignKind
  value: Audience
  onChange: (audience: Audience) => void
}) {
  const t = useTranslations("superadmin")
  const locale = useLocale()
  const [count, setCount] = useState<number | null>(null)
  const members = value.groups.includes("members")
  const body = JSON.stringify({
    kind,
    groups: value.groups,
    editors_only: value.editorsOnly,
    company_ids: value.companies.map((company) => company.id),
  })

  useEffect(() => {
    const timer = window.setTimeout(() => {
      apiFetch<{ count: number }>(
        "/notifications/superadmin/campaigns/recipients",
        { method: "POST", body }
      )
        .then((found) => setCount(found.count))
        .catch(() => setCount(null))
    }, SEARCH_DELAY_MS)

    return () => window.clearTimeout(timer)
  }, [body])

  function toggle(group: AudienceGroup, on: boolean) {
    const groups = on
      ? GROUPS.filter((item) => item === group || value.groups.includes(item))
      : value.groups.filter((item) => item !== group)
    // Owners only and some companies only narrow the companies group: they go with it.
    const keep = groups.includes("members")

    onChange({
      groups,
      editorsOnly: keep && value.editorsOnly,
      companies: keep ? value.companies : [],
    })
  }

  return (
    <div className="space-y-2">
      <span className="block text-sm text-muted-foreground">
        {t("campaignAudience")}
      </span>
      <div className="divide-y rounded-xl border">
        <div className="p-4">
          <Choice
            name={t("campaignAudienceEveryone")}
            note={t(`campaignAudienceEveryoneNote.${kind}`)}
            checked={value.groups.length === 0}
            onChange={(on) =>
              on && onChange({ groups: [], editorsOnly: false, companies: [] })
            }
            testId="audience-everyone"
          />
        </div>
        {GROUPS.map((group) => (
          <div key={group} className="space-y-4 p-4">
            <Choice
              name={t(`campaignAudienceGroups.${group}`)}
              note={t(`campaignAudienceNotes.${group}`)}
              checked={value.groups.includes(group)}
              onChange={(on) => toggle(group, on)}
              testId={`audience-${group}`}
            />
            {group === "members" && members && (
              <div className="space-y-4 ps-6">
                <Choice
                  name={t("campaignAudienceEditorsOnly")}
                  checked={value.editorsOnly}
                  onChange={(on) => onChange({ ...value, editorsOnly: on })}
                  testId="audience-editors-only"
                />
                {kind === "notices" && (
                  // Labelled above, as PillSelect is; the label names the picker too.
                  <div className="space-y-2">
                    <span className="block text-sm text-muted-foreground">
                      {t("campaignCompanies")}
                    </span>
                    <CompanyPicker
                      value={value.companies}
                      onChange={(companies) =>
                        onChange({ ...value, companies })
                      }
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
      <p
        aria-live="polite"
        className="text-end text-sm text-muted-foreground tabular-nums"
        data-testid="audience-count"
      >
        {t("campaignAudienceCount", {
          count: count ?? 0,
          shown: count === null ? "—" : compactNumber(count, locale),
        })}
      </p>
    </div>
  )
}
