import { cn } from "cn"
import Link from "next/link"
import { notFound } from "next/navigation"
import { getLocale, getTranslations } from "next-intl/server"

import { BackLink } from "@/components/common/back-link"
import { EmailText } from "@/components/common/email-text"
import { PageKey } from "@/components/common/page-key"
import { DEFAULT_LOCALE } from "@/config/i18n"
import { formatDay } from "@/lib/format"
import { textDirection } from "@/lib/locale"
import { publicFetch } from "@/lib/server-api"
import { timeTag } from "@/lib/time-tag"
import type { LegalDocument } from "@/types/help"
import { TEXT_LINK } from "@/config/links"
import { CARD } from "@/config/cards"

// A version's name: the day it applies from.
const VERSION = /^\d{4}-\d{2}-\d{2}$/

/** The terms, the privacy policy or the DPA, as the rounds service serves them (the FAQ chat
answers from the same texts): in the page's language when it's translated, with a link to the
English, the binding text; `english` shows the English. */
export async function LegalPage({
  name,
  version,
  english,
}: {
  name: "terms" | "privacy" | "dpa"
  version?: string
  english?: boolean
}) {
  const locale = await getLocale()
  const query = new URLSearchParams({
    language: english ? DEFAULT_LOCALE : locale,
  })

  if (version && VERSION.test(version)) {
    query.set("version", version)
  }

  const document = await publicFetch<LegalDocument>(
    `/site/help/legal/${name}?${query}`
  )

  if (!document) {
    notFound()
  }

  const { intro, sections, versions, in_force: inForce } = document
  const shown = document.version
  const t = await getTranslations("legal")
  const link = (to: string, inEnglish = english) => {
    const params = new URLSearchParams()

    if (to !== document.current) {
      params.set("version", to)
    }

    if (inEnglish) {
      params.set("language", DEFAULT_LOCALE)
    }

    return params.size ? `/${name}?${params}` : `/${name}`
  }

  return (
    <main className="mx-auto max-w-page space-y-10 px-6 py-12">
      <PageKey page={name} />
      <header className="mx-auto max-w-5xl space-y-4">
        {/* The way back home, beside the title as on the app's pages. */}
        <div className="relative">
          <BackLink href="/">{null}</BackLink>
          <h1 className="font-heading text-4xl font-medium tracking-tight">
            {t(`titles.${name}`)}
          </h1>
        </div>
        <p className="text-sm text-muted-foreground">
          {document.language !== DEFAULT_LOCALE ? (
            <span className="block pb-2">
              {t.rich("translatedRead", {
                link: (chunks) => (
                  <Link href={link(shown, true)} className={TEXT_LINK}>
                    {chunks}
                  </Link>
                ),
              })}
            </span>
          ) : (
            locale !== DEFAULT_LOCALE && (
              <span className="block pb-2">{t("englishOnly")}</span>
            )
          )}
          {document.state === "in_force"
            ? t.rich("inForce", {
                date: formatDay(shown, locale),
                ...timeTag(shown),
              })
            : t.rich(`${document.state}Read`, {
                date: formatDay(shown, locale),
                ...timeTag(shown),
                link: (chunks) => (
                  <Link href={link(inForce)} className={TEXT_LINK}>
                    {chunks}
                  </Link>
                ),
              })}
        </p>
      </header>
      {/* In the text's own language: English reads left to right in every interface. */}
      <div
        lang={document.language}
        dir={textDirection(document.language)}
        className="mx-auto max-w-5xl space-y-10"
      >
        <p className="text-base leading-relaxed text-muted-foreground">
          <EmailText text={intro} />
        </p>
        {sections.map((section) => (
          <section key={section.heading} className="space-y-3">
            <h2 className="font-heading text-2xl font-medium">
              {section.heading}
            </h2>
            {/* Index keys: a text as a key would put its email address in the page's data. */}
            {section.paragraphs?.map((paragraph, index) => (
              <p
                key={index}
                className="text-base leading-relaxed text-muted-foreground"
              >
                <EmailText text={paragraph} />
              </p>
            ))}
            {section.items && (
              <ul className="list-disc space-y-2 ps-5 text-base leading-relaxed text-muted-foreground">
                {section.items.map((item, index) => (
                  <li key={index}>
                    <EmailText text={item} />
                  </li>
                ))}
              </ul>
            )}
          </section>
        ))}
      </div>
      {versions.length > 0 && (
        // Every version, in a card at the end, like the contact page's cards: the one shown in
        // the muted color, the others as links.
        <nav
          className={`mx-auto max-w-5xl space-y-3 ${CARD} text-sm text-muted-foreground`}
        >
          <h2 className="text-lg font-medium text-foreground">
            {t("versions")}
          </h2>
          <ul className="flex flex-wrap gap-x-6 gap-y-2">
            {versions.map((item) => (
              <li key={item}>
                {item === shown ? (
                  <time dateTime={item}>{formatDay(item, locale)}</time>
                ) : (
                  // A list, not running text: the dates stay regular weight.
                  <Link
                    href={link(item)}
                    className={cn(TEXT_LINK, "font-normal")}
                  >
                    <time dateTime={item}>{formatDay(item, locale)}</time>
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </nav>
      )}
    </main>
  )
}
