import { ChevronDownIcon } from "lucide-react"
import ReactMarkdown from "react-markdown"

import { SiteLink } from "@/components/content/markdown"
import { FAQ_MARKDOWN } from "@/lib/markdown"

import type { FaqItem } from "@/types/help"

/** Questions that open to their answers, as on the FAQ page; an answer's links to the site's
 * pages are links. */
export function FaqList({ items }: { items: FaqItem[] }) {
  return (
    <div className="divide-y rounded-3xl bg-card shadow-sm ring-1 ring-foreground/5">
      {items.map((item) => (
        <details key={item.key} className="group px-6">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-4 py-5 font-medium [&::-webkit-details-marker]:hidden">
            {item.question}
            <ChevronDownIcon className="size-5 shrink-0 text-muted-foreground transition-transform group-open:rotate-180" />
          </summary>
          <div className="max-w-3xl pb-5 text-base leading-relaxed text-muted-foreground">
            <ReactMarkdown {...FAQ_MARKDOWN} components={{ a: SiteLink }}>
              {item.answer}
            </ReactMarkdown>
          </div>
        </details>
      ))}
    </div>
  )
}
