import type { components } from "@/types/api/rounds"

type Schemas = components["schemas"]

export type FaqItem = Schemas["FaqItemOut"]
export type LegalDocument = Schemas["LegalOut"]

/** A message of the help chat's conversation, as the assistant's POST /help/chat takes it: a
reply goes with the signature the chat gave it. */
export type HelpMessage = {
  role: "user" | "assistant"
  content: string
  signature?: string | null
}
