/** The message key for an answer's verdict; `correct` is null when a candidate may not see
results. A multi-answer answer with some of the points (`score` above 0) is partly right. */
export function verdict(correct: boolean | null, score?: number | null) {
  if (correct === null) {
    return "answered"
  }

  if (!correct && score) {
    return "partlyCorrect"
  }

  return correct ? "correct" : "incorrect"
}
