import Image from "next/image"
import { getTranslations } from "next-intl/server"

import { BackLink } from "@/components/back-link"
import { LinkedInIcon } from "@/components/brand-icons"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { JsonLd } from "@/components/json-ld"
import { FOUNDER } from "@/constants/about"
import { pageMetadata, siteUrl } from "@/lib/site"
import { personData } from "@/lib/structured-data"
import { PageKey } from "@/components/page-key"

export async function generateMetadata() {
  const t = await getTranslations("about")

  return pageMetadata(t("title"), t("description"), "/about", true)
}

export default async function AboutPage() {
  const t = await getTranslations("about")

  return (
    <main className="mx-auto max-w-page space-y-16 px-6 py-12">
      <PageKey page="about" />
      <JsonLd data={personData(siteUrl())} />
      <header className="mx-auto max-w-5xl space-y-4">
        {/* The way back home, beside the title as on the app's pages. */}
        <div className="relative">
          <BackLink href="/">{null}</BackLink>
          <h1 className="font-heading text-4xl font-medium tracking-tight">
            {t("title")}
          </h1>
        </div>
        <p className="text-lg text-muted-foreground">{t("intro")}</p>
      </header>
      <section className="mx-auto max-w-5xl space-y-4">
        <h2 className="font-heading text-2xl font-medium tracking-tight">
          {t("company.title")}
        </h2>
        <p className="text-base leading-relaxed text-muted-foreground">
          {t("company.problem")}
        </p>
        <p className="text-base leading-relaxed text-muted-foreground">
          {t("company.approach")}
        </p>
        <p className="text-base leading-relaxed text-muted-foreground">
          {t("company.practice")}
        </p>
      </section>
      <figure className="grid items-center gap-8 rounded-3xl border p-6 sm:p-10 md:grid-cols-[16rem_1fr] md:gap-12">
        <Image
          src={FOUNDER.photo}
          width={FOUNDER.width}
          height={FOUNDER.height}
          alt={FOUNDER.name}
          // Shown 14rem wide (16rem from tablets), far narrower than the file.
          sizes="(min-width: 768px) 16rem, 14rem"
          className="aspect-[3/4] w-56 rounded-3xl object-cover md:w-64"
        />
        <div className="space-y-6">
          <blockquote className="text-xl leading-relaxed italic sm:text-2xl">
            {/* <q> takes the quotation marks of the page's language: “…”, «…», „…“, 「…」. */}
            <q>{t("founder.quote")}</q>
          </blockquote>
          <figcaption className="flex items-center justify-between gap-4">
            <span>
              <span className="block font-medium">{FOUNDER.name}</span>
              <span className="block text-sm text-muted-foreground">
                {t("founder.role")}
              </span>
            </span>
            <Tooltip>
              <TooltipTrigger
                render={
                  <a
                    href={FOUNDER.linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label="LinkedIn"
                    className="flex size-12 items-center justify-center rounded-xl border transition-colors hover:bg-muted [&_svg]:size-6"
                  />
                }
              >
                <LinkedInIcon />
              </TooltipTrigger>
              <TooltipContent>LinkedIn</TooltipContent>
            </Tooltip>
          </figcaption>
        </div>
      </figure>
    </main>
  )
}
