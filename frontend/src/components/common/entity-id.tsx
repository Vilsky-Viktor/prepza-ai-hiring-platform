"use client"

import { CheckIcon, CopyIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { Button } from "@/components/ui/button"

import { useCopyId } from "@/hooks/use-copy-id"

// Each form's look: small grey text under a page's title, and a normal outline button where
// there's room (Settings). The account menu has its own item (user-menu.tsx).
const FORMS = {
  text: "h-auto rounded-sm border-0 bg-transparent p-0 text-sm font-normal text-muted-foreground hover:bg-transparent hover:text-foreground [&_svg:not([class*='size-'])]:size-3.5 dark:bg-transparent dark:hover:bg-transparent",
  button: "h-10 px-5",
}

/** Copies the id of what a page shows (a company, an interview, a candidate, an account), to
 * quote when writing to testee: support finds it from the id. "copy id" with a copy icon,
 * which turns into a check for a moment once copied. */
export function EntityId({
  id,
  form = "text",
}: {
  id: string
  form?: keyof typeof FORMS
}) {
  const common = useTranslations("common")
  const { copied, copy } = useCopyId(id)

  const label = common(copied ? "idCopied" : "copyId")

  const icon = copied ? (
    <CheckIcon aria-hidden className="text-primary" />
  ) : (
    <CopyIcon aria-hidden />
  )

  // The text stays "copy id"; screen readers hear when it's copied. A normal button has its
  // icon first, as Settings' other buttons do.
  return (
    <Button
      variant="outline"
      className={FORMS[form]}
      aria-label={label}
      data-testid="copy-id"
      data-copied={copied}
      onClick={copy}
    >
      {form === "button" && icon}
      {common("copyId")}
      {form !== "button" && icon}
    </Button>
  )
}
