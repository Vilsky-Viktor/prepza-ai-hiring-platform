import { apiFetch } from "@/lib/api"
import type { PracticeStart, PracticeTimingId } from "@/types/round"

/** Starts a practice round on the template with the chosen time per question; returns the
 * first section's page. */
export async function startPracticeRound(
  templateId: string,
  timing: PracticeTimingId
): Promise<string> {
  const round = await apiFetch<PracticeStart>(
    `/rounds/practice/${templateId}`,
    {
      method: "POST",
      body: JSON.stringify({ timing }),
    }
  )

  return `/sessions/${round.session_id}`
}
