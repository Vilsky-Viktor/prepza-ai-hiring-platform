import { optionalFetch } from "@/lib/server-api"

/** Whether prepza is paused (the admin zone's emergency pause). Not known counts as not paused:
 * the services refuse what the pause stops themselves, and the page still shows. */
export async function isPaused() {
  const pause = await optionalFetch<{ paused: boolean }>("/companies/pause")

  return Boolean(pause?.paused)
}
