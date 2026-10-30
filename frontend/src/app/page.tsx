import { ChevronDownIcon } from "lucide-react"
import { getTranslations } from "next-intl/server"

import { CandidatesSection } from "@/features/landing/components/candidates"
import { Closing } from "@/features/landing/components/closing"
import { ComparisonSection } from "@/features/landing/components/comparison"
import { CreateSection } from "@/features/landing/components/create"
import { FreeToStartSection } from "@/features/landing/components/free-to-start"
import { ShareReportsSection } from "@/features/landing/components/share-reports"
import { InviteFromSection } from "@/features/landing/components/invite-from"
import { JustAskSection } from "@/features/landing/components/just-ask"
import { TrustQualitySection } from "@/features/landing/components/trust-quality"
import { VideoButton } from "@/features/landing/components/video-button"
import { JsonLd } from "@/components/common/json-ld"
import { PageHelp } from "@/components/common/page-help"
import { Dotted } from "@/components/common/dot"
import { HeroCallout } from "@/features/landing/components/hero-callout"
import { HeroWires } from "@/features/landing/components/hero-wires"
import { StartTest } from "@/components/common/start-test"
import { LOCALES } from "@/config/i18n"
import { READY_MINUTES } from "@/config/landing"
import { SITE_NAME } from "@/config/seo"
import { publicFetch } from "@/lib/server-api"
import { pageMetadata, siteUrl } from "@/lib/site"
import { organizationData } from "@/lib/structured-data"
import { countryCatalog, priceValues, visitorCatalog } from "@/lib/catalog"
import type { Sizes } from "@/types/generation"

export async function generateMetadata() {
  const t = await getTranslations("site")

  // The layout's title template doesn't reach its own segment's page: the brand is added here.
  return pageMetadata(
    `${t("homeTitle")} · ${SITE_NAME}`,
    t("description", await priceValues(await countryCatalog())),
    "/",
    true
  )
}

export default async function HomePage() {
  const t = await getTranslations("home")
  const site = await getTranslations("site")
  const landing = await getTranslations("landing")
  // Asked together. Without prices (billing is slow or down) the page still shows, without the
  // free offer; without the sizes, the create section shows without its questions-per-topic fact.
  const [catalog, sizes, countryPrices] = await Promise.all([
    visitorCatalog(),
    publicFetch<Sizes>("/generate/sizes").catch(() => null),
    countryCatalog().then(priceValues),
  ])
  const freeCandidates = catalog?.free_candidates ?? null
  const { price } = await priceValues(catalog)

  return (
    // As wide as the page's box (the window less a scrollbar's gutter), for the sections'
    // window-wide backgrounds (config/landing-backgrounds.ts).
    <div className="@container">
      <main className="mx-auto max-w-page px-6">
        <JsonLd
          data={organizationData(siteUrl(), site("description", countryPrices))}
        />
        {/* The promise and the box to start in fill the first screen, under the 3.5rem header; on a
          short phone, with some room above the title. */}
        <div className="relative flex min-h-[calc(100svh-3.5rem)] flex-col items-center justify-center pb-24 max-sm:pt-10">
          <div className="w-full max-w-176 space-y-10">
            <div className="space-y-4">
              {/* The promise, with the video and the page's info button beside it as on other
                pages' titles: in the margin on the start side from wide screens, the info button on
                the title's first line and the video under it; on their own line above it on
                narrower ones. */}
              <div className="relative">
                <div className="-ms-3 mb-2 flex items-center gap-1 xl:absolute xl:end-[calc(100%+0.75rem)] xl:top-2 xl:ms-0 xl:mb-0 xl:flex-col xl:gap-4">
                  <HeroCallout label={landing("howItWorks")}>
                    <PageHelp page="landing" className="[&_svg]:size-7" />
                  </HeroCallout>
                  <HeroCallout label={landing("watchVideo")}>
                    <VideoButton />
                  </HeroCallout>
                </div>
                {/* Two lines, each ending with the logo's blue dot; close together, with room for
                  marks above and below in Arabic, Persian, Hindi, Thai and Vietnamese. */}
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
              </div>
              {/* Each sentence on a line of its own; the price, in the visitor's currency, once
                billing answers. A little wider than the column on its end side, so the first
                sentence fits one line in every language. */}
              <p
                className="text-lg text-balance text-muted-foreground sm:-me-16"
                data-testid="hero-text"
              >
                <span className="block">{t("text")}</span>
                {price && (
                  <span className="block" data-testid="hero-price">
                    {t("price", { price })}
                  </span>
                )}
              </p>
            </div>
            <div className="space-y-5">
              {/* The box with wires from both edges of the window. */}
              <div className="relative">
                <HeroWires />
                <StartTest freeCandidates={freeCandidates} />
              </div>
              {/* What a company gets, in short, right under the box. */}
              <p
                data-testid="hero-proof"
                className="text-center text-sm text-muted-foreground"
              >
                <Dotted
                  items={[
                    landing("proof.anyJob"),
                    landing("proof.languages", { count: LOCALES.length }),
                    landing("proof.ready", { minutes: READY_MINUTES }),
                    landing("proof.noSubscription"),
                  ]}
                />
              </p>
            </div>
          </div>
          {/* The way on to how it works: two blue chevrons that fade down one after the other,
              named for screen readers. */}
          <a
            href="#how"
            aria-label={landing("more")}
            className="absolute bottom-6 flex flex-col items-center rounded-xl p-2 text-primary outline-none hover:opacity-80 focus-visible:ring-3 focus-visible:ring-ring/50"
          >
            <ChevronDownIcon
              aria-hidden
              strokeWidth={2.5}
              className="size-7 animate-[cascade-down_1.6s_ease-in-out_infinite]"
            />
            <ChevronDownIcon
              aria-hidden
              strokeWidth={2.5}
              className="-mt-4 size-7 animate-[cascade-down_1.6s_ease-in-out_0.2s_infinite]"
            />
          </a>
        </div>
        <CreateSection questionsPerTopic={sizes?.questions_per_topic ?? null} />
        <InviteFromSection />
        <CandidatesSection />
        <ShareReportsSection />
        <JustAskSection />
        <TrustQualitySection />
        {catalog && <ComparisonSection catalog={catalog} />}
        {catalog && <FreeToStartSection catalog={catalog} />}
        <Closing freeCandidates={freeCandidates} />
      </main>
    </div>
  )
}
