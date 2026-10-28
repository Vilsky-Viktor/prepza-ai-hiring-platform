import { cn } from "cn"
import { ArrowUpIcon, MicIcon } from "lucide-react"

import { Caret } from "@/features/landing/components/caret"
import { buttonVariants } from "@/components/ui/button"

/** The assistant's chat input (features/assistant/components/chat-input.tsx) as a small
 * picture: `text` as typed so far (the `placeholder` while null), with a caret and the field's
 * focus border while `typing`, the voice button's microphone, and its send button (`sendRef`),
 * dimmed while there's no text, ringed while `pressed`. */
export function DemoChatInput({
  ref,
  sendRef,
  text,
  typing,
  placeholder,
  pressed,
}: {
  ref?: React.Ref<HTMLDivElement>
  sendRef?: React.Ref<HTMLSpanElement>
  text: string | null
  typing: boolean
  placeholder: string
  pressed: boolean
}) {
  return (
    <div
      ref={ref}
      className={cn(
        "flex min-h-14 items-center gap-2 rounded-xl border border-transparent bg-surface ps-5 pe-2 transition-colors",
        typing && "border-ring"
      )}
    >
      {/* One line's height whatever it holds, so the caret never moves the text. */}
      <span className="flex h-6 min-w-0 flex-1 items-center text-base">
        {text === null ? (
          <span className="truncate text-muted-foreground">{placeholder}</span>
        ) : (
          <>
            <span className="truncate">{text}</span>
            {typing && <Caret />}
          </>
        )}
      </span>
      {/* The voice button, as the real input has it before send. */}
      <span className="flex size-10 shrink-0 items-center justify-center text-foreground">
        <MicIcon className="size-5" />
      </span>
      <span
        ref={sendRef}
        className={buttonVariants({
          size: "icon",
          className: cn(
            "size-10 shrink-0 rounded-lg",
            !text && "opacity-50",
            pressed && "ring-3 ring-ring/50"
          ),
        })}
      >
        <ArrowUpIcon className="size-5" />
      </span>
    </div>
  )
}
