import { cn } from "cn"
import { CheckIcon } from "lucide-react"

/** A topic as the topic review shows it (features/generation/components/topic-review.tsx),
 * small, as a card of its own in a list: its checkbox, its name, and `children` (its subtopic
 * chips) under it. `hidden` keeps its place unseen; `highlighted` tints it while it's being
 * changed. */
export function TopicCard({
  name,
  checked = true,
  hidden = false,
  highlighted = false,
  children,
}: {
  name: string
  checked?: boolean
  hidden?: boolean
  highlighted?: boolean
  children?: React.ReactNode
}) {
  return (
    <li
      className={cn(
        "flex gap-3 rounded-xl border bg-background px-3 py-2.5 transition-[opacity,background-color] duration-300",
        hidden && "opacity-0",
        highlighted && "bg-primary/5"
      )}
    >
      <span
        className={cn(
          "flex size-5 shrink-0 items-center justify-center rounded-[6px] border transition-colors",
          checked
            ? "border-primary bg-primary-gradient text-primary-foreground gradient-soft"
            : "border-input"
        )}
      >
        {checked && <CheckIcon className="size-3.5" />}
      </span>
      <span className="min-w-0 flex-1 space-y-1.5">
        <span className="block font-medium">{name}</span>
        {children && <span className="flex flex-wrap gap-1">{children}</span>}
      </span>
    </li>
  )
}

/** A subtopic under a topic card: a soft pill. While `typing`, it's ringed like a field in use;
 * `hidden` keeps its place unseen. */
export function SubtopicChip({
  ref,
  typing = false,
  hidden = false,
  children,
}: {
  ref?: React.Ref<HTMLSpanElement>
  typing?: boolean
  hidden?: boolean
  children: React.ReactNode
}) {
  return (
    <span
      ref={ref}
      className={cn(
        "flex h-5 items-center rounded-full border px-2 text-xs",
        typing ? "border-ring bg-background" : "border-transparent bg-surface",
        hidden && "invisible"
      )}
    >
      {children}
    </span>
  )
}
