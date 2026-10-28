import { cn } from "cn"
import { CheckIcon } from "lucide-react"

import { InlineText } from "@/components/questions/inline-text"

type ChoiceOptionsProps = {
  options: string[]
  // The options picked: one, or for a multi-answer question any number.
  chosen: number[]
  // Multi-answer ("select all that apply"): each option is ticked on its own, with a check box.
  multi?: boolean
  disabled: boolean
  onChoose: (optionIndex: number) => void
}

/** A question's options. The ones picked stay marked and can be changed until they're sent;
 * candidates never see which are right. */
export function ChoiceOptions({
  options,
  chosen,
  multi = false,
  disabled,
  onChoose,
}: ChoiceOptionsProps) {
  return (
    <ul className="space-y-2">
      {options.map((option, index) => {
        const picked = chosen.includes(index)

        return (
          // By place: two options can read the same, and the list never reorders.
          <li key={index}>
            <button
              type="button"
              disabled={disabled}
              aria-pressed={picked}
              onClick={() => onChoose(index)}
              className={cn(
                "flex w-full items-start gap-3 rounded-xl border p-4 text-start text-lg leading-7 font-light normal-case transition-colors outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-default",
                picked
                  ? "border-ring bg-surface"
                  : "hover:border-ring hover:bg-surface active:bg-surface"
              )}
            >
              {/* A big check box for an option ticked on its own; the card is marked as in a
                  single-answer question too. */}
              {multi && (
                <span
                  aria-hidden
                  data-testid="option-check"
                  className={cn(
                    "mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-md border-2 border-input",
                    picked &&
                      "border-primary bg-primary-gradient text-primary-foreground gradient-soft"
                  )}
                >
                  {picked && <CheckIcon className="size-4" strokeWidth={3} />}
                </span>
              )}
              <span className="w-4 shrink-0 text-muted-foreground">
                {String.fromCharCode(65 + index)}
              </span>
              <span className="bidi-auto min-w-0 flex-1">
                <InlineText text={option} />
              </span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
