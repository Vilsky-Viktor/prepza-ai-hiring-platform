"use client"

import { SendIcon, SquarePenIcon, Trash2Icon } from "lucide-react"
import { useRouter } from "next/navigation"
import { useLocale, useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { ConfirmDialog } from "@/components/common/confirm-dialog"
import { NewsDialog } from "@/components/superadmin/news-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { VirtualList } from "@/components/common/virtual-list"
import { usePagedList } from "@/hooks/use-paged-list"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { bdiText } from "@/lib/bidi"
import { formatDay } from "@/lib/format"
import { byId } from "@/lib/paged-list"
import type { AdminNewsPost } from "@/types/news"
import { LIST_BOX } from "@/config/lists"

/** The news tab's posts, newest first, like the templates list: each row's paper plane makes a
 * product-update campaign of it, its pencil opens the post to edit, and its bin deletes it after
 * asking. A badge tells whether the post is translated into
 * every language yet. */
export function NewsAdminList({ initial }: { initial: AdminNewsPost[] }) {
  const t = useTranslations("superadmin")
  const common = useTranslations("common")
  const locale = useLocale()
  const router = useRouter()
  const { items, setItems, loadMore } = usePagedList(
    "/library/superadmin/news",
    byId,
    initial
  )
  const [editing, setEditing] = useState<AdminNewsPost | null>(null)
  const [deleting, setDeleting] = useState<AdminNewsPost | null>(null)
  const [busy, setBusy] = useState(false)
  const [starting, setStarting] = useState(false)

  /** A new product update filled with the post (the API makes it), opened to check and send. */
  async function sendAsCampaign(post: AdminNewsPost) {
    setStarting(true)

    try {
      const campaign = await apiFetch<{ id: string }>(
        `/notifications/superadmin/campaigns/from-news/${post.id}`,
        { method: "POST" }
      )
      router.push(`/superadmin/campaigns/${campaign.id}`)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("campaignSaveFailed")))
      setStarting(false)
    }
  }

  async function remove() {
    if (!deleting) {
      return
    }

    setBusy(true)

    try {
      await apiFetch(`/library/superadmin/news/${deleting.id}`, {
        method: "DELETE",
      })
      setItems((current) => current.filter((item) => item.id !== deleting.id))
      setDeleting(null)
      router.refresh()
    } catch (error) {
      toast.error(apiErrorMessage(error, t("postDeleteFailed")))
    } finally {
      setBusy(false)
    }
  }

  if (items.length === 0) {
    return (
      <p className="py-16 text-center text-muted-foreground">{t("noNews")}</p>
    )
  }

  return (
    <>
      <VirtualList
        items={items}
        getKey={byId}
        estimateSize={89}
        onEndReached={loadMore}
        className={LIST_BOX}
        renderItem={(post) => (
          // On phones the status and buttons take the line under the title.
          <div className="flex items-center gap-6 p-6 max-sm:flex-wrap max-sm:gap-y-3">
            <div className="min-w-0 flex-1 space-y-1 max-sm:basis-full">
              <span className="block text-lg font-medium break-words sm:truncate">
                {post.title}
              </span>
              <span className="block text-sm text-muted-foreground">
                <time dateTime={post.published_on}>
                  {formatDay(post.published_on, locale)}
                </time>
              </span>
            </div>
            <Badge
              variant="outline"
              className="h-7 shrink-0 px-3 text-sm font-light"
            >
              {post.translated ? t("translated") : t("translating")}
            </Badge>
            <div className="flex shrink-0 items-center max-sm:ms-auto max-sm:-me-3">
              <Button
                variant="ghost"
                size="icon"
                className="size-12 text-muted-foreground hover:text-foreground"
                aria-label={t("sendAsCampaign")}
                tooltip={t("sendAsCampaign")}
                disabled={starting}
                onClick={() => sendAsCampaign(post)}
              >
                <SendIcon className="size-6" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="size-12 text-muted-foreground hover:text-foreground"
                aria-label={t("editPost")}
                tooltip={t("editPost")}
                onClick={() => setEditing(post)}
              >
                <SquarePenIcon className="size-6" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="size-12 text-muted-foreground hover:text-destructive"
                aria-label={t.markup("deleteLabel", {
                  title: post.title,
                  ...bdiText,
                })}
                tooltip={common("delete")}
                onClick={() => setDeleting(post)}
              >
                <Trash2Icon className="size-6" />
              </Button>
            </div>
          </div>
        )}
      />
      {editing && (
        <NewsDialog
          open
          onOpenChange={(open) => !open && setEditing(null)}
          post={editing}
          onSaved={(saved) => {
            setItems((current) =>
              current.map((item) => (item.id === saved.id ? saved : item))
            )
            router.refresh()
          }}
        />
      )}
      <ConfirmDialog
        open={deleting !== null}
        onOpenChange={(open) => !open && setDeleting(null)}
        title={t("deletePostTitle")}
        text={t("deletePostText")}
        confirm={busy ? common("deleting") : common("delete")}
        busy={busy}
        onConfirm={remove}
      />
    </>
  )
}
