import { headers } from "next/headers"
import { notFound } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { MAINTENANCE_HEADER } from "@/constants/maintenance"
import { translatedTitle } from "@/lib/site"

export const generateMetadata = () => translatedTitle("maintenance", "title")

/** Every page while maintenance mode is on, for everyone but superadmins: proxy.ts shows it in
 * their place. Visited by its own address, it isn't there. */
export default async function MaintenancePage() {
  if ((await headers()).get(MAINTENANCE_HEADER) !== "closed") {
    notFound()
  }

  const t = await getTranslations("maintenance")

  return (
    <main className="mx-auto flex w-full max-w-page flex-1 flex-col items-center justify-center px-6 py-12">
      <div className="w-full space-y-4 text-center">
        <h1 className="font-heading text-4xl font-medium tracking-tight text-balance sm:text-5xl">
          {t("title")}
        </h1>
        <p className="text-base text-muted-foreground">{t("text")}</p>
      </div>
    </main>
  )
}
