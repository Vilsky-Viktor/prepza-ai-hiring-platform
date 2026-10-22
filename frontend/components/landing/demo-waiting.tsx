/** A demo panel's place while it waits for an earlier panel: muted "waiting…" in its middle. */
export function Waiting({ text }: { text: string }) {
  return (
    <span
      data-testid="demo-waiting"
      className="absolute inset-0 flex items-center justify-center text-sm text-muted-foreground"
    >
      {text}
    </span>
  )
}
