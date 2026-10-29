"use client"

import {
  BookmarkIcon,
  BookmarkXIcon,
  PencilIcon,
  Trash2Icon,
  UserIcon,
} from "lucide-react"
import { useFormatter, useNow, useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { NoteEditor } from "@/features/company/components/note-editor"
import { ConfirmDialog } from "@/components/common/confirm-dialog"
import { IconButton } from "@/components/common/icon-button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { TEXT_LINK } from "@/config/links"
import { ROW_HOVER } from "@/config/lists"
import { apiErrorMessage, apiFetch, serviceRefusal } from "@/lib/api"
import { firstGrapheme } from "@/lib/graphemes"
import { linkParts } from "@/lib/linkify"
import type { InterviewNote } from "@/types/company"

/** One note in an interview's notes: its author's picture and name ("former member" once
 * they've left), when it was written and whether it was edited, its text with its addresses as
 * links; and what the member may do with it, as the backend says: edit, delete, pin. */
export function NoteRow({
  note,
  path,
  onChanged,
  onRemoved,
}: {
  note: InterviewNote
  // The note's own address in the API.
  path: string
  onChanged: (note: InterviewNote) => void
  onRemoved: () => void
}) {
  const t = useTranslations("interviews")
  const common = useTranslations("common")
  const format = useFormatter()
  const now = useNow({ updateInterval: 60000 })
  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const name = note.author.former ? t("noteFormerMember") : note.author.name

  async function save(text: string) {
    const saved = await apiFetch<InterviewNote>(path, {
      method: "PATCH",
      body: JSON.stringify({ text }),
    })
    onChanged(saved)
    setEditing(false)
  }

  async function remove() {
    setDeleting(true)

    try {
      await apiFetch(path, { method: "DELETE" })
      setConfirming(false)
      onRemoved()
    } catch (error) {
      toast.error(
        serviceRefusal(error, [403, 404]) ??
          apiErrorMessage(error, t("noteFailed"))
      )
    } finally {
      setDeleting(false)
    }
  }

  async function pin() {
    try {
      await apiFetch(`${path}/pinned`, {
        method: "PUT",
        body: JSON.stringify({ pinned: !note.pinned }),
      })
      onChanged({ ...note, pinned: !note.pinned })
    } catch (error) {
      toast.error(
        serviceRefusal(error, [403, 404]) ??
          apiErrorMessage(error, t("noteFailed"))
      )
    }
  }

  return (
    <div
      data-testid="note"
      data-pinned={note.pinned || undefined}
      className={`flex gap-4 p-6 pe-3 max-sm:flex-wrap max-sm:pe-6 ${ROW_HOVER}`}
    >
      <Avatar size="lg">
        {note.author.photo_url && (
          <AvatarImage src={note.author.photo_url} alt="" />
        )}
        <AvatarFallback>
          {name ? firstGrapheme(name) : <UserIcon className="size-5" />}
        </AvatarFallback>
      </Avatar>
      <div className="min-w-0 flex-1 space-y-4">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
          {/* On phones the name has its line; when, "edited" and "pinned" go under it. */}
          <bdi
            className="font-medium max-sm:basis-full"
            data-testid="note-author"
          >
            {name}
          </bdi>
          <time
            dateTime={note.created_at}
            title={format.dateTime(new Date(note.created_at), {
              dateStyle: "medium",
              timeStyle: "short",
            })}
            className="text-muted-foreground"
            suppressHydrationWarning
          >
            {format.relativeTime(new Date(note.created_at), now)}
          </time>
          {note.edited_at && (
            <span className="text-muted-foreground" data-testid="note-edited">
              {t("noteEdited")}
            </span>
          )}
          {note.pinned && (
            <Badge variant="outline">
              <BookmarkIcon aria-hidden />
              {t("notePinned")}
            </Badge>
          )}
        </div>
        {/* On phones the text starts under the picture, not beside it (its size-10 and the gap-4). */}
        {editing ? (
          <div className="max-sm:-ms-14">
            <NoteEditor
              initial={note.text}
              submitLabel={common("save")}
              busyLabel={common("saving")}
              save={save}
              onCancel={() => setEditing(false)}
            />
          </div>
        ) : (
          <p
            dir="auto"
            className="text-base break-words whitespace-pre-wrap max-sm:-ms-14"
            data-testid="note-text"
          >
            {linkParts(note.text).map((part, index) =>
              part.url ? (
                <a
                  key={index}
                  href={part.url}
                  target="_blank"
                  rel="noopener noreferrer nofollow"
                  dir="ltr"
                  className={`${TEXT_LINK} break-all`}
                >
                  {part.text}
                </a>
              ) : (
                part.text
              )
            )}
          </p>
        )}
      </div>
      {!editing && (
        <div className="flex shrink-0 items-center self-center max-sm:w-full max-sm:justify-center">
          {note.can_pin && (
            <IconButton
              label={note.pinned ? t("noteUnpin") : t("notePin")}
              onClick={pin}
            >
              {note.pinned ? (
                <BookmarkXIcon className="size-6" />
              ) : (
                <BookmarkIcon className="size-6" />
              )}
            </IconButton>
          )}
          {note.can_edit && (
            <IconButton label={common("edit")} onClick={() => setEditing(true)}>
              <PencilIcon className="size-6" />
            </IconButton>
          )}
          {note.can_delete && (
            <IconButton
              label={common("delete")}
              className="hover:text-destructive"
              onClick={() => setConfirming(true)}
            >
              <Trash2Icon className="size-6" />
            </IconButton>
          )}
        </div>
      )}
      <ConfirmDialog
        open={confirming}
        onOpenChange={setConfirming}
        title={t("noteDeleteTitle")}
        text={t("noteDeleteText")}
        confirm={deleting ? common("deleting") : common("delete")}
        busy={deleting}
        onConfirm={remove}
      />
    </div>
  )
}
