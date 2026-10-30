import { cn } from "cn"
import { ClipboardPasteIcon, CopyIcon, ScissorsIcon } from "lucide-react"

import { DEMO_PRESSED } from "@/features/landing/components/demo-panel"

/** A right-click menu over an empty field, in the site's menu look
 * (components/ui/dropdown-menu.tsx), its top corner at where it was opened: cut and copy greyed
 * out, as there's nothing to copy, and paste highlighted (`paste`, for the pointer).
 * Shown while `open`. */
export function DemoPasteMenu({
  open,
  pressed,
  labels,
}: {
  open: boolean
  // Paste, as the pointer clicks it.
  pressed: boolean
  labels: { cut: string; copy: string; paste: string }
}) {
  const items = [
    { label: labels.cut, icon: ScissorsIcon, off: true },
    { label: labels.copy, icon: CopyIcon, off: true },
    { label: labels.paste, icon: ClipboardPasteIcon, off: false },
  ]

  return (
    <span
      className={cn(
        "absolute start-1 top-1 z-5 flex min-w-32 origin-top-left flex-col rounded-xl bg-popover p-1 text-popover-foreground shadow-md ring-1 ring-foreground/10 transition-[opacity,scale] duration-100 rtl:origin-top-right",
        !open && "invisible scale-95 opacity-0"
      )}
    >
      {items.map(({ label, icon: Icon, off }) => (
        <span
          key={label}
          data-demo-target={off ? undefined : "paste"}
          className={cn(
            "flex items-center gap-1.5 rounded-lg px-1.5 py-1 text-sm",
            off ? "opacity-50" : "bg-surface transition-all",
            !off && pressed && DEMO_PRESSED
          )}
        >
          <Icon className="size-4 shrink-0" />
          {label}
        </span>
      ))}
    </span>
  )
}
