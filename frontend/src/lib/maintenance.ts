import {
  MAINTENANCE_CACHE_MS,
  MAINTENANCE_TIMEOUT_MS,
} from "@/constants/maintenance"

export type MaintenanceState = "off" | "open" | "closed"

type Status = { on: boolean; superadmin: boolean }

const OFF: Status = { on: false, superadmin: false }
let cached = { status: OFF, until: 0 }

async function fetchStatus(token?: string): Promise<Status> {
  try {
    const response = await fetch(
      `${process.env.API_URL}/api/companies/maintenance`,
      {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        cache: "no-store",
        signal: AbortSignal.timeout(MAINTENANCE_TIMEOUT_MS),
      }
    )

    return response.ok ? await response.json() : OFF
  } catch {
    return OFF
  }
}

/** Maintenance mode for this visitor, as the companies service says: closed to everyone but
 * superadmins while it's on. */
export async function maintenanceState(
  token?: string
): Promise<MaintenanceState> {
  if (Date.now() > cached.until) {
    cached = {
      status: await fetchStatus(),
      until: Date.now() + MAINTENANCE_CACHE_MS,
    }
  }

  if (!cached.status.on) {
    return "off"
  }

  const mine = token ? await fetchStatus(token) : cached.status

  return mine.superadmin ? "open" : "closed"
}
