import { cn } from "cn"
import {
  BracesIcon,
  FileUpIcon,
  LinkIcon,
  MailIcon,
  PanelsTopLeftIcon,
  SparklesIcon,
} from "lucide-react"

import { KeepAcronyms } from "@/components/keep-acronyms"
import { MCP_MARK } from "@/constants/ai-apps"
import { ATS_PROVIDERS } from "@/constants/ats"
import { PHONE_ATS_LOGOS, type InviteSource } from "@/constants/invite-demo"
import { SLACK } from "@/constants/slack"

const ICONS = {
  email: MailIcon,
  file: FileUpIcon,
  link: LinkIcon,
  api: BracesIcon,
  sdk: PanelsTopLeftIcon,
  agent: SparklesIcon,
}

// A mark's size in its tile.
const MARK = "size-6 lg:size-7"

type Mark = InviteSource["key"] | "slack"

/** One card on the invite stage, bordered on the page's background like the app's lists: its
 * mark (an icon, the ATSs' logos, the MCP mark or Slack's) in a soft tile like the integrations'
 * logo tiles, and its short label. On phones and tablets a cell of the grid, the tile above the
 * label; from laptops up, side by side. */
export function InviteCard({
  ref,
  mark,
  label,
  className,
  style,
}: {
  ref?: React.Ref<HTMLLIElement>
  mark: Mark
  label: string
  className?: string
  style?: React.CSSProperties
}) {
  return (
    <li
      ref={ref}
      style={style}
      data-testid="invite-card"
      data-mark={mark}
      className={cn(
        "relative z-10 flex min-w-0 flex-col items-center justify-center gap-2 rounded-2xl border bg-background px-2 pt-3 pb-4 text-center text-sm leading-tight font-medium break-words lowercase lg:flex-row lg:gap-4 lg:p-3 lg:pe-7 lg:text-start lg:text-lg lg:whitespace-nowrap",
        className
      )}
    >
      {/* The ATSs' tile as wide as their logos, so they never run under the label. */}
      <span
        className={cn(
          "flex h-11 shrink-0 items-center justify-center rounded-xl bg-muted lg:h-13 dark:bg-card",
          mark === "ats" ? "px-1 lg:px-3" : "w-11 lg:w-13"
        )}
      >
        <MarkIcon mark={mark} />
      </span>
      <span className="min-w-0">
        <KeepAcronyms text={label} />
      </span>
    </li>
  )
}

/** A card's mark: its icon in the primary colour; the ATSs' logos overlapping (two on phones and
 * tablets); the MCP mark in the icons' blue; Slack's logo in its colours. */
function MarkIcon({ mark }: { mark: Mark }) {
  if (mark === "slack") {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={SLACK.logo} alt="" className={cn(MARK, "object-contain")} />
    )
  }

  if (mark === "apps") {
    return (
      <span
        className={cn(MARK, "bg-primary")}
        style={{
          mask: `url(${MCP_MARK}) center / contain no-repeat`,
          WebkitMask: `url(${MCP_MARK}) center / contain no-repeat`,
        }}
      />
    )
  }

  if (mark === "ats") {
    return (
      <span className="flex -space-x-1.5 rtl:space-x-reverse">
        {ATS_PROVIDERS.map((provider, index) => (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            key={provider.id}
            src={provider.logo}
            alt=""
            className={cn(
              MARK,
              "rounded-md bg-background object-contain ring-2 ring-muted dark:ring-card",
              index >= PHONE_ATS_LOGOS && "max-lg:hidden"
            )}
          />
        ))}
      </span>
    )
  }

  const Icon = ICONS[mark]

  return <Icon className={cn(MARK, "text-primary")} />
}
