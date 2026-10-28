"use client"

import { useTranslations } from "next-intl"
import { useCallback, useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { PAGE_SIZE } from "@/constants/lists"
import { apiFetch } from "@/lib/api"
import { mergePages, nextPagePath, pagePath } from "@/lib/paged-list"

/** A list the API serves a page at a time, its rows told apart by `getKey`. `initial` is the
first page the server already rendered; without it, the first page loads on mount, and if that
fails, `failed` says so (not an empty list) until `retry()`. A later page that fails says so in
a toast with Retry, and the list can still load more. With `byKey`, a later page is asked for
after the last row's key (`after=`), for a list the API pages by key. */
export function usePagedList<T>(
  path: string,
  getKey: (item: T) => string,
  initial?: T[],
  byKey = false
) {
  const t = useTranslations("common")
  const [items, setItems] = useState<T[]>(initial ?? [])
  const [hasMore, setHasMore] = useState(
    initial === undefined || initial.length === PAGE_SIZE
  )
  const [loaded, setLoaded] = useState(initial !== undefined)
  const [failed, setFailed] = useState(false)
  const [attempt, setAttempt] = useState(0)
  const [source, setSource] = useState({ path, initial })
  const loading = useRef(false)
  // The latest loadMore, for a failed page's Retry in its toast.
  const loadMoreLatest = useRef<() => Promise<void>>(async () => {})
  // The path shown now, so a page that arrives for an earlier search is dropped.
  const currentPath = useRef(path)

  useEffect(() => {
    currentPath.current = path
  }, [path])

  // A new search or filter starts the list over (reset during render, as React recommends).
  if (source.path !== path) {
    setSource({ path, initial })
    setItems(initial ?? [])
    setHasMore(initial === undefined || initial.length === PAGE_SIZE)
    setLoaded(initial !== undefined)
  } else if (source.initial !== initial) {
    // The server rendered the page again (a refresh after a change): its first page replaces
    // the old one, and the pages loaded after it stay.
    const oldFirst = source.initial?.length ?? 0
    setSource({ path, initial })
    setItems((current) =>
      mergePages(initial ?? [], current.slice(oldFirst), getKey)
    )
  }

  // Lists the server didn't render load their first page here.
  useEffect(() => {
    if (loaded) {
      return
    }

    let current = true
    apiFetch<T[]>(pagePath(path, 0))
      .then((page) => {
        if (current) {
          setItems(page)
          setHasMore(page.length === PAGE_SIZE)
        }
      })
      .then(() => current && setLoaded(true))
      .catch(() => current && setFailed(true))

    return () => {
      current = false
    }
  }, [path, loaded, attempt])

  function retry() {
    setFailed(false)
    setAttempt((count) => count + 1)
  }

  const loadMore = useCallback(async () => {
    if (loading.current || !hasMore || !loaded) {
      return
    }

    loading.current = true

    try {
      const page = await apiFetch<T[]>(nextPagePath(path, items, getKey, byKey))

      if (currentPath.current !== path) {
        return
      }

      setItems((current) => mergePages(current, page, getKey))
      setHasMore(page.length === PAGE_SIZE)
    } catch {
      if (currentPath.current === path) {
        toast.error(t("loadMoreFailed"), {
          action: {
            label: t("retry"),
            onClick: () => void loadMoreLatest.current(),
          },
        })
      }
    } finally {
      loading.current = false
    }
  }, [path, items, byKey, hasMore, loaded, getKey, t])

  useEffect(() => {
    loadMoreLatest.current = loadMore
  }, [loadMore])

  return { items, setItems, hasMore, loaded, failed, retry, loadMore }
}
