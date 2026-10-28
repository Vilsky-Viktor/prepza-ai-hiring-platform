"use client"

import { usePathname } from "next/navigation"
import { type ReactNode, useSyncExternalStore } from "react"

import { COMPANY_INTERVIEW_PAGE, TIMED_PAGE } from "@/constants/layout"
import { subscribeTimedPageOver, timedPageOver } from "@/lib/timed-page"

/** Its children everywhere but on a timed question's page while its questions run, where they
 * would only distract, back once they're over (a company's interview keeps them away even then);
 * and never on a company's invitation or test link. */
export function NotOnTimedPage({ children }: { children: ReactNode }) {
  const pathname = usePathname()
  const over = useSyncExternalStore(
    subscribeTimedPageOver,
    timedPageOver,
    () => false
  )

  if (
    (TIMED_PAGE.test(pathname) && !over) ||
    COMPANY_INTERVIEW_PAGE.test(pathname)
  ) {
    return null
  }

  return children
}
