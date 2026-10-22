"use client"

import { cn } from "cn"
import { ArrowLeftIcon } from "lucide-react"
import type { ReactNode } from "react"
import { useTranslations } from "next-intl"

import { LocalizedLink } from "@/components/localized-link"
import { PageHelp } from "@/components/page-help"
import { Button } from "@/components/ui/button"
import type { PageHelpKey } from "@/types/page-help"

export function BackLink({
  href,
  help,
  className,
  children,
}: {
  href: string
  // The page's info button: under the arrow in the page margin, beside it on narrower screens.
  help?: PageHelpKey
  // For a title much larger than usual, to line the arrow up with its lowercase letters.
  className?: string
  children: ReactNode
}) {
  const t = useTranslations("nav")
  const label = typeof children === "string" ? children : t("back")

  return (
    // Beside the title only when the page margin fits it; above the title otherwise.
    // Centred with auto margins: the button's press effect replaces any translate, so a
    // translate-based centre would jump away from the cursor mid-click.
    <div
      data-testid="back-link"
      className={cn(
        "-ms-3 mb-2 flex shrink-0 items-center xl:absolute xl:inset-y-0 xl:end-[calc(100%+1rem)] xl:my-auto xl:ms-0",
        // With the info button, a smaller arrow leaves 8px between the two in the margin.
        help ? "gap-2 xl:h-12" : "xl:h-14",
        className
      )}
    >
      <Button
        variant="ghost"
        size="icon-lg"
        aria-label={label}
        className={cn(
          "size-11 rounded-xl text-muted-foreground",
          help ? "xl:size-12" : "xl:size-14"
        )}
        render={<LocalizedLink href={href} />}
        nativeButton={false}
      >
        <ArrowLeftIcon className="size-6 xl:size-8 rtl:-scale-x-100" />
      </Button>
      {help && (
        <PageHelp
          page={help}
          className="xl:absolute xl:inset-x-0 xl:top-[calc(100%+0.5rem)] xl:mx-auto xl:size-6"
        />
      )}
    </div>
  )
}
