import type { ReactNode } from "react"

import { PageHelp } from "@/components/page-help"
import type { PageHelpKey } from "@/types/page-help"

export function PageHeader({
  back,
  help,
  before,
  tags,
  title,
  children,
}: {
  // The back arrow, with the page's info button under it when it has one.
  back?: ReactNode
  // Without a back arrow, the info button takes its place: in the page margin, centred on the
  // title's first line (3xl), or on its own line above the title on narrower screens.
  help?: PageHelpKey
  before?: ReactNode
  // Tags such as a status, just under the title.
  tags?: ReactNode
  title: ReactNode
  children?: ReactNode
}) {
  return (
    <div className="space-y-3">
      {before}
      <div className="relative">
        {back}
        {!back && help && (
          <PageHelp
            page={help}
            className="-ms-3 mb-2 xl:absolute xl:end-[calc(100%+0.75rem)] xl:-top-1 xl:ms-0 xl:mb-0"
          />
        )}
        <div className="min-w-0">{title}</div>
      </div>
      {tags && (
        <div className="-mt-2 flex flex-wrap items-center gap-2">{tags}</div>
      )}
      {children}
    </div>
  )
}
