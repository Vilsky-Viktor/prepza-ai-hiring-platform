import {
  BadgeCheckIcon,
  ClipboardPasteIcon,
  ListChecksIcon,
} from "lucide-react"
import { getTranslations } from "next-intl/server"

import { CreateFlow } from "@/features/landing/components/create-flow"
import { DEMO_GROUP } from "@/features/landing/components/demo-panel"
import { NotesLine } from "@/features/landing/components/notes-line"
import { PhoneSteps } from "@/features/landing/components/phone-steps"
import { LandingSection } from "@/features/landing/components/section"
import { BAND } from "@/config/landing-backgrounds"

// The three steps, each with its icon on phones.
const STEPS = {
  describe: ClipboardPasteIcon,
  adjust: ListChecksIcon,
  ready: BadgeCheckIcon,
}
const STEP_KEYS = Object.keys(STEPS) as (keyof typeof STEPS)[]

/** How an interview is created, played in one frame: a job description pasted and a first
 * company named, its topics adjusted, and the interview made from them, a candidate invited.
 * Under it, short facts: that no subject expert is needed to make one, the questions written for
 * each topic (`questionsPerTopic`, from Controls; left out without it), and the ready
 * templates. On phones, the three steps as cards in place of the frame. */
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
      <div className="mt-8 flex flex-col gap-8 max-sm:mt-0">
        <div className={`${DEMO_GROUP} max-sm:hidden`}>
          <CreateFlow
            labels={{
              steps: STEP_KEYS.map((step) =>
                t.rich(step, {
                  n: (chunks) => <span className="text-primary">{chunks}</span>,
                })
              ),
              status: t("status"),
            }}
          />
        </div>
        <PhoneSteps
          className="bg-background"
          steps={STEP_KEYS.map((key) => ({
            key,
            icon: STEPS[key],
            title: t.markup(key, { n: (chunks) => chunks }),
            text: t(`phone.${key}`),
          }))}
        />
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
