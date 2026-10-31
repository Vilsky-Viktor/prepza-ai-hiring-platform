import { Fragment } from "react"
import { getTranslations } from "next-intl/server"

import { ContactForm } from "@/components/common/contact-form"
import { OPERATOR } from "@/config/operator"
import { pageMetadata } from "@/lib/site"
import { PageKey } from "@/components/common/page-key"
import { CARD } from "@/config/cards"

export async function generateMetadata() {
  const t = await getTranslations("contact")

  return pageMetadata(t("title"), t("description"), "/contact", true)
}

export default async function ContactPage() {
  const t = await getTranslations("contact")

  return (
    <main className="mx-auto max-w-page space-y-10 px-6 py-12">
      <PageKey page="contact" />
      <h1 className="font-heading text-4xl font-medium tracking-tight">
        {t("title")}
      </h1>
      {/* The description in a card beside the form from laptops up (above it on narrower
          screens), so the form keeps a comfortable width. */}
      <div className="grid gap-8 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)] lg:items-start">
        <div className="space-y-4">
          <div className={`space-y-4 ${CARD}`}>
            <p className="text-base text-muted-foreground">{t("intro")}</p>
            {/* What to quote, so support finds what the message is about at once. */}
            <p className="text-base text-muted-foreground">{t("idHint")}</p>
          </div>
          {/* Who runs testee, as labelled rows. */}
          <div className={`space-y-3 ${CARD}`}>
            <dl className="grid grid-cols-[auto_minmax(0,1fr)] gap-x-6 gap-y-2 text-sm">
              {(
                [
                  ["name", OPERATOR.name],
                  ["code", OPERATOR.registryCode],
                  ["address", OPERATOR.address],
                  ["email", OPERATOR.email],
                ] as const
              ).map(([key, value]) => (
                <Fragment key={key}>
                  <dt className="text-muted-foreground">
                    {t(`company.${key}`)}
                  </dt>
                  <dd className="break-words">
                    {key === "email" ? (
                      <a
                        href={`mailto:${value}`}
                        className="hover:text-primary"
                      >
                        {value}
                      </a>
                    ) : (
                      value
                    )}
                  </dd>
                </Fragment>
              ))}
            </dl>
          </div>
        </div>
        <ContactForm />
      </div>
    </main>
  )
}
