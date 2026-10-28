import { getTranslations } from "next-intl/server"

import { CandidatesDemo } from "@/components/landing/candidates-demo"
import { DEMO_GROUP } from "@/components/landing/demo-panel"
import { NotesLine } from "@/components/landing/notes-line"
import { LandingSection } from "@/components/landing/section"
import { CANDIDATE_NOTES, DEMO_QUESTIONS } from "@/constants/candidates-demo"
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
