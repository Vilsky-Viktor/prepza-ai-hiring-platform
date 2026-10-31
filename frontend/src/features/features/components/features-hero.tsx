import { cn } from "cn"
import { getTranslations } from "next-intl/server"

import { Dotted } from "@/components/common/dot"
import { MoreLink } from "@/components/common/more-link"
import { buttonVariants } from "@/components/ui/button"
import { LOCALES } from "@/config/i18n"
import { READY_MINUTES } from "@/config/landing"

/** The features page's first screen, like the landing's: a two-line promise, each line ending
 * with the logo's blue dot, a short text, the way down to the start box at the page's end and to
 * pricing, and what a company gets in short. */
export async function FeaturesHero() {
  const t = await getTranslations("featuresPage.hero")

  return (
    <header className="flex flex-col items-center gap-10 pt-20 pb-16 text-center sm:pt-28 sm:pb-20">
      <div className="max-w-3xl space-y-5">
        <h1 className="no-dot font-heading text-[min(3rem,10.5vw)] leading-none font-medium tracking-tight text-balance sm:text-6xl [:lang(ar)_&]:leading-tight [:lang(fa)_&]:leading-tight [:lang(hi)_&]:leading-tight [:lang(th)_&]:leading-tight [:lang(vi)_&]:leading-tight">
          {t("title")
            .split("\n")
            .map((line) => (
              <span key={line} className="block">
                {line}
                <span className="blue-dot">.</span>
              </span>
            ))}
        </h1>
        <p className="mx-auto max-w-2xl text-lg leading-relaxed text-balance text-muted-foreground sm:text-xl">
          {t("text")}
        </p>
      </div>
      <div className="flex justify-center gap-3 max-sm:w-full max-sm:flex-col max-sm:items-stretch">
        {/* To the start box at the page's end, where the job description goes. */}
        <a href="#start" className={cn(buttonVariants(), "h-14 px-10 text-lg")}>
          {t("start")}
        </a>
        <MoreLink href="/pricing" className="h-14 px-10 text-lg">
          {t("pricing")}
        </MoreLink>
      </div>
      <p className="text-sm text-muted-foreground">
        <Dotted
          items={[
            t("proof.anyJob"),
            t("proof.languages", { count: LOCALES.length }),
            t("proof.ready", { minutes: READY_MINUTES }),
            t("proof.noSubscription"),
          ]}
        />
      </p>
    </header>
  )
}
