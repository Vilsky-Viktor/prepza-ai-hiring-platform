import { getTranslations } from "next-intl/server"

import { AskAgentDemo } from "@/features/landing/components/ask-agent-demo"
import { LandingSection } from "@/features/landing/components/section"
import { GLOW } from "@/config/landing-backgrounds"

/** Just ask the agent: the assistant's panel answering about results and how-tos and inviting a
 * candidate once confirmed, with the three things it does beside it. */
export async function JustAskSection() {
  const t = await getTranslations("landing.justAsk")

  return (
    <LandingSection
      id="agent"
      title={t("title")}
      text={t("text")}
      background={GLOW}
    >
      <AskAgentDemo />
    </LandingSection>
  )
}
