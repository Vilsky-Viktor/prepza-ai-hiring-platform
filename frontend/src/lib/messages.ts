import { ADMIN_MESSAGES, SERVER_ONLY_MESSAGES } from "@/constants/i18n"

type Messages = Record<string, unknown>

/** The messages client components may need: never the server-only groups, and the admin
 * zone's only `withAdmin`. */
export function clientMessages(messages: Messages, withAdmin = false) {
  const left: readonly string[] = withAdmin
    ? SERVER_ONLY_MESSAGES
    : [...SERVER_ONLY_MESSAGES, ...ADMIN_MESSAGES]

  return Object.fromEntries(
    Object.entries(messages).filter(([group]) => !left.includes(group))
  )
}

/** Whether `t` has a message for `key`: narrows a value the API sends as any string to the keys
 * `t` takes, so an unknown one can fall back instead of failing. */
export function hasMessage<
  T extends { has: (key: never) => boolean },
  Key extends string,
>(t: T, key: Key): key is Key & Parameters<T["has"]>[0] {
  return t.has(key as never)
}
