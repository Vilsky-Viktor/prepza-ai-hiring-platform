"use client"

import { Trash2Icon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"
import { toast } from "sonner"

import { useLocalTime } from "@/hooks/use-local-time"
import { ConfirmDialog } from "@/components/confirm-dialog"
import { Button } from "@/components/ui/button"
import { Dot } from "@/components/dot"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { apiErrorMessage } from "@/lib/api"
import { deleteConversation, listConversations } from "@/lib/assistant"
import { bdiText } from "@/lib/bidi"
import type { Conversation } from "@/types/assistant"

/** The user's past conversations with the assistant, the latest first: one opens, the bin
 * deletes it. `companyNames` names each one's company. */
export function AssistantHistory({
  companyNames,
  onOpen,
  onDeleted,
}: {
  companyNames: Record<string, string>
  onOpen: (id: string) => void
  onDeleted: (id: string) => void
}) {
  const t = useTranslations("assistant")
  const common = useTranslations("common")
  const localTime = useLocalTime()
  const [items, setItems] = useState<Conversation[] | null>(null)
  // The conversation the user asked to delete, until they confirm or keep it.
  const [deleting, setDeleting] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    listConversations()
      .then(setItems)
      .catch((error) => {
        setItems([])
        toast.error(apiErrorMessage(error, t("historyFailed")))
      })
  }, [t])

  async function remove() {
    const id = deleting!
    setBusy(true)

    try {
      await deleteConversation(id)
      setItems((current) => current?.filter((item) => item.id !== id) ?? null)
      onDeleted(id)
    } catch (error) {
      toast.error(apiErrorMessage(error, common("failed")))
    }

    setBusy(false)
    setDeleting(null)
  }

  if (items === null) {
    return (
      <p className="py-16 text-center text-muted-foreground">
        {common("loading")}
      </p>
    )
  }

  if (items.length === 0) {
    return (
      <p className="py-16 text-center text-muted-foreground">
        {t("historyEmpty")}
      </p>
    )
  }

  return (
    <>
      <ul className="divide-y rounded-xl border">
        {items.map((item) => (
          // One hover surface: the row opens the conversation, the bin sits on top of it.
          <li
            key={item.id}
            className="relative flex items-center gap-2 p-4 pe-2 transition-colors hover:bg-muted/50 active:bg-muted/50"
          >
            {/* The title is cut to one line; the tooltip shows it whole. */}
            <Tooltip>
              <TooltipTrigger
                render={
                  <button
                    type="button"
                    onClick={() => onOpen(item.id)}
                    className="min-w-0 flex-1 space-y-1 text-start outline-none after:absolute after:inset-0 focus-visible:underline"
                  />
                }
              >
                <span className="bidi-auto block truncate font-medium">
                  {item.title}
                </span>
                <span className="block truncate text-sm text-muted-foreground">
                  <time dateTime={item.updated_at} suppressHydrationWarning>
                    {localTime.date(item.updated_at)}
                  </time>
                  {item.company_id && companyNames[item.company_id] && (
                    <>
                      <Dot />
                      {companyNames[item.company_id]}
                    </>
                  )}
                </span>
              </TooltipTrigger>
              <TooltipContent className="bidi-auto max-w-xs">
                {item.title}
              </TooltipContent>
            </Tooltip>
            <Button
              variant="ghost"
              size="icon"
              className="relative z-10 size-10 shrink-0 text-muted-foreground hover:text-destructive"
              aria-label={t.markup("deleteChat", {
                title: item.title,
                ...bdiText,
              })}
              tooltip={common("delete")}
              onClick={() => setDeleting(item.id)}
            >
              <Trash2Icon className="size-5" />
            </Button>
          </li>
        ))}
      </ul>
      <ConfirmDialog
        open={deleting !== null}
        onOpenChange={(open) => !open && setDeleting(null)}
        title={t("deleteTitle")}
        text={t("deleteText")}
        confirm={busy ? common("deleting") : common("delete")}
        busy={busy}
        onConfirm={remove}
      />
    </>
  )
}
