"use client"

import { cn } from "cn"
import { ChevronDownIcon } from "lucide-react"
import { usePathname, useRouter, useSearchParams } from "next/navigation"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

/** Chooses how a list is ordered; the choice lives in the address (`?sort=`), so the server
 * renders the first page in that order, and the address's other filters stay. */
export function SortMenu({
  current,
  label,
  options,
  className,
}: {
  current: string
  // The button's text, e.g. "Sort by: newest".
  label: string
  options: { value: string; label: string }[]
  // The trigger's look where a page needs another, e.g. a grey pill.
  className?: string
}) {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  function choose(sort: string) {
    const params = new URLSearchParams(searchParams)
    params.set("sort", sort)
    router.replace(`${pathname}?${params}`, { scroll: false })
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            type="button"
            variant="ghost"
            className={cn("h-10 shrink-0 gap-1.5 px-3 text-sm", className)}
          />
        }
      >
        {label}
        <ChevronDownIcon className="text-muted-foreground" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56 p-2">
        <DropdownMenuRadioGroup value={current} onValueChange={choose}>
          {options.map((option) => (
            <DropdownMenuRadioItem
              key={option.value}
              value={option.value}
              className="px-3 py-2 lowercase"
            >
              {option.label}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
