import { getTranslations } from "next-intl/server"

import { DEMO_GROUP } from "@/features/landing/components/demo-panel"
import { InviteStage } from "@/features/landing/components/invite-stage"
import { MoreLink } from "@/components/common/more-link"
import { LandingSection } from "@/features/landing/components/section"
import { INVITE_SOURCES, type InviteSource } from "@/config/invite-demo"
import { DOT_GRID } from "@/config/landing-backgrounds"

/** Every way candidates come into an interview, around it, each wired to it, and Slack told
 * about them; under it, the way to the developer docs. */
export async function InviteFromSection() {
  const t = await getTranslations("landing.sources")
  const labels = Object.fromEntries(
    INVITE_SOURCES.map(({ key }) => [key, t(`labels.${key}`)])
  ) as Record<InviteSource["key"], string>
  const descriptions = Object.fromEntries(
    INVITE_SOURCES.map(({ key }) => [key, t(`descriptions.${key}`)])
  ) as Record<InviteSource["key"], string>

  return (
    <LandingSection
      id="invite"
      title={t("title")}
      text={t("text")}
      background={DOT_GRID}
    >
      {/* A little closer to the text than other sections' pictures. */}
      <div className={`${DEMO_GROUP} -mt-6`}>
        <InviteStage
          labels={labels}
          descriptions={descriptions}
          slackDescription={t("slackDescription")}
          interview={t("interview")}
        />
      </div>
      {/* Under the picture: for developers, the way to the docs. */}
      <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
        <span className="text-lg text-muted-foreground lowercase">
          {t("automate")}
        </span>
        <MoreLink href="/api-docs">{t("developerDocs")}</MoreLink>
      </div>
    </LandingSection>
  )
}
