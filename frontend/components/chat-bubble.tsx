import { cn } from "cn"

/** One message of a chat with the AI: the person's on the end side, the AI's on the start;
 * `after` (such as the answer's votes) sits on its bottom edge, at its end. */
export function ChatBubble({
  role,
  content,
  className,
  after,
}: {
  role: "user" | "assistant"
  // Plain text keeps its line breaks; the assistant's answers come as rendered markdown.
  content: React.ReactNode
  className?: string
  after?: React.ReactNode
}) {
  const bubble = cn(
    "bidi-auto rounded-xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
    role === "user" ? "bg-surface" : "bg-card",
    className
  )
  const place = cn("w-fit max-w-[85%]", role === "user" && "ms-auto")

  if (after) {
    // `after` sits on the message's bottom edge, at its end, half over the border; the room
    // under the message keeps it off the next one.
    return (
      <li className={cn(place, "relative pb-3")}>
        <div className={bubble}>{content}</div>
        <div className="absolute end-3 bottom-0">{after}</div>
      </li>
    )
  }

  return <li className={cn(place, bubble)}>{content}</li>
}

/** The AI's answer before its first words arrive: three dots rising in turn, named `label`
 * for screen readers. */
export function ThinkingDots({ label }: { label: string }) {
  return (
    <>
      <span className="sr-only">{label}</span>
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          aria-hidden
          className="size-1.5 animate-[thinking_1.2s_ease-in-out_infinite] rounded-full bg-muted-foreground"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </>
  )
}
