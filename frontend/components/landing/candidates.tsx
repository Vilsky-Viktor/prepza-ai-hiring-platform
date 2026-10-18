import { getTranslations } from "next-intl/server"

import { CandidatesDemo } from "@/components/landing/candidates-demo"
import { DEMO_BAND } from "@/components/landing/demo-panel"
import { NotesLine } from "@/components/landing/notes-line"
import { LandingSection } from "@/components/landing/section"
import { CANDIDATE_NOTES } from "@/constants/candidates-demo"

/** What candidates see: the invitation accepted and three kinds of question answered, played in
 * one panel; under it, what makes it easy and fair for them. */
export async function CandidatesSection() {
  const t = await getTranslations("landing.candidates")

  return (
    <LandingSection id="candidates" title={t("title")} text={t("text")}>
      <div className="flex flex-col gap-8">
        <div className={DEMO_BAND}>
          <CandidatesDemo />
        </div>
        <NotesLine notes={CANDIDATE_NOTES.map((key) => t(`notes.${key}`))} />
      </div>
    </LandingSection>
  )
}
