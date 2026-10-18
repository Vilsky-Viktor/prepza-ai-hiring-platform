import { getTranslations } from "next-intl/server"

import { CreateFlow } from "@/components/landing/create-flow"
import { DEMO_BAND } from "@/components/landing/demo-panel"
import { NotesLine } from "@/components/landing/notes-line"
import { LandingSection } from "@/components/landing/section"

/** How an interview is created, as three panels playing on their own, joined by arrows: a job
 * description typed, its topics adjusted, and the interview made from them. In one row from
 * laptops up; one under the other below. Under them, short facts: that no subject expert is
 * needed to make one, the questions written for each topic (`questionsPerTopic`, from Controls;
 * left out without it), and the ready templates. */
export async function CreateSection({
  questionsPerTopic,
}: {
  questionsPerTopic: number | null
}) {
  const t = await getTranslations("landing.create")

  return (
    <LandingSection id="how" title={t("title")} text={t("text")}>
      <div className="flex flex-col gap-8">
        <div className={DEMO_BAND}>
          <CreateFlow
            labels={{
              describe: t("describe"),
              adjust: t("adjust"),
              ask: t("ask"),
              ready: t("ready"),
              status: t("status"),
              invite: t("invite"),
            }}
          />
        </div>
        <NotesLine
          notes={[
            t("notes.expert"),
            ...(questionsPerTopic === null
              ? []
              : [t("notes.questions", { count: questionsPerTopic })]),
            t("notes.templates"),
          ]}
        />
      </div>
    </LandingSection>
  )
}
