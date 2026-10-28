"use client"

import { UploadIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useRef } from "react"

import { Button } from "@/components/ui/button"
import { INVITE_EXAMPLES } from "@/constants/invites"
import { MAX_BULK_TEXT_LENGTH } from "@/constants/limits"

/** The invite dialog's file tab: the button that picks a CSV or TXT file, what it may hold, and
 * the example files to download. `onChoose` gets the file, or null with why when it's too large
 * to send (it isn't read: the service would refuse it the same way); "" when it's fine. */
export function InviteFileTab({
  file,
  maxInvites,
  onChoose,
}: {
  file: File | null
  // The most candidates one file may invite; null when the API didn't say.
  maxInvites: number | null
  onChoose: (file: File | null, tooLarge: string) => void
}) {
  const t = useTranslations("interviews")
  const fileInput = useRef<HTMLInputElement>(null)

  return (
    <>
      <Button
        type="button"
        variant="outline"
        className="h-16 w-full justify-start gap-3 rounded-xl px-6 text-lg font-normal"
        onClick={() => fileInput.current?.click()}
      >
        <UploadIcon className="size-5 shrink-0 text-muted-foreground" />
        <span className="truncate normal-case">
          {file ? file.name : t("uploadFile")}
        </span>
      </Button>
      <input
        ref={fileInput}
        type="file"
        accept=".csv,.txt,text/csv,text/plain"
        className="hidden"
        onChange={(event) => {
          const chosen = event.target.files?.[0] ?? null
          const tooLarge = chosen !== null && chosen.size > MAX_BULK_TEXT_LENGTH

          onChoose(
            tooLarge ? null : chosen,
            tooLarge
              ? t("fileTooLarge", {
                  kb: Math.round(MAX_BULK_TEXT_LENGTH / 1000),
                })
              : ""
          )
          event.target.value = ""
        }}
      />
      <p className="px-6 py-2 text-center text-sm text-muted-foreground">
        {maxInvites === null
          ? t("fileFormatsNoLimit")
          : t("fileFormats", { count: maxInvites })}
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        {INVITE_EXAMPLES.map((example) => (
          <Button
            key={example.href}
            variant="outline"
            className="h-10 px-5 text-base"
            render={<a href={example.href} download />}
            nativeButton={false}
          >
            {t(example.label)}
          </Button>
        ))}
      </div>
    </>
  )
}
