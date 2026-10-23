"use client"

import { useTheme } from "next-themes"
import { Toaster as Sonner, type ToasterProps } from "sonner"
import {
  CircleCheckIcon,
  InfoIcon,
  TriangleAlertIcon,
  OctagonXIcon,
  Loader2Icon,
} from "lucide-react"

// How long a toast stays: the library's 4 seconds is too short to read most of ours.
const TOAST_SECONDS = 8

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme()

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      icons={{
        success: <CircleCheckIcon className="size-7" />,
        info: <InfoIcon className="size-7" />,
        warning: <TriangleAlertIcon className="size-7" />,
        error: <OctagonXIcon className="size-7" />,
        loading: <Loader2Icon className="size-7 animate-spin" />,
      }}
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
          "--border-radius": "var(--radius-xl)",
        } as React.CSSProperties
      }
      // Long enough to read a sentence or two before it goes.
      duration={TOAST_SECONDS * 1000}
      toastOptions={{
        classNames: {
          // Larger than the library's 13px, with more room around it, for every kind of toast; the icon
          // too, in a box its size (the library's is 16px).
          toast:
            "cn-toast gap-4! p-5! text-[17px]! [&_[data-button]]:text-sm! [&_[data-icon]]:size-7!",
          // The level shows in the border and the icon only, on the popover's own background:
          // errors red, warnings orange (the site's amber, as in the warning card).
          error: "border-destructive! [&_[data-icon]]:text-destructive",
          warning:
            "border-amber-500! [&_[data-icon]]:text-amber-600 dark:[&_[data-icon]]:text-amber-400",
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
