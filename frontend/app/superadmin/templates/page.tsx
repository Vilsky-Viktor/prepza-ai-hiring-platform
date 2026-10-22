import Link from "next/link"
import { notFound } from "next/navigation"
import { getTranslations } from "next-intl/server"

import {
  TemplateBrowser,
  type TemplateSearchParams,
} from "@/components/templates/template-browser"
import { SuperadminHeader } from "@/components/superadmin/superadmin-header"
import { Button } from "@/components/ui/button"
import { translatedTitle } from "@/lib/site"

export const generateMetadata = () => translatedTitle("superadmin", "zone")

/** The superadmin's templates, laid out like the companies list; library answers "not found"
 * to anyone else. */
export default async function TemplatesPage({
  searchParams,
}: {
  searchParams: Promise<TemplateSearchParams>
}) {
  const t = await getTranslations("superadmin")
  const browser = await TemplateBrowser({
    base: "/superadmin/templates",
    listPath: "/library/superadmin/templates",
    params: await searchParams,
    openBase: "/superadmin/templates",
    allLanguages: true,
  })

  if (!browser) {
    notFound()
  }

  return (
    <main className="mx-auto max-w-5xl space-y-8 px-6 py-12">
      <SuperadminHeader
        current="templates"
        action={
          <Button
            render={<Link href="/superadmin/templates/new" />}
            nativeButton={false}
            className="h-12 shrink-0 px-6 text-base"
          >
            {t("new")}
          </Button>
        }
      >
        {browser}
      </SuperadminHeader>
    </main>
  )
}
