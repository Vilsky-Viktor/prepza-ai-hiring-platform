"use client"

import { CheckIcon, ChevronDownIcon, CopyIcon } from "lucide-react"
import { cn } from "cn"
import { useTranslations } from "next-intl"
import { useSyncExternalStore } from "react"

import { IconButton } from "@/components/icon-button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useCopyId } from "@/hooks/use-copy-id"
import { useHighlight } from "@/hooks/use-highlight"
import { type CodeToken, editorText } from "@/lib/code-tokens"
import {
  chooseCodeLanguage,
  chosenCodeLanguage,
  onCodeLanguage,
} from "@/lib/code-language"

export type CodeVariant = { code: string; language?: string }

/** Code as in an editor: a header with its language and a copy button, then numbered lines in
 * the language's colors (plain until they load). The same example in several languages
 * (`variants`) gets a language menu in the header instead; picking one switches every editor on
 * the page that has it. `header={false}` leaves the header
 * out, as in an interview's or practice's question. `tokens`, each option's colors made on the
 * server (components/highlighted-code.tsx), spare the browser shiki. */
export function CodeEditor({
  code = "",
  language,
  variants,
  header = true,
  className,
  tokens,
}: {
  code?: string
  language?: string
  variants?: CodeVariant[]
  header?: boolean
  className?: string
  tokens?: (CodeToken[][] | null)[]
}) {
  const t = useTranslations("common")
  const options = variants ?? [{ code, language }]
  // The language picked in any editor on the page, when this one has it; else its first.
  const picked = useSyncExternalStore(
    onCodeLanguage,
    chosenCodeLanguage,
    () => null
  )
  const chosen = Math.max(
    0,
    options.findIndex((option) => option.language === picked)
  )
  const shown = options[chosen]
  const text = editorText(shown.code)
  const { copied, copy } = useCopyId(shown.code)
  // Colored in the browser only when the server didn't.
  const colored = useHighlight(text, tokens ? undefined : shown.language)
  const lines: CodeToken[][] =
    tokens?.[chosen] ??
    colored ??
    text.split("\n").map((line) => [{ content: line }])

  return (
    <div
      className={cn(
        "overflow-hidden rounded-2xl border bg-muted text-start",
        className
      )}
      dir="ltr"
    >
      {header && (
        <div className="flex items-center justify-between gap-4 border-b py-1 ps-5 pe-2">
          {options.length > 1 ? (
            <LanguageMenu
              label={t("codeLanguage")}
              languages={options.map((option) => option.language ?? "")}
              chosen={chosen}
              onChange={(index) =>
                chooseCodeLanguage(options[index].language ?? "")
              }
            />
          ) : (
            <span className="font-mono text-sm text-muted-foreground">
              {shown.language}
            </span>
          )}
          <IconButton
            label={copied ? t("codeCopied") : t("copyCode")}
            onClick={copy}
            className="size-10"
          >
            {copied ? (
              <CheckIcon aria-hidden className="text-primary" />
            ) : (
              <CopyIcon aria-hidden />
            )}
          </IconButton>
        </div>
      )}
      <pre className="overflow-x-auto py-4 font-mono text-sm leading-relaxed font-normal">
        <code className="grid min-w-max">
          {lines.map((line, index) => (
            <span key={index} className="flex pe-5">
              <span
                aria-hidden
                className="w-12 shrink-0 pe-4 text-end text-muted-foreground/60 select-none"
              >
                {index + 1}
              </span>
              <span className="whitespace-pre">
                {line.map((token, at) => (
                  <span
                    key={at}
                    style={token.style}
                    className="text-(--shiki-light) dark:text-(--shiki-dark)"
                  >
                    {token.content}
                  </span>
                ))}
                {/* An empty line keeps its height. */}
                {line.length === 0 || line.every((token) => !token.content)
                  ? " "
                  : null}
              </span>
            </span>
          ))}
        </code>
      </pre>
    </div>
  )
}

/** The header's language menu: the chosen language, opening the site's menu of the others. */
function LanguageMenu({
  label,
  languages,
  chosen,
  onChange,
}: {
  label: string
  languages: string[]
  chosen: number
  onChange: (index: number) => void
}) {
  return (
    <div>
      <DropdownMenu>
        <DropdownMenuTrigger
          aria-label={label}
          className="-ms-3 flex h-8 items-center gap-1.5 rounded-full px-3 font-mono text-sm text-muted-foreground transition-colors outline-none hover:bg-background hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
        >
          {languages[chosen]}
          <ChevronDownIcon aria-hidden className="size-4" />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-48 p-2">
          <DropdownMenuRadioGroup
            value={String(chosen)}
            onValueChange={(value) => onChange(Number(value))}
          >
            {languages.map((name, index) => (
              <DropdownMenuRadioItem
                key={name}
                value={String(index)}
                className="px-3 py-2 font-mono text-sm"
              >
                {name}
              </DropdownMenuRadioItem>
            ))}
          </DropdownMenuRadioGroup>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
