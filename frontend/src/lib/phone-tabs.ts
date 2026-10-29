// How many pages a page menu's row shows on phones before the rest go under "more pages".
export const PHONE_TABS_SHOWN = 2

/** A page menu's pages on a phone: the first PHONE_TABS_SHOWN in the row and the others, in
 * their order, in the "more pages" menu; an open page from that menu takes the row's last place,
 * and the page it replaces goes into the menu. */
export function splitPhoneTabs<T extends { id: string }>(
  items: readonly T[],
  current: string
) {
  const index = items.findIndex((item) => item.id === current)
  const shown =
    index < PHONE_TABS_SHOWN
      ? items.slice(0, PHONE_TABS_SHOWN)
      : [...items.slice(0, PHONE_TABS_SHOWN - 1), items[index]]

  return { shown, rest: items.filter((item) => !shown.includes(item)) }
}
