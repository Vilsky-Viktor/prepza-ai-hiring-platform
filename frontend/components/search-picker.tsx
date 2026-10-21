"use client"

import { Combobox } from "@base-ui/react/combobox"
import { cn } from "cn"
import { CheckIcon, ChevronDownIcon, SearchIcon } from "lucide-react"

import { MAX_PICKER_SEARCH_LENGTH } from "@/constants/limits"

/** A dropdown of choices with a search field above them, matching what each is called
 * (`labelOf`). `compact` is the small trigger that sits next to a text box's send button;
 * `triggerClassName` sizes the trigger to sit beside other controls. */
export function SearchPicker<T extends string>({
  items,
  value,
  onChange,
  labelOf,
  label,
  placeholder,
  empty,
  disabled = false,
  compact = false,
  triggerClassName,
  valueLabel,
}: {
  items: readonly T[]
  value: T
  onChange: (item: T) => void
  labelOf: (item: T) => string
  // The trigger's accessible name, the search field's placeholder and what shows with no match.
  label: string
  placeholder: string
  empty: string
  disabled?: boolean
  compact?: boolean
  triggerClassName?: string
  // What the trigger shows for the chosen item, when not its label (a currency's code).
  valueLabel?: (item: T) => string
}) {
  return (
    <Combobox.Root
      items={items}
      value={value}
      onValueChange={(item: T | null) => {
        if (item && item !== value) {
          onChange(item)
        }
      }}
      itemToStringLabel={labelOf}
      disabled={disabled}
    >
      <Combobox.Trigger
        aria-label={label}
        className={cn(
          "flex items-center justify-between gap-3 rounded-full normal-case transition-colors outline-none hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50",
          // Compact, it sits inside a grey input card: white stands out there in light mode.
          compact
            ? "h-9 w-48 bg-background px-4 text-sm dark:bg-muted/50"
            : "h-12 w-full max-w-xs bg-muted/50 px-5 text-base",
          triggerClassName
        )}
      >
        <Combobox.Value>
          {valueLabel ? (item: T) => valueLabel(item) : undefined}
        </Combobox.Value>
        <ChevronDownIcon
          className={cn("text-muted-foreground", compact ? "size-4" : "size-5")}
        />
      </Combobox.Trigger>
      <Combobox.Portal>
        <Combobox.Positioner sideOffset={6} align="start" className="z-50">
          <Combobox.Popup className="w-max max-w-[calc(100vw-2rem)] min-w-(--anchor-width) overflow-hidden rounded-xl bg-popover text-popover-foreground shadow-md ring-1 ring-foreground/10">
            <div className="flex items-center gap-2 border-b px-3">
              <SearchIcon className="size-4 text-muted-foreground" />
              <Combobox.Input
                maxLength={MAX_PICKER_SEARCH_LENGTH}
                placeholder={placeholder}
                className="h-11 w-full bg-transparent text-base outline-none placeholder:text-muted-foreground"
              />
            </div>
            <Combobox.Empty className="px-4 py-3 text-sm text-muted-foreground empty:hidden">
              {empty}
            </Combobox.Empty>
            <Combobox.List className="max-h-64 overflow-y-auto p-1">
              {(item: T) => (
                <Combobox.Item
                  key={item}
                  value={item}
                  className="flex cursor-default items-center justify-between gap-4 rounded-lg px-3 py-2 text-base sm:whitespace-nowrap outline-none select-none data-highlighted:bg-accent data-highlighted:text-accent-foreground"
                >
                  {labelOf(item)}
                  <Combobox.ItemIndicator>
                    <CheckIcon className="size-4" />
                  </Combobox.ItemIndicator>
                </Combobox.Item>
              )}
            </Combobox.List>
          </Combobox.Popup>
        </Combobox.Positioner>
      </Combobox.Portal>
    </Combobox.Root>
  )
}
