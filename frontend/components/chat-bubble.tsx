import { cn } from "cn"

/** One message of a chat with the AI: the person's on the end side, the AI's on the start;
 * `after` (such as the answer's votes) sits right under it, as wide as the message. */
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
    "bidi-auto rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
    role === "user" ? "bg-muted" : "bg-card",
    className
  )
  const place = cn("w-fit max-w-[85%]", role === "user" && "ms-auto")

  if (after) {
    return (
      <li className={cn(place, "space-y-1")}>
        <div className={bubble}>{content}</div>
        {after}
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
