// A question mark as the page's language writes it: Latin, full-width (Chinese, Japanese) or
// Arabic and Persian.
const QUESTION_MARK = /[?？؟]$/

/** Whether `title` ends with a question mark: such a title gets no dot after it (globals.css). */
export function endsWithQuestionMark(title: string) {
  return QUESTION_MARK.test(title.trim())
}
