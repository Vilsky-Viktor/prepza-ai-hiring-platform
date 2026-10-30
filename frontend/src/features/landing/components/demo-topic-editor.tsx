"use client"

import { cn } from "cn"
import { PlusIcon, XIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { DEMO_PRESSED } from "@/features/landing/components/demo-panel"
import { Caret } from "@/features/landing/components/caret"
import { buttonVariants } from "@/components/ui/button"

/** A topic's editor (features/generation/components/topic-editor.tsx), small and without its name
 * field: its `subtopics` as chips to remove, the new subtopic's field (`typed` so far, a caret
 * while `typing`; `subtopic`), add (`add`) and done (`done`), the one
 * `pressed` pressed in. */
export function DemoTopicEditor({
  aimed,
  subtopics,
  typed,
  typing,
  pressed,
}: {
  // Whether its parts are the pointer's targets.
  aimed: boolean
  subtopics: string[]
  typed: string
  typing: boolean
  pressed: string | null
}) {
  const t = useTranslations("generation")
  const ring = (name: string) => pressed === name && DEMO_PRESSED

  return (
    <span className="flex flex-col gap-2.5 p-3">
      <span className="flex flex-wrap gap-1.5">
        {subtopics.map((subtopic) => (
          <span
            key={subtopic}
            className="flex items-center gap-0.5 rounded-full bg-surface py-0.5 ps-2.5 pe-0.5 text-xs"
          >
            {subtopic}
            <span className="flex size-5 items-center justify-center rounded-full">
              <XIcon className="size-3" />
            </span>
          </span>
        ))}
      </span>
      <span className="flex items-center gap-1.5">
        <span
          data-demo-target={aimed ? "subtopic" : undefined}
          className={cn(
            "flex h-8 min-w-0 flex-1 items-center rounded-xl border bg-surface px-3",
            typing ? "border-ring" : "border-input"
          )}
        >
          {typed || typing ? (
            <>
              <span className="truncate">{typed}</span>
              {typing && <Caret />}
            </>
          ) : (
            <span className="truncate text-muted-foreground">
              {t("addSubtopic")}
            </span>
          )}
        </span>
        <span
          data-demo-target={aimed ? "add" : undefined}
          className={buttonVariants({
            variant: "outline",
            className: cn("h-8 px-2.5", !typed && "opacity-50", ring("add")),
          })}
        >
          <PlusIcon />
          {t("add")}
        </span>
        <span
          data-demo-target={aimed ? "done" : undefined}
          className={buttonVariants({
            variant: "secondary",
            className: cn("h-8 px-3", ring("done")),
          })}
        >
          {t("done")}
        </span>
      </span>
    </span>
  )
}
