import type { Metadata } from "next"
import { headers } from "next/headers"
import { NextIntlClientProvider } from "next-intl"
import { getLocale, getMessages, getTranslations } from "next-intl/server"

import "@/styles/globals.css"
import { AssistantProvider } from "@/components/assistant/assistant-provider"
import { PaidNotice } from "@/components/billing/paid-notice"
import { PaymentFailed } from "@/components/billing/payment-failed"
import { AuthProvider } from "@/providers/auth-provider"
import { CjkFonts } from "@/components/common/cjk-fonts"
import { UrlLocaleProvider } from "@/components/common/localized-link"
import { LegalBanner } from "@/components/common/legal-banner"
import { MaintenanceNotice } from "@/components/common/maintenance-notice"
import { ScrollTopButton } from "@/components/common/scroll-top-button"
import { SignInProvider } from "@/components/common/sign-in-dialog"
import { NotOnTimedPage } from "@/components/common/not-on-timed-page"
import { SiteFooter } from "@/components/common/site-footer"
import { SiteHeader } from "@/components/common/site-header"
import { ThemeProvider } from "@/providers/theme-provider"
import { TooltipProvider } from "@/components/ui/tooltip"
import { ReferralNotice } from "@/components/common/referral-notice"
import { Toaster } from "@/components/ui/sonner"
import { FONT_VARIABLES } from "@/config/fonts"
import { CJK_LOCALES, type Locale } from "@/config/i18n"
import { SITE_NAME } from "@/config/seo"
import { textDirection } from "@/lib/locale"
import { countryCatalog, priceValues } from "@/lib/catalog"
import { clientMessages } from "@/lib/messages"
import { linkLocale, ogLocale, previewImage, siteUrl } from "@/lib/site"
import { cn } from "cn"
import { DirectionProvider } from "@base-ui/react/direction-provider"

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("site")

  return {
    // Absolute links for shared pages' previews and canonical addresses.
    metadataBase: new URL(siteUrl()),
    title: { default: SITE_NAME, template: `%s · ${SITE_NAME}` },
    description: t("description", await priceValues(await countryCatalog())),
    openGraph: {
      siteName: SITE_NAME,
      type: "website",
      locale: ogLocale(await getLocale()),
      images: previewImage(),
    },
    twitter: { card: "summary_large_image" },
    // Ownership checks for Google Search Console and Bing Webmaster Tools, when set.
    verification: {
      google: process.env.GOOGLE_SITE_VERIFICATION || undefined,
      other: process.env.BING_SITE_VERIFICATION
        ? { "msvalidate.01": process.env.BING_SITE_VERIFICATION }
        : undefined,
    },
  }
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  // The Content-Security-Policy's nonce from proxy.ts, for the theme's inline script.
  const nonce = (await headers()).get("x-nonce") ?? undefined
  const locale = await getLocale()
  const common = await getTranslations("common")

  return (
    // In-page links ("how it works" on the home page) scroll smoothly; Next.js turns it off for
    // navigation between pages (data-scroll-behavior), and reduced motion keeps the jump.
    <html
      lang={locale}
      dir={textDirection(locale)}
      data-scroll-behavior="smooth"
      suppressHydrationWarning
      className={cn(
        "scroll-smooth antialiased motion-reduce:scroll-auto",
        ...FONT_VARIABLES,
        "font-sans"
      )}
    >
      {/* A full-height column: the content grows, so the footer sits at the bottom of short
          pages without making them scroll. Pages take the full width, as auto margins in a
          flex column would otherwise shrink them to their content. */}
      <body className="flex min-h-svh flex-col">
        {CJK_LOCALES.includes(locale as Locale) && <CjkFonts />}
        {/* Base UI's sliders, menus and popups follow the page's direction (right to left in
            Arabic, Hebrew and Persian), arrow keys included. */}
        <DirectionProvider direction={textDirection(locale)}>
          {/* Only what client components use: the admin zone adds its own (its layout). */}
          <NextIntlClientProvider
            messages={clientMessages(await getMessages())}
          >
            <UrlLocaleProvider locale={await linkLocale(locale)}>
              <ThemeProvider nonce={nonce}>
                <AuthProvider>
                  <TooltipProvider>
                    <SignInProvider>
                      <AssistantProvider>
                        <NotOnTimedPage>
                          {/* For keyboards and screen readers: past the header to the page,
                            shown only when tabbed to. */}
                          <a
                            href="#content"
                            className="sr-only focus:not-sr-only focus:fixed focus:start-4 focus:top-4 focus:z-50 focus:rounded-xl focus:border focus:bg-background focus:px-5 focus:py-3 focus:text-base"
                          >
                            {common("skipToContent")}
                          </a>
                          <SiteHeader />
                        </NotOnTimedPage>
                        <div
                          id="content"
                          tabIndex={-1}
                          className="flex flex-1 flex-col outline-none [&>*]:w-full"
                        >
                          <MaintenanceNotice />
                          <NotOnTimedPage>
                            <LegalBanner />
                          </NotOnTimedPage>
                          {children}
                        </div>
                        <NotOnTimedPage>
                          <SiteFooter />
                        </NotOnTimedPage>
                        <ScrollTopButton />
                        <Toaster />
                        <ReferralNotice />
                        <PaidNotice />
                        <PaymentFailed />
                      </AssistantProvider>
                    </SignInProvider>
                  </TooltipProvider>
                </AuthProvider>
              </ThemeProvider>
            </UrlLocaleProvider>
          </NextIntlClientProvider>
        </DirectionProvider>
      </body>
    </html>
  )
}
