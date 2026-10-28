import { getTranslations } from "next-intl/server"

import { CandidatesDemo } from "@/features/landing/components/candidates-demo"
import { DEMO_GROUP } from "@/features/landing/components/demo-panel"
import { NotesLine } from "@/features/landing/components/notes-line"
import { LandingSection } from "@/features/landing/components/section"
import { CANDIDATE_NOTES, DEMO_QUESTIONS } from "@/config/candidates-demo"
import { codeTokens, editorText } from "@/lib/code-tokens"

/** What candidates see: the invitation accepted and three kinds of question answered, played in
 * one panel; under it, what makes it easy and fair for them. */
export async function CandidatesSection() {
  const t = await getTranslations("landing.candidates")
  // The examples' colors, made here so the page doesn't load shiki for them.
  const exampleColors = await Promise.all(
    DEMO_QUESTIONS.map((question) =>
      question.example
        ? codeTokens(
            editorText(question.example.code),
            question.example.language
          )
        : null
    )
  )

  return (
    <LandingSection id="candidates" title={t("title")} text={t("text")}>
      <div className="flex flex-col gap-8">
        <div className={DEMO_GROUP}>
          <CandidatesDemo exampleColors={exampleColors} />
        </div>
        <NotesLine notes={CANDIDATE_NOTES.map((key) => t(`notes.${key}`))} />
      </div>
    </LandingSection>
  )
}
