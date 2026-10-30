import { cn } from "cn"
import { CircleCheckIcon, FileTextIcon } from "lucide-react"

import { DEMO_PDF } from "@/config/reports-demo"

/** The browser's sign that a file was saved, small, at the picture's top end corner where a
 * browser shows its downloads: the PDF's name and a check. Shown while `shown`. */
export function DemoDownloadCue({ shown }: { shown: boolean }) {
  return (
    <div
      className={cn(
        "absolute end-4 top-4 z-5 flex items-center gap-3 rounded-xl bg-popover px-4 py-3 text-sm text-popover-foreground shadow-md ring-1 ring-foreground/10 transition-[opacity,translate] duration-200",
        !shown && "invisible -translate-y-1 opacity-0"
      )}
    >
      <FileTextIcon className="size-5 shrink-0 text-muted-foreground" />
      <span className="truncate">{DEMO_PDF}</span>
      <CircleCheckIcon className="size-5 shrink-0 text-primary" />
    </div>
  )
}
