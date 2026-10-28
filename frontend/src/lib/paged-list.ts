import { PAGE_SIZE } from "@/config/lists"

export function pagePath(path: string, offset: number) {
  const separator = path.includes("?") ? "&" : "?"

  return `${path}${separator}offset=${offset}&limit=${PAGE_SIZE}`
}

/** The page after `items`: by offset, or for a list the API pages by key (`byKey`), also after
the last row's key. */
export function nextPagePath<T>(
  path: string,
  items: T[],
  getKey: (item: T) => string,
  byKey: boolean
) {
  const next = pagePath(path, items.length)
  const last = items.at(-1)

  return byKey && last
    ? `${next}&after=${encodeURIComponent(getKey(last))}`
    : next
}

/** `first` followed by the items of `rest` it doesn't have yet: rows shift between pages when
one is added or removed, so a page can repeat a row already shown. */
export function mergePages<T>(
  first: T[],
  rest: T[],
  getKey: (item: T) => string
) {
  const shown = new Set(first.map(getKey))

  return [...first, ...rest.filter((item) => !shown.has(getKey(item)))]
}

/** The key of rows that have an id; defined once, so lists keep a stable function. */
export function byId(item: { id: string }) {
  return item.id
}
