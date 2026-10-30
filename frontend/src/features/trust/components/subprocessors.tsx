import Link from "next/link"
import { getTranslations } from "next-intl/server"

import { EmailText } from "@/components/common/email-text"
import { DEFAULT_LOCALE } from "@/config/i18n"
import { TEXT_LINK } from "@/config/links"
import { SUBPROCESSORS_HEADING } from "@/config/trust"
import { publicFetch } from "@/lib/server-api"
import type { LegalDocument } from "@/types/help"

/** The sub-processors, as the data processing agreement lists them (its binding English text,
 * from the site service): who each is, what for and where. Without an answer, only the link to
 * the agreement. */
export async function Subprocessors() {
  const t = await getTranslations("trust.subprocessors")
  const dpa = await publicFetch<LegalDocument>(
    `/site/help/legal/dpa?language=${DEFAULT_LOCALE}`,
    { locale: DEFAULT_LOCALE }
  )
  const section = dpa?.sections.find(
    (item) => item.heading === SUBPROCESSORS_HEADING
  )

  return (
    <section className="mx-auto max-w-5xl space-y-4">
      <h2 className="font-heading text-2xl font-medium tracking-tight">
        {t("title")}
      </h2>
      <p className="text-base leading-relaxed text-muted-foreground">
        {t.rich("intro", {
          link: (chunks) => (
            <Link href="/dpa" className={TEXT_LINK}>
              {chunks}
            </Link>
          ),
        })}
      </p>
      {section?.items && (
        // In the agreement's own language: English reads left to right in every interface.
        <ul
          lang={DEFAULT_LOCALE}
          dir="ltr"
          className="list-disc space-y-2 ps-6 text-base leading-relaxed text-muted-foreground"
        >
          {/* Index keys, as on the legal pages. */}
          {section.items.map((item, index) => (
            <li key={index}>
              <EmailText text={item} />
            </li>
          ))}
        </ul>
      )}
      <p className="text-base leading-relaxed text-muted-foreground">
        {t("changes")}
      </p>
    </section>
  )
}
