import { cn } from "cn"
import { GiftIcon } from "lucide-react"
import { getTranslations } from "next-intl/server"

import { AskAgentButton } from "@/components/common/ask-agent-button"
import { MoreLink } from "@/components/common/more-link"
import { StartTest } from "@/components/common/start-test"
import { GLOW } from "@/config/landing-backgrounds"

/** The features page's last screen, like the landing's: a two-line call to create the first
 * interview, each line ending with the logo's blue dot, and the home page's start box right
 * under it with the free candidates from billing (left out without them); then "more
 * questions?" with Mira, the FAQ and the guides. */
export async function FeaturesClosing({
  freeCandidates,
}: {
  freeCandidates: number | null
}) {
  const t = await getTranslations("featuresPage.closing")
  const landing = await getTranslations("landing")

  return (
    <section
      id="start"
      className={cn(
        GLOW,
        "flex min-h-[calc(100svh-3.5rem)] scroll-mt-16 flex-col items-center justify-center gap-24 py-24"
      )}
    >
      <div className="flex w-full flex-col items-center gap-10">
        <h2 className="no-dot text-center font-heading text-[min(3rem,10.5vw)] leading-none font-medium tracking-tight text-balance sm:text-6xl">
          {t("title")
            .split("\n")
            .map((line) => (
              <span key={line} className="block">
                {line}
                <span className="blue-dot">.</span>
              </span>
            ))}
        </h2>
        <div className="w-full max-w-176 space-y-4">
          <StartTest freeCandidates={freeCandidates} />
          {freeCandidates !== null && (
            <p className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
              <GiftIcon aria-hidden className="size-4 text-primary" />
              {landing("freeToStart.free", { count: freeCandidates })}
            </p>
          )}
        </div>
      </div>
      <div className="space-y-5 text-center">
        <h3 className="no-dot font-heading text-2xl font-medium lowercase">
          {landing("moreQuestions.title")}
        </h3>
        <div className="flex flex-wrap justify-center gap-3">
          <AskAgentButton />
          <MoreLink href="/faq" keepCase className="h-12">
            {landing("moreQuestions.faq")}
          </MoreLink>
          <MoreLink href="/guides" className="h-12">
            {landing("moreQuestions.guides")}
          </MoreLink>
        </div>
      </div>
    </section>
  )
}
