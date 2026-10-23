import { cn } from "cn"
import { InfoIcon, TriangleAlertIcon } from "lucide-react"

type CardProps = {
  children: React.ReactNode
  className?: string
  // A button at the end, such as one closing the notice.
  action?: React.ReactNode
}

/** A notice on a soft gray card (the side menu's active item's gray), its sign large and half
 * transparent in the card's top start corner, running under the top and start borders only, the
 * same size and place on a card of any height: a large sign and the text in the muted color, as the maintenance
 * notice shows it. */
function NoticeCard({
  children,
  className,
  icon,
  action,
}: CardProps & { icon: React.ReactNode }) {
  return (
    <div
      role="status"
      className={cn(
        "relative flex items-center gap-4 overflow-hidden rounded-2xl bg-muted/50 p-5 ps-20 text-base",
        className
      )}
    >
      <span
        aria-hidden
        className="absolute -start-5 -top-5 flex opacity-50 [&_svg]:size-20"
      >
        {icon}
      </span>
      <p className="text-muted-foreground">{children}</p>
      {action && <div className="ms-auto shrink-0">{action}</div>}
    </div>
  )
}

/** A warning: an amber warning sign. */
export function WarningCard(props: CardProps) {
  return (
    <NoticeCard
      {...props}
      icon={
        <TriangleAlertIcon
          aria-hidden
          className="shrink-0 text-amber-600 dark:text-amber-400"
        />
      }
    />
  )
}

/** Information: a sign in the primary color. */
export function InfoCard(props: CardProps) {
  return (
    <NoticeCard
      {...props}
      icon={<InfoIcon aria-hidden className="shrink-0 text-primary" />}
    />
  )
}
