import { getTranslations } from "next-intl/server"

import { NewTemplate } from "@/features/superadmin/components/new-template"
import { BackLink } from "@/components/common/back-link"
import { translatedTitle } from "@/lib/site"

export const generateMetadata = () => translatedTitle("superadmin", "new")

/** Laid out like a company's "create an interview": a title and the box, nothing else. */
export default async function NewTemplatePage() {
  const t = await getTranslations("superadmin")

  return (
    <main className="mx-auto max-w-page px-6">
      <div className="flex min-h-[calc(100svh-3.5rem)] flex-col items-center justify-center pb-24">
        <div className="w-full max-w-176 space-y-10">
          <div className="relative">
            <BackLink href="/superadmin/templates" className="wide:top-2.5">
              {t("templates")}
            </BackLink>
            <h1 className="font-heading text-5xl font-medium tracking-tight text-balance sm:text-6xl">
              {t("createTitle")}
            </h1>
          </div>
          <NewTemplate />
        </div>
      </div>
    </main>
  )
}
