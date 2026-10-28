import { cn } from "cn"

export function RoundFooter({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    // data-round-footer: the page scrolls focused elements clear of it (globals.css).
    <div
      data-round-footer
      className="fixed inset-x-0 bottom-0 z-20 border-t bg-background/95 backdrop-blur"
    >
      <div
        className={cn(
          "mx-auto flex max-w-page items-center justify-between gap-4 px-6 py-4",
          className
        )}
      >
        {children}
      </div>
    </div>
  )
}
