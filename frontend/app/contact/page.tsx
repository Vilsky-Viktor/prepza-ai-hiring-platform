import { getTranslations } from "next-intl/server"

import { ContactForm } from "@/components/contact-form"
import { OPERATOR } from "@/constants/operator"
import { pageMetadata } from "@/lib/site"
import { PageKey } from "@/components/page-key"

export async function generateMetadata() {
  const t = await getTranslations("contact")

  return pageMetadata(t("title"), t("description"), "/contact", true)
}

export default async function ContactPage() {
  const t = await getTranslations("contact")

  return (
    <main className="mx-auto max-w-page space-y-10 px-6 py-12">
      <PageKey page="contact" />
      <header className="max-w-3xl space-y-4">
        <h1 className="font-heading text-4xl font-medium tracking-tight">
          {t("title")}
        </h1>
        <p className="text-base text-muted-foreground">{t("intro")}</p>
        {/* What to quote, so support finds what the message is about at once. */}
        <p className="text-base text-muted-foreground">{t("idHint")}</p>
        <p className="text-sm text-muted-foreground">
          {t("operator", {
            name: OPERATOR.name,
            code: OPERATOR.registryCode,
            address: OPERATOR.address,
            email: OPERATOR.email,
          })}
        </p>
      </header>
      <ContactForm />
    </main>
  )
}
