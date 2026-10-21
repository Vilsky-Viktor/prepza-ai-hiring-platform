import { getTranslations } from "next-intl/server"

import { FaqList } from "@/components/faq-list"
import { JsonLd } from "@/components/json-ld"
import { faqPath } from "@/lib/catalog"
import { plainAnswer } from "@/lib/markdown"
import { publicFetch } from "@/lib/server-api"
import { pageMetadata } from "@/lib/site"
import type { FaqItem } from "@/types/help"
import { PageKey } from "@/components/page-key"

export async function generateMetadata() {
  const t = await getTranslations("faq")

  return pageMetadata(t("title"), t("description"), "/faq", true)
}

export default async function FaqPage() {
  const t = await getTranslations("faq")
  // The questions come from the rounds service in the page's language, with today's prices in
  // the visitor's currency.
  const items = (await publicFetch<FaqItem[]>(await faqPath())) ?? []
  // FAQ structured data, so search engines can show the answers.
  const structured = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: { "@type": "Answer", text: plainAnswer(item.answer) },
    })),
  }

  return (
    <main className="mx-auto max-w-5xl space-y-10 px-6 py-12">
      <PageKey page="faq" />
      {/* None without questions: an empty FAQPage is invalid. */}
      {items.length > 0 && <JsonLd data={structured} />}
      <header className="space-y-4">
        <h1 className="font-heading text-4xl font-medium tracking-tight">
          {t("title")}
        </h1>
        <p className="text-base text-muted-foreground">{t("intro")}</p>
      </header>
      <FaqList items={items} />
    </main>
  )
}
