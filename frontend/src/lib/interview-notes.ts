import type { InterviewNote } from "@/types/company"

/** An interview's notes in the API, the pinned one first, then newest first. */
export function notesPath(id: string) {
  return `/companies/interviews/${id}/notes`
}

/** A note's author's name as shown: a former member or a deleted API key by what they are
 * (`labels`), anyone else by their name; null for a member without one. */
export function noteAuthorName(
  author: InterviewNote["author"],
  labels: { former: string; deletedKey: string }
) {
  if (author.former) {
    return labels.former
  }

  return author.name ?? (author.api_key ? labels.deletedKey : null)
}
