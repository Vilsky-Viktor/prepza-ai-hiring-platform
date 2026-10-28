import type { Messages } from "next-intl"

// The messages at a dotted path, as "assistant.pages" names a nested group.
type Group<
  Value,
  Path extends string,
> = Path extends `${infer Head}.${infer Rest}`
  ? Head extends keyof Value
    ? Group<Value[Head], Rest>
    : never
  : Path extends keyof Value
    ? Value[Path]
    : never

/** The keys of a group of messages by its dotted path: `MessageKey<"assistant.pages">`. */
export type MessageKey<Path extends string> = keyof Group<Messages, Path> &
  string
