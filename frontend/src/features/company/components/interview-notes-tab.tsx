"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"

import { NoteEditor } from "@/features/company/components/note-editor"
import { NoteRow } from "@/features/company/components/note-row"
import { VirtualList } from "@/components/common/virtual-list"
import { LIST_BOX, LIST_EMPTY } from "@/config/lists"
import { usePagedList } from "@/hooks/use-paged-list"
import { apiFetch } from "@/lib/api"
import { notesPath } from "@/lib/interview-notes"
import { byId } from "@/lib/paged-list"
import type { InterviewNote } from "@/types/company"

/** An interview's notes tab: the box to write a note, then the team's notes in one list, the
 * pinned one first, then newest first, a page at a time; `initial` is the server's first page.
 * Each change refreshes the page, so the menu's count and the pinned line under the title
 * follow. */
export function InterviewNotesTab({
  interviewId,
  initial,
}: {
  interviewId: string
  initial: InterviewNote[]
}) {
  const t = useTranslations("interviews")
  const router = useRouter()
  const path = notesPath(interviewId)
  const { items, setItems, loadMore } = usePagedList(path, byId, initial)

  async function post(text: string) {
    const note = await apiFetch<InterviewNote>(path, {
      method: "POST",
      body: JSON.stringify({ text }),
    })
    // After the pinned note, which stays first.
    setItems((current) => {
      const pinned = current[0]?.pinned ? 1 : 0

      return [...current.slice(0, pinned), note, ...current.slice(pinned)]
    })
    router.refresh()
  }

  function changed(note: InterviewNote) {
    setItems((current) =>
      current.map((item) =>
        item.id === note.id
          ? note
          : // Pinning one unpins the other.
            { ...item, pinned: note.pinned ? false : item.pinned }
      )
    )
    router.refresh()
  }

  function removed(noteId: string) {
    setItems((current) => current.filter((item) => item.id !== noteId))
    router.refresh()
  }

  return (
    <div className="space-y-6">
      <NoteEditor
        submitLabel={t("notePost")}
        busyLabel={t("notePosting")}
        save={post}
      />
      {items.length === 0 ? (
        <p data-testid="no-notes" className={LIST_EMPTY}>
          {t("notesEmpty")}
        </p>
      ) : (
        <VirtualList
          items={items}
          getKey={byId}
          estimateSize={120}
          onEndReached={loadMore}
          className={LIST_BOX}
          renderItem={(note) => (
            <NoteRow
              note={note}
              path={`${path}/${note.id}`}
              onChanged={changed}
              onRemoved={() => removed(note.id)}
            />
          )}
        />
      )}
    </div>
  )
}
