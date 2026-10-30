import { InterviewSettings } from "@/features/company/components/interview-settings"
import { ShareLink } from "@/features/company/components/share-link"
import type { InterviewDetail } from "@/types/company"

/** An interview's settings tab: the shareable link above the interview's settings. */
export function InterviewSettingsTab({
  interview,
  canEdit,
}: {
  interview: InterviewDetail
  canEdit: boolean
}) {
  return (
    <div className="space-y-6">
      <ShareLink
        interviewId={interview.id}
        linkToken={interview.link_token}
        canEdit={canEdit}
      />
      <InterviewSettings
        interviewId={interview.id}
        questionSeconds={interview.question_seconds}
        passMark={interview.pass_mark}
        hired={interview.hired}
        keepPrivate={interview.keep_private}
        voice={{
          on: interview.voice ?? false,
          available: interview.voice_available ?? false,
          languages: interview.voice_languages ?? [],
        }}
      />
    </div>
  )
}
