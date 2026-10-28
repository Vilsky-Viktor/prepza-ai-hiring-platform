import { notFound } from "next/navigation"

import { LegalNotices } from "@/features/superadmin/components/legal-notices"
import { LimitSettings } from "@/features/superadmin/components/limit-settings"
import { MaintenanceSwitch } from "@/features/superadmin/components/maintenance-switch"
import { PauseSwitch } from "@/features/superadmin/components/pause-switch"
import { SuperadminHeader } from "@/features/superadmin/components/superadmin-header"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { LegalNotice, LimitChange, Limits } from "@/types/superadmin"

export const generateMetadata = () => translatedTitle("superadmin", "zone")

/** The admin zone's controls: the emergency pause, maintenance mode, the legal notices and every
 * limit, editable. The pause's state is
 * public (pages show a notice), so the page asks who's signed in; maintenance's is for
 * superadmins only. The API turns both for superadmins only. */
export default async function ControlsPage() {
  const [pause, maintenance, notices, limits, changes] = await Promise.all([
    serverFetch<{ paused: boolean }>("/companies/pause"),
    serverFetch<{ on: boolean }>("/companies/superadmin/maintenance"),
    serverFetch<LegalNotice[]>("/notifications/superadmin/legal-notices"),
    serverFetch<Limits>("/billing/superadmin/limits"),
    serverFetch<LimitChange[]>("/billing/superadmin/limits/changes"),
  ])

  if (!pause || !maintenance || !notices || !limits || !changes) {
    notFound()
  }

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <SuperadminHeader current="controls">
        <div className="space-y-4">
          <PauseSwitch paused={pause.paused} />
          <MaintenanceSwitch on={maintenance.on} />
          <LegalNotices initial={notices} />
          <LimitSettings initial={limits} initialChanges={changes} />
        </div>
      </SuperadminHeader>
    </main>
  )
}
