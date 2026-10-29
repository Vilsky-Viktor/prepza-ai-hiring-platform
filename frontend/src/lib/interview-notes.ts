/** An interview's notes in the API, the pinned one first, then newest first. */
export function notesPath(id: string) {
  return `/companies/interviews/${id}/notes`
}
