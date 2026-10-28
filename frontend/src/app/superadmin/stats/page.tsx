import { redirect } from "next/navigation"

/** The stats tab opens on its general tab. */
export default function StatsPage() {
  redirect("/superadmin/stats/general")
}
