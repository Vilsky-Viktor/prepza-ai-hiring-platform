import { getTranslations } from "next-intl/server"

import { CreateFlow } from "@/features/landing/components/create-flow"
import { DEMO_GROUP } from "@/features/landing/components/demo-panel"
import { NotesLine } from "@/features/landing/components/notes-line"
import { LandingSection } from "@/features/landing/components/section"
import { BAND } from "@/config/landing-backgrounds"

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
    <LandingSection
      id="how"
      title={t("title")}
      text={t("text")}
      background={BAND}
    >
      <div className="flex flex-col gap-8">
        <div className={DEMO_GROUP}>
          <CreateFlow
            labels={{
              describe: t("describe"),
              adjust: t("adjust"),
              ask: t("ask"),
              ready: t("ready"),
              status: t("status"),
              invite: t("invite"),
              waiting: t("waiting"),
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
