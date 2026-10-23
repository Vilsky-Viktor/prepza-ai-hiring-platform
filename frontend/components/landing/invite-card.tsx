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
const MARK = "size-6 lg:size-8"

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
        "relative z-10 flex min-w-0 flex-col items-center justify-center gap-2 rounded-2xl border bg-background px-2 pt-3 pb-4 text-center text-sm leading-tight font-medium break-words lowercase lg:flex-row lg:gap-5 lg:overflow-hidden lg:p-4 lg:pe-9 lg:text-start lg:text-xl lg:whitespace-nowrap",
        className
      )}
    >
      {/* From laptops up, the tile fills the card's start edge, top to bottom, like the
          integrations' logo tiles; the ATSs' tile as wide as their logos. */}
      <span
        className={cn(
          "flex h-11 shrink-0 items-center justify-center rounded-xl bg-muted lg:-my-4 lg:-ms-4 lg:h-auto lg:min-h-16 lg:self-stretch lg:rounded-none dark:bg-card",
          mark === "ats" ? "px-1 lg:px-4" : "w-11 lg:w-16"
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

/** A card's mark: its icon in the text colour (white in dark); the ATSs' logos overlapping (two
 * on phones and tablets); the MCP mark in the icons' colour; Slack's logo in its colours. */
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
        className={cn(MARK, "bg-foreground")}
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

  return <Icon className={cn(MARK, "text-foreground")} />
}
