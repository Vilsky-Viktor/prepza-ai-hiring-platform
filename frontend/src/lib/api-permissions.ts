// An API key's permissions on the API page. Which permission comes with which read (`implied`)
// is the api service's answer; these only show it.

/** Ticking a permission ticks the read it comes with, if any. */
export function tick(
  ticked: string[],
  permission: string,
  implied: Record<string, string>
) {
  const added = [permission, implied[permission]].filter(Boolean)

  return [...new Set([...ticked, ...added])]
}

/** The reads that a ticked permission comes with: they stay ticked and can't be unticked. */
export function lockedReads(ticked: string[], implied: Record<string, string>) {
  return new Set(ticked.map((item) => implied[item]).filter(Boolean))
}

/** A key's permissions for its line in the list, by group in the groups' order: each group with
 * its ticked permissions, empty groups left out. */
export function permissionsByGroup(
  permissions: string[],
  groups: Record<string, string[]>
) {
  return Object.entries(groups)
    .map(([group, items]) => ({
      group,
      permissions: items.filter((item) => permissions.includes(item)),
    }))
    .filter((entry) => entry.permissions.length > 0)
}
