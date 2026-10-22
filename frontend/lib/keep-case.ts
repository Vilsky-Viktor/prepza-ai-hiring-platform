// Words a lowercase title or button keeps as written: acronyms in any script (ATS, PDF, ИИ),
// Slack's name, and Mira's (the assistant's) in the forms the languages use ("Miralt", "Mirę",
// "Миру", "Міру"). Scripts without capitals (ミラ, ميرا) aren't changed by lowercase anyway.
const KEPT =
  /(?<![\p{L}\p{N}])(\p{Lu}{2,}|Slack|Mira(?:lt|le|ga|l)?|Mirę|Мир[аеуы]|Мір[аиіу])(?![\p{L}\p{N}])/u

/** The text split into the parts that follow the lowercase style (even indexes) and the words
 * it keeps as written (odd indexes). */
export function keptCaseParts(text: string): string[] {
  return text.split(KEPT)
}
