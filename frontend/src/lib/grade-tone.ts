/** A grade's colour: green when the candidate passed, red when they didn't, none while it isn't
 * decided; the 700 shades, as text needs 4.5:1 on white and on the muted cards. */
export function gradeTone(passed: boolean | null | undefined) {
  if (passed === true) {
    return "text-green-700 dark:text-green-400"
  }

  if (passed === false) {
    return "text-red-700 dark:text-red-400"
  }

  return ""
}
