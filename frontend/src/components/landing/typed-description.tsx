import { cn } from "cn"
import { ArrowUpIcon } from "lucide-react"

import { Caret } from "@/components/landing/caret"
import { buttonVariants } from "@/components/ui/button"

/** The home page's job description box (components/common/start-test.tsx) as a picture, filling its
 * space: `full` typed up to `letters` (the `placeholder` while null), a caret while `typing`,
 * and its send button (`sendRef`), dimmed while there's no text, ringed while `pressed`. The whole text keeps
 * its place unseen, so the box never grows as it's typed. */
export function TypedDescription({
  ref,
  sendRef,
  full,
  letters,
  typing,
  placeholder,
  pressed,
}: {
  // The text's place, where a pointer clicks into the box.
  ref?: React.Ref<HTMLParagraphElement>
  sendRef?: React.Ref<HTMLSpanElement>
  full: string
  letters: number | null
  typing: boolean
  placeholder: string
  pressed: boolean
}) {
  return (
    <div ref={ref} className="flex flex-1 flex-col p-5">
      <div className="grid flex-1 items-start text-base *:[grid-area:1/1]">
        <p ref={ref} className="invisible">
          {full}
        </p>
        <p>
          {letters === null ? (
            <span className="text-muted-foreground">{placeholder}</span>
          ) : (
            <>
              {full.slice(0, letters)}
              {typing && <Caret />}
            </>
          )}
        </p>
      </div>
      <div className="flex justify-end pt-3">
        <span
          ref={sendRef}
          className={buttonVariants({
            size: "icon-lg",
            className: cn(
              "rounded-lg",
              !letters && "opacity-50",
              pressed && "ring-3 ring-ring/50"
            ),
          })}
        >
          <ArrowUpIcon />
        </span>
      </div>
    </div>
  )
}
