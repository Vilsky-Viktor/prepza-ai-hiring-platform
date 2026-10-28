import { getTranslations } from "next-intl/server"

import { InterviewStatus } from "@/components/company/interview-status"
import { EditableTitle } from "@/components/common/editable-title"
import { EntityId } from "@/components/common/entity-id"
import type { InterviewDetail } from "@/types/company"

/** An interview's title (editable by those who can), or what's happening while it has none
 * (generating, or failed); under it its status once ready and the id to quote when writing to
 * prepza. */
export async function InterviewTitle({
  interview,
  canEdit,
}: {
  interview: InterviewDetail
  canEdit: boolean
}) {
  const t = await getTranslations("interviews")

  return (
    <div className="min-w-0 flex-1">
      {interview.title ? (
        <EditableTitle
          title={interview.title}
          path={`/companies/interviews/${interview.id}/title`}
          editable={canEdit}
        />
      ) : (
        <h1
          className="font-heading text-3xl font-medium tracking-tight text-balance"
          data-testid={
            interview.generation_failed ? "generation-failed" : undefined
          }
        >
          {interview.generation_failed
            ? t("generationFailed")
            : t("generating")}
        </h1>
      )}
      {/* The status under the title, before the buttons on phones, and the id (also while
          generating, or after a failure). */}
      <div className="mt-1 flex flex-wrap items-center gap-x-4">
        {interview.set_id && <InterviewStatus status={interview.status} />}
        <EntityId id={interview.id} />
      </div>
    </div>
  )
}
