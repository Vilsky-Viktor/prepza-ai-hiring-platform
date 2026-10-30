import { cn } from "cn"

/** A green dot beside a voice's name on the voice screen while that voice talks. It hangs past
 * the name's end (the name's box is `relative`), so the name stays centred. */
export function TalkingDot({ talking }: { talking: boolean }) {
  return (
    <span
      aria-hidden
      data-testid="talking-dot"
      data-talking={talking}
      className={cn(
        "absolute -end-5 top-1/2 size-2.5 -translate-y-1/2 rounded-full bg-emerald-500 transition-opacity",
        talking ? "opacity-100" : "opacity-0"
      )}
    />
  )
}
