import type { Metadata } from "next"
import { notFound } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { GenerationView } from "@/components/generation/generation-view"
import { SignInPage } from "@/components/common/sign-in-page"
import { READY_PARAM } from "@/config/interviews"
import { signedIn } from "@/lib/server-api"

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("generation")

  return { title: t("title") }
}

/** A test being generated: its topic review, then its progress. Reached from a company's test,
 *  whose page `next` points back to, or from the superadmin's templates. */
export default async function GeneratePage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>
  searchParams: Promise<{ next?: string }>
}) {
  if (!(await signedIn())) {
    return <SignInPage />
  }

  const t = await getTranslations("generation")
  const superadmin = await getTranslations("superadmin")
  const { id } = await params
  const next = (await searchParams).next

  if (next === "/superadmin/templates") {
    return (
      <main className="mx-auto flex w-full max-w-page flex-1 flex-col space-y-8 px-6 py-12">
        <GenerationView
          path={`/generate/superadmin/generations/${id}`}
          next={next}
          backHref={next}
          backLabel={superadmin("templates")}
        />
      </main>
    )
  }

  const company = next?.match(/^\/companies\/([^/]+)\/interviews\/([^/?]+)/)

  if (!next || !company) {
    notFound()
  }

  return (
    <main className="mx-auto flex w-full max-w-page flex-1 flex-col space-y-8 px-6 py-12">
      <GenerationView
        // Generations go through companies, so every admin can follow them.
        path={`/companies/interviews/${company[2]}/generation`}
        // Marked as just generated, so the interview shows what to do next.
        next={`${next}${next.includes("?") ? "&" : "?"}${READY_PARAM}=1`}
        backHref={`/companies/${company[1]}/interviews`}
        backLabel={t("interviews")}
      />
    </main>
  )
}
