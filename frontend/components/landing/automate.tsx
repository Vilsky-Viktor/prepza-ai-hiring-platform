import { ArrowRightIcon } from "lucide-react"
import { getTranslations } from "next-intl/server"

import { AutomateStage } from "@/components/landing/automate-stage"
import { DEMO_GROUP } from "@/components/landing/demo-panel"
import { LandingSection } from "@/components/landing/section"
import { LocalizedLink } from "@/components/localized-link"
import { AUTOMATE_CARDS, type AutomateCard } from "@/constants/automate-demo"

/** Automate your hiring: your platform, AI apps and job boards wired to prepza, and Slack after
 * it. Under its text, a link to the developer docs. */
export async function AutomateSection() {
  const t = await getTranslations("landing.automate")
  const nav = await getTranslations("nav")
  const labels = Object.fromEntries(
    AUTOMATE_CARDS.map((key) => [key, t(`labels.${key}`)])
  ) as Record<AutomateCard, string>

  return (
    <LandingSection
      id="automate"
      title={t("title")}
      text={
        <>
          {t("text")}
          {/* On a line of its own, so the text above keeps its one line. */}
          <span className="mt-1 block">
            <LocalizedLink
              href="/api-docs"
              className="group inline-flex items-center gap-1 text-primary lowercase transition-colors hover:text-primary/80"
            >
              {nav("apiDocs")}
              <ArrowRightIcon
                aria-hidden
                className="size-4 transition-transform duration-200 group-hover:translate-x-1 motion-reduce:transition-none rtl:-scale-x-100 rtl:group-hover:-translate-x-1"
              />
            </LocalizedLink>
          </span>
        </>
      }
    >
      <div className={DEMO_GROUP}>
        <AutomateStage labels={labels} />
      </div>
    </LandingSection>
  )
}
