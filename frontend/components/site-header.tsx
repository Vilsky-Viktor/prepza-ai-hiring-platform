"use client"

import { useTranslations } from "next-intl"

import { AssistantButton } from "@/components/assistant/assistant-button"
import { useAuth } from "@/components/auth-provider"
import { LocalizedLink } from "@/components/localized-link"
import { NotificationBell } from "@/components/notification-bell"
import { SiteNav } from "@/components/site-nav"
import { ThemeModes } from "@/components/theme-toggle"
import { UserMenu } from "@/components/user-menu"
import { Wordmark } from "@/components/wordmark"

export function SiteHeader() {
  const tc = useTranslations("common")
  const { user, loading } = useAuth()

  return (
    // Exactly 3.5rem including the border.
    <header className="h-14 border-b">
      {/* Both sides are h-8 boxes centered in the row, so they share one center line. */}
      <div className="mx-auto flex h-full max-w-page items-center justify-between gap-2 px-4 sm:gap-4 sm:px-6">
        {/* The logo and links share a text baseline; the separator stays centered. */}
        <div className="flex items-baseline gap-2 sm:gap-4">
          {/* The link's name is the logo as shown ("p." on phones) plus "Home", so it always
              contains the visible text (WCAG 2.5.3). */}
          <LocalizedLink href="/" className="flex h-8 items-center">
            <Wordmark className="text-xl leading-none" shortOnPhones />
            <span className="sr-only"> {tc("home")}</span>
          </LocalizedLink>
          <span aria-hidden className="h-5 w-px self-center bg-border" />
          <SiteNav />
        </div>
        <div className="flex h-8 items-center gap-3 max-[359px]:gap-1.5">
          {/* Hidden on phones, where it doesn't fit next to Sign in; signed-in users have it in
              their menu. */}
          {!loading && !user && (
            <div className="hidden w-32 sm:block">
              <ThemeModes />
            </div>
          )}
          <AssistantButton />
          <NotificationBell />
          <UserMenu />
        </div>
      </div>
    </header>
  )
}
