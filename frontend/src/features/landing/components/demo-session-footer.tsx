import { cn } from "cn"

import { DEMO_PRESSED } from "@/features/landing/components/demo-panel"
import { buttonVariants } from "@/components/ui/button"

/** The interview's footer bar (components/common/round-footer.tsx), at the panel's bottom: the
 * way to finish (`finish`) and Next (`next`), shown once an option is `picked`, pressed in while
 * `pressed`. */
export function DemoSessionFooter({
  finish,
  next,
  picked,
  pressed,
}: {
  finish: string
  next: string
  picked: boolean
  pressed: boolean
}) {
  return (
    <div className="-mx-5 mt-auto -mb-5 flex items-center justify-between gap-4 border-t px-5 py-3 sm:-mx-8 sm:-mb-8 sm:px-8">
      <span
        className={buttonVariants({
          variant: "ghost",
          className: "h-10 px-4 text-base",
        })}
      >
        {finish}
      </span>
      <span
        data-demo-target="next"
        className={buttonVariants({
          className: cn(
            "h-10 px-5 text-base transition-opacity",
            !picked && "opacity-0",
            pressed && DEMO_PRESSED
          ),
        })}
      >
        {next}
      </span>
    </div>
  )
}
