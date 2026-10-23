import { getTranslations } from "next-intl/server"

import { DEMO_GROUP } from "@/components/landing/demo-panel"
import { InviteStage } from "@/components/landing/invite-stage"
import { LandingSection, MoreLink } from "@/components/landing/section"
import { INVITE_SOURCES, type InviteSource } from "@/constants/invite-demo"

/** Every way candidates come into an interview, around it, each wired to it, and Slack told
 * about them; above the interview, a link to the developer docs. */
export async function InviteFromSection() {
  const t = await getTranslations("landing.sources")
  const labels = Object.fromEntries(
    INVITE_SOURCES.map(({ key }) => [key, t(`labels.${key}`)])
  ) as Record<InviteSource["key"], string>

  return (
    <LandingSection id="invite" title={t("title")} text={t("text")}>
      {/* A little closer to the text than other sections' pictures. */}
      <div className={`${DEMO_GROUP} -mt-6`}>
        <InviteStage
          labels={labels}
          interview={t("interview")}
          developers={
            <>
              <span className="text-lg text-muted-foreground lowercase">
                {t("automate")}
              </span>
              <MoreLink href="/api-docs">{t("developerDocs")}</MoreLink>
            </>
          }
        />
      </div>
    </LandingSection>
  )
}
