"use client"

import { PlayIcon, XIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { HERO_VIDEO_ID } from "@/constants/landing"

/** A play icon, named in its tooltip, that opens prepza's video in a window on the page, played
 * by YouTube's no-cookie player, which loads only once the window opens. The size of the page's
 * info button beside it; a blue ring keeps pulsing out of it to draw the eye (hidden with reduced
 * motion). */
export function VideoButton() {
  const t = useTranslations("landing")
  const common = useTranslations("common")

  return (
    <Dialog>
      <Tooltip>
        <TooltipTrigger
          render={
            <DialogTrigger
              render={
                <button
                  type="button"
                  aria-label={t("videoTooltip")}
                  data-testid="video-button"
                  className="relative inline-flex size-11 shrink-0 cursor-pointer items-center justify-center rounded-full text-primary transition-colors outline-none hover:bg-muted focus-visible:ring-3 focus-visible:ring-ring/50"
                />
              }
            />
          }
        >
          <span
            aria-hidden
            className="absolute inset-1 animate-ping rounded-full border-2 border-primary/60 [animation-duration:2s] motion-reduce:hidden"
          />
          <PlayIcon aria-hidden className="size-6 fill-current" />
        </TooltipTrigger>
        <TooltipContent>{t("videoTooltip")}</TooltipContent>
      </Tooltip>
      {/* The close button sits on the window's corner, over its edge; on phones, where the
          window spans the screen, inside it. */}
      <DialogContent
        showCloseButton={false}
        className="sm:max-w-4xl sm:overflow-visible"
        bodyClassName="gap-0 px-4 pt-16 pb-4 sm:p-6"
      >
        <DialogClose
          render={
            <Button
              variant="outline"
              size="icon"
              className="absolute end-3 top-3 z-10 size-11 rounded-full bg-popover sm:-end-5 sm:-top-5 dark:bg-popover"
            />
          }
        >
          <XIcon className="size-6" />
          <span className="sr-only">{common("close")}</span>
        </DialogClose>
        <DialogTitle className="sr-only">{t("demos")}</DialogTitle>
        <iframe
          src={`https://www.youtube-nocookie.com/embed/${HERO_VIDEO_ID}?autoplay=1&rel=0`}
          title={t("demos")}
          allow="autoplay; encrypted-media; picture-in-picture; fullscreen"
          allowFullScreen
          className="aspect-video w-full rounded-lg"
        />
      </DialogContent>
    </Dialog>
  )
}
