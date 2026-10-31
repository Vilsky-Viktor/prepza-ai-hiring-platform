import { getLocale, getTranslations } from "next-intl/server"
import type { ReactNode } from "react"

import { BackLink } from "@/components/common/back-link"
import { BulletSection } from "@/components/common/bullet-section"
import { LocalizedLink } from "@/components/common/localized-link"
import { PageKey } from "@/components/common/page-key"
import { TEXT_LINK } from "@/config/links"
import { OPERATOR } from "@/config/operator"
import {
  AI_ACT_APPLIES,
  TRUST_COMPLIANCE,
  TRUST_LINKS,
  TRUST_PRIVACY,
  TRUST_RETENTION,
  TRUST_SECURITY,
} from "@/config/trust"
import { Subprocessors } from "@/features/trust/components/subprocessors"
import { formatDay } from "@/lib/format"
import { pageMetadata } from "@/lib/site"
import { timeTag } from "@/lib/time-tag"

export async function generateMetadata() {
  const t = await getTranslations("trust")

  return pageMetadata(t("title"), t("description"), "/trust", true)
}

const TEXT = "text-base leading-relaxed text-muted-foreground"

/** The trust page: how testee keeps data secure and private, what it provides for the hiring
 * laws, who processes data for it and where, how long data is kept, and the legal documents. */
export default async function TrustPage() {
  const t = await getTranslations("trust")
  const locale = await getLocale()
  const link = (href: string) =>
    function TextLink(chunks: ReactNode) {
      return (
        <LocalizedLink href={href} className={TEXT_LINK}>
          {chunks}
        </LocalizedLink>
      )
    }

  return (
    <main className="mx-auto max-w-page space-y-12 px-6 py-12">
      <PageKey page="trust" />
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
      <BulletSection
        title={t("security.title")}
        items={TRUST_SECURITY.map((key) => t(`security.${key}`))}
      />
      <BulletSection
        title={t("privacy.title")}
        items={TRUST_PRIVACY.map((key) => t(`privacy.${key}`))}
      />
      <BulletSection
        title={t("compliance.title")}
        items={TRUST_COMPLIANCE.map((key) =>
          t.rich(`compliance.${key}`, {
            date: formatDay(AI_ACT_APPLIES, locale),
            ...timeTag(AI_ACT_APPLIES),
            link: link("/documents"),
          })
        )}
      />
      <section className="mx-auto max-w-5xl space-y-4">
        <h2 className="font-heading text-2xl font-medium tracking-tight">
          {t("residency.title")}
        </h2>
        <p className={TEXT}>{t("residency.storage")}</p>
        <p className={TEXT}>{t("residency.transfers")}</p>
      </section>
      <Subprocessors />
      <BulletSection
        title={t("retention.title")}
        items={TRUST_RETENTION.map((key) => t(`retention.${key}`))}
      />
      <section className="mx-auto max-w-5xl space-y-4">
        <h2 className="font-heading text-2xl font-medium tracking-tight">
          {t("accessibility.title")}
        </h2>
        <p className={TEXT}>
          {t.rich("accessibility.text", { link: link("/accessibility") })}
        </p>
      </section>
      <section className="mx-auto max-w-5xl space-y-4">
        <h2 className="font-heading text-2xl font-medium tracking-tight">
          {t("links.title")}
        </h2>
        <ul className={`list-disc space-y-2 ps-6 ${TEXT}`}>
          {TRUST_LINKS.map((item) => (
            <li key={item.key}>
              {t.rich(`links.${item.key}`, { link: link(item.href) })}
            </li>
          ))}
        </ul>
      </section>
      <section className="mx-auto max-w-5xl space-y-4">
        <h2 className="font-heading text-2xl font-medium tracking-tight">
          {t("contact.title")}
        </h2>
        <p className={TEXT}>
          {t.rich("contact.text", {
            email: () => (
              <a href={`mailto:${OPERATOR.email}`} className={TEXT_LINK}>
                {OPERATOR.email}
              </a>
            ),
          })}
        </p>
      </section>
    </main>
  )
}
