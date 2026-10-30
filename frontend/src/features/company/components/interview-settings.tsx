"use client"

import { useRouter } from "next/navigation"
import { useLocale, useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import type { InterviewSettingsData } from "@/types/company"
import { formatList } from "@/lib/format"
import { LIST_BOX } from "@/config/lists"
import { CARD_PADDING } from "@/config/cards"
import { AnswerModeSetting } from "@/features/company/components/answer-mode-switch"

/** The interview's settings tab: whether it's taken in click mode or voice mode (voice only in
the languages the API names), the average time per question (each question gets its own, fitted
to it by rounds), the pass mark, whether the company hired, and whether its questions stay out of
prepza's shared question bank, one row each in a list like the topics'.
Every interview is timed, and candidates never see their scores. */
export function InterviewSettings({
  interviewId,
  questionSeconds,
  passMark,
  hired,
  keepPrivate,
  voice,
}: {
  interviewId: string
  questionSeconds: number
  passMark: number
  hired: boolean
  keepPrivate: boolean
  // Taken in voice mode (click mode otherwise, the default), whether the interview's language
  // allows it, and the languages that do.
  voice: { on: boolean; available: boolean; languages: string[] }
}) {
  const t = useTranslations("interviews")
  const locale = useLocale()
  const router = useRouter()
  const [saved, setSaved] = useState<InterviewSettingsData>({
    question_seconds: questionSeconds,
    hired,
    pass_mark: passMark,
    keep_private: keepPrivate,
    voice: voice.on,
  })
  const [seconds, setSeconds] = useState(String(questionSeconds))
  const [mark, setMark] = useState(String(passMark))
  const [saving, setSaving] = useState(false)

  // Every setting goes together, so saving one never resets the others. The API checks the
  // ranges; its message shows if a value doesn't fit, and the field goes back.
  async function save(change: Partial<InterviewSettingsData>) {
    const next = { ...saved, ...change }

    if (saving || JSON.stringify(next) === JSON.stringify(saved)) {
      return
    }

    setSaving(true)

    try {
      await apiFetch(`/companies/interviews/${interviewId}/settings`, {
        method: "PATCH",
        body: JSON.stringify(next),
      })
      setSaved(next)
      router.refresh()
    } catch (error) {
      setSeconds(String(saved.question_seconds))
      setMark(String(saved.pass_mark))
      toast.error(apiErrorMessage(error, t("settingsFailed")))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={LIST_BOX}>
      <AnswerModeSetting
        label={t("answerMode")}
        help={
          voice.available
            ? t("answerModeHelp")
            : t("voiceModeLanguages", {
                languages: languageList(voice.languages, locale),
              })
        }
        voice={saved.voice}
        disabled={saving || (!voice.available && !saved.voice)}
        onChange={(on) => save({ voice: on })}
      />
      <NumberSetting
        label={t("timePerQuestion")}
        help={t("timePerQuestionHelp")}
        fieldLabel={t("secondsLabel")}
        unit={t("secondsUnit")}
        value={seconds}
        disabled={saving}
        onChange={setSeconds}
        onSave={() => save({ question_seconds: Number(seconds) })}
      />
      <NumberSetting
        label={t("passMark")}
        fieldLabel={t("passMarkLabel")}
        unit="%"
        value={mark}
        disabled={saving}
        onChange={setMark}
        onSave={() => save({ pass_mark: Number(mark) })}
      />
      <CheckSetting
        label={t("markHired")}
        checked={saved.hired}
        disabled={saving}
        onChange={(checked) => save({ hired: checked })}
      />
      <CheckSetting
        label={t("keepPrivate")}
        help={t("keepPrivateHelp")}
        checked={saved.keep_private}
        disabled={saving}
        onChange={(checked) => save({ keep_private: checked })}
      />
    </div>
  )
}

/** The languages' names in the interface's language, as a list: "English, Spanish and German". */
function languageList(codes: string[], locale: string) {
  const names = new Intl.DisplayNames(locale, { type: "language" })

  return formatList(
    codes.map((code) => names.of(code) ?? code),
    locale
  )
}

/** A yes-or-no setting: its name, an optional line under it, and a checkbox. */
function CheckSetting({
  label,
  help,
  checked,
  disabled,
  onChange,
}: {
  label: string
  help?: string
  checked: boolean
  disabled: boolean
  onChange: (checked: boolean) => void
}) {
  return (
    <label
      className={`flex cursor-pointer items-center justify-between gap-4 ${CARD_PADDING}`}
    >
      <span className="min-w-0 space-y-1">
        <span className="block text-lg font-light">{label}</span>
        {help && (
          <span className="block text-sm text-muted-foreground">{help}</span>
        )}
      </span>
      {/* Centred under the fields above. */}
      <span className="flex w-36 shrink-0 justify-center">
        <Checkbox
          className="size-7 shrink-0 [&_[data-slot=checkbox-indicator]>svg]:size-5"
          checked={checked}
          disabled={disabled}
          onCheckedChange={onChange}
        />
      </span>
    </label>
  )
}

/** A number setting: its name, an optional line under it, and a field with its unit that saves
 * when left. */
function NumberSetting({
  label,
  help,
  fieldLabel,
  unit,
  value,
  disabled,
  onChange,
  onSave,
}: {
  label: string
  help?: string
  fieldLabel: string
  unit: string
  value: string
  disabled: boolean
  onChange: (value: string) => void
  onSave: () => void
}) {
  return (
    // On phones the field takes its own line.
    <label
      className={`flex items-center justify-between gap-4 max-sm:flex-col max-sm:items-start ${CARD_PADDING}`}
    >
      <span className="min-w-0 space-y-1">
        <span className="block text-lg font-light">{label}</span>
        {help && (
          <span className="block text-sm text-muted-foreground">{help}</span>
        )}
      </span>
      {/* Same look as the app's other fields (library search, candidate invite). */}
      <span className="relative w-36 shrink-0 rounded-xl border border-transparent transition-colors focus-within:border-ring-gradient">
        <Input
          type="number"
          inputMode="numeric"
          value={value}
          disabled={disabled}
          aria-label={fieldLabel}
          className="h-14 [appearance:textfield] border-0 ps-5 pe-14 text-lg focus-visible:ring-0 md:text-lg [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
          onChange={(event) => onChange(event.target.value)}
          onBlur={onSave}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.currentTarget.blur()
            }
          }}
        />
        <span className="pointer-events-none absolute end-5 top-1/2 -translate-y-1/2 text-lg text-muted-foreground">
          {unit}
        </span>
      </span>
    </label>
  )
}
