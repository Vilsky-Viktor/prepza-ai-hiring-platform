import { notFound } from "next/navigation"
import { NextIntlClientProvider } from "next-intl"
import { getMessages } from "next-intl/server"

import { clientMessages } from "@/lib/messages"
import { serverFetch } from "@/lib/server-api"

/** The admin zone, for superadmins only: anyone else, signed in or not, finds no such page
 * (the API refuses them too). Its pages get its texts; every other page's browser leaves them
 * out. */
export default async function SuperadminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const me = await serverFetch<{ is_superadmin: boolean }>("/library/me")

  if (!me?.is_superadmin) {
    notFound()
  }

  return (
    <NextIntlClientProvider
      messages={clientMessages(await getMessages(), true)}
    >
      {children}
    </NextIntlClientProvider>
  )
}
