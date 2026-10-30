"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"
import { useState } from "react"

import { DemoInterviewTabs } from "@/features/landing/components/demo-interview-tabs"
import { DEMO_PRESSED } from "@/features/landing/components/demo-panel"
import { InterviewHeader } from "@/features/landing/components/interview-header"
import { NoteRow } from "@/features/company/components/note-row"
import { SubmitHint } from "@/components/common/submit-hint"
import { buttonVariants } from "@/components/ui/button"
import { FloatingTextarea } from "@/components/ui/floating-field"
import {
  DEMO_AUTHOR,
  DEMO_NOTES,
  DEMO_CANDIDATE_COUNT,
  DEMO_NOTE_COUNT,
  DEMO_REPORT_INTERVIEW,
} from "@/config/reports-demo"
import type { InterviewNote } from "@/types/company"

const HOUR = 3_600_000
const NOTHING = () => {}

/** A note as the API gives it, written `hoursAgo`, by `author`; nothing to change in a picture. */
function note(
  id: string,
  author: string,
  text: string,
  hoursAgo: number
): InterviewNote {
  return {
    id,
    text,
    pinned: false,
    author: { name: author, former: false, api_key: false },
    created_at: new Date(Date.now() - hoursAgo * HOUR).toISOString(),
    edited_at: null,
    can_edit: false,
    can_delete: false,
    can_pin: false,
  }
}

/** An interview's notes tab (features/company/components/interview-notes-tab.tsx), for the
 * landing: its header and tabs, the real note box with `typed` so far and Post (the pointer's
 * "post", pressed in while `pressed`), then the real notes, newest first; once `posted`, the new
 * note sliding in on top. What doesn't fit is cut off. */
export function DemoNotes({
  typed,
  pressed,
  posted,
}: {
  typed: string
  pressed: boolean
  posted: string | null
}) {
  const t = useTranslations("interviews")
  // Made once, so their times don't change as it plays.
  const [notes] = useState(() =>
    DEMO_NOTES.map((item, index) =>
      note(`n${index}`, item.author, item.text, item.hoursAgo)
    )
  )
  // Newest first, as the real tab lists them; the posted note on top.
  const earlier = [...notes].reverse()
  const shown = posted
    ? [note("new", DEMO_AUTHOR, posted, 0), ...earlier]
    : earlier

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <InterviewHeader {...DEMO_REPORT_INTERVIEW} status="in_process" />
      <DemoInterviewTabs
        current="notes"
        counts={{
          topics: DEMO_REPORT_INTERVIEW.topics,
          candidates: DEMO_CANDIDATE_COUNT,
          notes: DEMO_NOTE_COUNT + (posted ? 1 : 0),
        }}
      />
      <div data-demo-target="noteBox" className="[&_textarea]:min-h-28">
        <FloatingTextarea
          label={t("noteLabel")}
          placeholder={t("notePlaceholder")}
          value={typed}
          readOnly
          onChange={NOTHING}
          hint={<SubmitHint />}
          action={
            <span
              data-demo-target="post"
              className={buttonVariants({
                className: cn(
                  "h-10 shrink-0 rounded-lg px-5 text-base transition-all",
                  !typed && "opacity-50",
                  pressed && DEMO_PRESSED
                ),
              })}
            >
              {t("notePost")}
            </span>
          }
        />
      </div>
      <ul className="min-h-0 divide-y overflow-hidden rounded-xl border">
        {shown.map((item) => (
          <li
            key={item.id}
            className={cn(
              item.id === "new" &&
                "animate-in duration-500 fade-in slide-in-from-top-4"
            )}
          >
            <NoteRow
              note={item}
              path=""
              onChanged={NOTHING}
              onRemoved={NOTHING}
            />
          </li>
        ))}
      </ul>
    </div>
  )
}
