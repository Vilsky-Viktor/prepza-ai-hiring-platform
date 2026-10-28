import { redirect } from "next/navigation"

/** The AI costs tab moved into the stats tab, as a tab of its own. */
export default function AiCostsPage() {
  redirect("/superadmin/stats/ai-costs")
}
