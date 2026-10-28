import { DownloadIcon } from "lucide-react"
import Link from "next/link"
import { getLocale, getTranslations } from "next-intl/server"

import { Badge } from "@/components/ui/badge"
import { IconButton } from "@/components/common/icon-button"
import { DOCUMENTS } from "@/config/documents"
import { DEFAULT_LOCALE } from "@/config/i18n"
import { pageMetadata } from "@/lib/site"
import { LIST_BOX, ROW_HOVER } from "@/config/lists"
import { PageKey } from "@/components/common/page-key"

// Like the report's download button (features/company/components/report-actions.tsx).
export async function generateMetadata() {
  const t = await getTranslations("docs")

  return pageMetadata(t("metaTitle"), t("intro"), "/documents", true)
}

/** Documents for companies to download: instructions, notice and DPIA templates, the DPA. */
export default async function DocsPage() {
  const t = await getTranslations("docs")
  const locale = await getLocale()

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <PageKey page="documents" />
      <header className="space-y-4">
        <h1 className="font-heading text-3xl font-medium tracking-tight">
          {t("title")}
        </h1>
        <p className="text-base text-muted-foreground">
          {t("intro")}
          {/* The documents are English only, like the legal pages. */}
          {locale !== DEFAULT_LOCALE && (
            <span className="block pt-2 text-sm">{t("englishOnly")}</span>
          )}
        </p>
      </header>
      <ul className={`${LIST_BOX} overflow-hidden`}>
        {DOCUMENTS.map((item) => (
          <li
            key={item.key}
            className={`flex items-center justify-between gap-4 py-6 ps-6 pe-3 ${ROW_HOVER}`}
          >
            <div className="min-w-0 space-y-1">
              <span className="block text-xl font-medium">
                {t(`items.${item.key}.title`)}
              </span>
              <p className="text-sm text-muted-foreground">
                {t(`items.${item.key}.description`)}
                {"online" in item && (
                  <>
                    {" "}
                    <Link
                      href={item.online}
                      className="underline underline-offset-4 hover:text-foreground"
                    >
                      {t("readOnline")}
                    </Link>
                  </>
                )}
              </p>
            </div>
            {/* The format beside the download button; above it, on phones. */}
            <div className="flex shrink-0 items-center gap-2 max-sm:flex-col max-sm:gap-1">
              <Badge
                variant="secondary"
                className="h-7 px-3 text-sm font-light"
              >
                {item.format}
              </Badge>
              <IconButton
                label={t("download", { format: item.format })}
                render={<a href={item.href} download />}
              >
                <DownloadIcon className="size-6" />
              </IconButton>
            </div>
          </li>
        ))}
      </ul>
    </main>
  )
}
