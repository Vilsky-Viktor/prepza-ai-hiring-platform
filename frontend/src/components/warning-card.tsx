import { cn } from "cn"
import { InfoIcon, TriangleAlertIcon } from "lucide-react"

import { CornerSign } from "@/components/corner-sign"
import { SIGN_CARD } from "@/config/cards"

type CardProps = {
  children: React.ReactNode
  className?: string
  // A button at the end, such as one closing the notice.
  action?: React.ReactNode
}

/** A notice on a soft gray card with its sign in the corner (CornerSign), the text in the muted
 * color, as the maintenance notice shows it. */
function NoticeCard({
  children,
  className,
  icon,
  action,
}: CardProps & { icon: React.ReactNode }) {
  return (
    <div
      role="status"
      className={cn(SIGN_CARD, "flex items-center gap-4 text-base", className)}
    >
      <CornerSign>{icon}</CornerSign>
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
