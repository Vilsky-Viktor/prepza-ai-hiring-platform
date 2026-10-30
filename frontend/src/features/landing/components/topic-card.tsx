"use client"

import { cn } from "cn"
import { SquarePenIcon } from "lucide-react"

import { DEMO_PRESSED } from "@/features/landing/components/demo-panel"
import { Dot } from "@/components/common/dot"
import { buttonVariants } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"

/** A topic as the topic review shows it (features/generation/components/topic-review.tsx),
 * small, as a row of its list: its checkbox, its name and its subtopics under it, and its edit
 * button at the end (the pointer's "edit" while `aimed`), pressed in while `pressed`. `hidden` keeps its
 * place unseen. */
export function TopicCard({
  name,
  subtopics,
  hidden = false,
  aimed = false,
  pressed = false,
}: {
  name: string
  subtopics: string[]
  hidden?: boolean
  aimed?: boolean
  pressed?: boolean
}) {
  return (
    <span
      className={cn(
        "relative flex items-center gap-3 py-2.5 ps-3 pe-11 transition-opacity duration-300",
        hidden && "opacity-0"
      )}
    >
      <Checkbox
        checked
        className="size-5 shrink-0 [&_[data-slot=checkbox-indicator]>svg]:size-3.5"
      />
      <span className="min-w-0 space-y-0.5">
        <span className="block font-medium">{name}</span>
        <span className="block text-xs text-muted-foreground">
          {subtopics.map((subtopic, position) => (
            <span key={subtopic}>
              {position > 0 && <Dot />}
              {subtopic}
            </span>
          ))}
        </span>
      </span>
      <span
        data-demo-target={aimed ? "edit" : undefined}
        className={buttonVariants({
          variant: "ghost",
          size: "icon-sm",
          className: cn(
            "absolute end-2 top-1/2 -translate-y-1/2",
            pressed && DEMO_PRESSED
          ),
        })}
      >
        <SquarePenIcon />
      </span>
    </span>
  )
}
