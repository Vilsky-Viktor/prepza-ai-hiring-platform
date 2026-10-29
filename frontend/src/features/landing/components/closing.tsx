import { cn } from "cn"
import { GiftIcon } from "lucide-react"
import { getTranslations } from "next-intl/server"

import { AskAgentButton } from "@/components/common/ask-agent-button"
import { DemosButton } from "@/features/landing/components/demos-button"
import { MoreLink } from "@/features/landing/components/section"
import { StartButton } from "@/features/landing/components/start-button"
import { GLOW } from "@/config/landing-backgrounds"

/** The landing page's last screen: a two-line call to create the first interview, each line
 * ending with the logo's blue dot, the button back up to the job description box and the free
 * candidates from billing's catalog; under it, "more questions?" with a row of buttons to the
 * agent, the demo videos, the FAQ and the guides. */
export async function Closing({
  freeCandidates,
}: {
  freeCandidates: number | null
}) {
  const t = await getTranslations("landing")

  return (
    <section
      id="help"
      className={cn(
        GLOW,
        "flex min-h-[calc(100svh-3.5rem)] scroll-mt-14 flex-col items-center justify-center gap-24 py-24 text-center"
      )}
    >
      <div className="flex flex-col items-center gap-10">
        <h2 className="no-dot font-heading text-[min(3rem,10.5vw)] leading-none font-medium tracking-tight text-balance sm:text-6xl">
          {t("closing.title")
            .split("\n")
            .map((line) => (
              <span key={line} className="block">
                {line}
                <span className="blue-dot">.</span>
              </span>
            ))}
        </h2>
        <div className="flex flex-col items-center gap-4">
          <StartButton label={t("closing.start")} />
          {freeCandidates !== null && (
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <GiftIcon aria-hidden className="size-4 text-primary" />
              {t("freeToStart.free", { count: freeCandidates })}
            </p>
          )}
        </div>
      </div>
      <div className="space-y-5">
        <h3 className="no-dot font-heading text-2xl font-medium lowercase">
          {t("moreQuestions.title")}
        </h3>
        <div className="flex flex-wrap justify-center gap-3">
          <AskAgentButton />
          <DemosButton label={t("moreQuestions.videos")} />
          <MoreLink href="/faq" keepCase className="h-12">
            {t("moreQuestions.faq")}
          </MoreLink>
          <MoreLink href="/guides" className="h-12">
            {t("moreQuestions.guides")}
          </MoreLink>
        </div>
      </div>
    </section>
  )
}
