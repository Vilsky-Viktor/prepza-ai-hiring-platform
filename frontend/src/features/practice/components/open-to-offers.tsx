"use client"

import { cn } from "cn"
import { HandshakeIcon, SaveIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { type FormEvent, useId, useState } from "react"
import { toast } from "sonner"

import { CornerSign } from "@/components/common/corner-sign"
import { Button } from "@/components/ui/button"
import { FloatingInput } from "@/components/ui/floating-field"
import { Switch } from "@/components/ui/switch"
import { SIGN_CARD } from "@/config/cards"
import { useLocalTime } from "@/hooks/use-local-time"
import { apiFetch, serviceRefusal } from "@/lib/api"
import { bdiText } from "@/lib/bidi"
import type { OpenToOffers } from "@/types/round"

const PATH = "/rounds/open-to-offers"

/** What the field's note says: while it's on, the name companies see and until when; while
 * it's off with no profile entered, that the switch needs one. */
function statusNote(
  status: OpenToOffers,
  draft: string,
  t: ReturnType<typeof useTranslations<"openToOffers">>,
  date: (iso: string) => string
): string | null {
  if (status.on && status.until) {
    return status.name
      ? t.markup("on", {
          ...bdiText,
          name: status.name,
          date: date(status.until),
        })
      : t("onNoName", { date: date(status.until) })
  }

  return draft.trim() ? null : t("needsLinkedin")
}

/** A practice user's Open to offers switch, after a practice round and in Settings: what turning
 * it on shares, the LinkedIn profile it needs, and while it's on, the name companies see and
 * until when. Saving the profile turns it on too. Turning it on sends the wording's version the
 * API gave (the consent it records); the API checks the profile's address and says what's wrong
 * with it. */
export function OpenToOffersCard({ initial }: { initial: OpenToOffers }) {
  const t = useTranslations("openToOffers")
  const localTime = useLocalTime()
  const errorId = useId()
  const [status, setStatus] = useState(initial)
  const [draft, setDraft] = useState(initial.linkedin_url ?? "")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // A profile to save: a new one, or the first one while it's off (saving it turns it on).
  const changed = !status.on || draft.trim() !== status.linkedin_url

  async function turnOn() {
    setSaving(true)
    setError(null)

    try {
      const saved = await apiFetch<OpenToOffers>(PATH, {
        method: "PUT",
        body: JSON.stringify({
          linkedin_url: draft,
          consent_version: status.consent_version,
        }),
      })
      setStatus(saved)
      setDraft(saved.linkedin_url ?? draft)
    } catch (failure) {
      const refusal = serviceRefusal(failure, [409, 422])

      if (refusal) {
        setError(refusal)
      } else {
        toast.error(t("failed"))
      }
    } finally {
      setSaving(false)
    }
  }

  async function turnOff() {
    setSaving(true)

    try {
      await apiFetch(PATH, { method: "DELETE" })
      setStatus({ ...status, on: false, name: null, until: null })
    } catch {
      toast.error(t("failed"))
    } finally {
      setSaving(false)
    }
  }

  function save(event: FormEvent) {
    event.preventDefault()

    if (changed && draft.trim()) {
      void turnOn()
    }
  }

  const note = error ? null : statusNote(status, draft, t, localTime.date)
  const described = error ?? note

  return (
    <div
      className={cn(SIGN_CARD, "space-y-4 max-sm:-mx-6 max-sm:rounded-none")}
      data-testid="open-to-offers"
    >
      <CornerSign>
        <HandshakeIcon className="text-primary" />
      </CornerSign>
      <label className="flex cursor-pointer items-center gap-4 text-base">
        <span className="min-w-0 flex-1 space-y-1">
          <span className="block text-xl font-medium lowercase">
            {t("title")}
            <span className="blue-dot">.</span>
          </span>
          <span className="block text-sm text-muted-foreground">
            {t("text")}
          </span>
        </span>
        <Switch
          checked={status.on}
          disabled={saving || (!status.on && !draft.trim())}
          onCheckedChange={(on) => void (on ? turnOn() : turnOff())}
        />
      </label>
      <form onSubmit={save} className="space-y-2">
        <FloatingInput
          label={t("linkedin")}
          placeholder={t("linkedinHint")}
          value={draft}
          inputMode="url"
          autoComplete="url"
          dir="ltr"
          maxLength={300}
          disabled={saving}
          // On the card's grey, the field is the page's white, so it stands out as a field does
          // on a page; the profile reads in the text colour.
          boxClassName="bg-background"
          className="text-foreground normal-case"
          aria-invalid={error !== null}
          aria-describedby={described ? errorId : undefined}
          onChange={(event) => {
            setDraft(event.target.value)
            setError(null)
          }}
          // Saves the profile: while it's off, that turns it on, as the switch does.
          action={
            <Button
              type="submit"
              className="h-10 shrink-0 rounded-lg px-5 text-base max-sm:w-10 max-sm:px-0"
              disabled={saving || !changed || !draft.trim()}
            >
              {/* On phones the icon alone; its name stays for screen readers. */}
              <SaveIcon aria-hidden className="sm:hidden" />
              <span className="max-sm:sr-only">{t("save")}</span>
            </Button>
          }
        />
        {described && (
          <p
            id={errorId}
            role={error ? "alert" : undefined}
            className={cn(
              "px-6 text-sm",
              error ? "text-destructive" : "text-muted-foreground"
            )}
          >
            {described}
          </p>
        )}
      </form>
    </div>
  )
}
