import { cn } from "cn"
import { ArrowUpIcon } from "lucide-react"

import { DEMO_PRESSED } from "@/features/landing/components/demo-panel"
import { DemoPasteMenu } from "@/features/landing/components/demo-paste-menu"
import { buttonVariants } from "@/components/ui/button"

/** The home page's job description box (components/common/start-test.tsx) as a picture, filling
 * its space: `placeholder` until `pasted`, then all of `text` at once, cut off at the field's bottom; the right-click menu that
 * pastes it, opened at `field` while `menu`; and its send button (`send`), dimmed
 * while there's no text, pressed while `pressed` (paste while `pasting`). */
export function DemoDescription({
  text,
  pasted,
  menu,
  pasting,
  pressed,
  placeholder,
  labels,
}: {
  text: string
  pasted: boolean
  menu: boolean
  pasting: boolean
  pressed: boolean
  placeholder: string
  labels: { cut: string; copy: string; paste: string }
}) {
  return (
    <div className="relative flex min-h-0 flex-1 flex-col p-5">
      {/* A long text runs past the field's bottom, cut off there as a field scrolls it. */}
      <div className="min-h-0 flex-1 overflow-hidden text-base">
        <p
          className={cn(
            "whitespace-pre-line",
            !pasted && "text-muted-foreground"
          )}
        >
          {pasted ? text : placeholder}
        </p>
      </div>
      {/* Where the pointer right-clicks, inside the empty box; the menu opens from there. */}
      <span className="absolute start-20 top-16">
        <span data-demo-target="field" className="absolute size-px" />
        <DemoPasteMenu open={menu} pressed={pasting} labels={labels} />
      </span>
      <div className="flex justify-end pt-3">
        <span
          data-demo-target="send"
          className={buttonVariants({
            size: "icon-lg",
            className: cn(
              "rounded-lg",
              !pasted && "opacity-50",
              pressed && DEMO_PRESSED
            ),
          })}
        >
          <ArrowUpIcon />
        </span>
      </div>
    </div>
  )
}
