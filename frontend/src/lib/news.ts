/** A post's title as the news page shows it, ending with the site's blue dot like its headings:
 * a title's own final period gives way to the dot, and one ending with "?" or "!" gets none. */
export function postHeading(title: string) {
  const text = title.trim().replace(/\.+$/, "")

  return { text, dot: !/[?!…]$/.test(text) }
}
