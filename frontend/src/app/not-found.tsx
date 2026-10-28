import Link from "next/link"
import { getTranslations } from "next-intl/server"

import { Button } from "@/components/ui/button"

export default async function NotFound() {
  const t = await getTranslations("errors")
  const common = await getTranslations("common")

  return (
    <main className="mx-auto flex w-full max-w-page flex-1 flex-col items-center justify-center px-6 py-12">
      <div className="w-full space-y-8 text-center">
        <div className="space-y-4">
          <h1 className="font-heading text-4xl font-medium tracking-tight text-balance sm:text-5xl">
            {t("notFound")}
          </h1>
          <p className="text-base text-muted-foreground">{t("notFoundText")}</p>
        </div>
        <Button
          className="h-12 px-6 text-base"
          render={<Link href="/" />}
          nativeButton={false}
        >
          {common("home")}
        </Button>
      </div>
    </main>
  )
}
