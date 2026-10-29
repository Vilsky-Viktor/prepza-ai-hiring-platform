"use client"

import { useFormatter } from "next-intl"

import { Badge } from "@/components/ui/badge"

/** How many things a menu page holds (an interview's notes), after its name; nothing at 0. */
export function MenuCount({ count }: { count?: number }) {
  const format = useFormatter()

  if (!count) {
    return null
  }

  return (
    <Badge variant="outline" className="tabular-nums" data-testid="menu-count">
      {format.number(count)}
    </Badge>
  )
}
