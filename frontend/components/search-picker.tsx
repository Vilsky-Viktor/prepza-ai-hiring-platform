"use client"

import { Combobox } from "@base-ui/react/combobox"
import { cn } from "cn"
import { CheckIcon, ChevronDownIcon, SearchIcon } from "lucide-react"

import { useId } from "react"

import { PILL_FILL } from "@/constants/floating-label"
import { MAX_PICKER_SEARCH_LENGTH } from "@/constants/limits"
import { languageOf } from "@/lib/locale"

/** A dropdown of choices with a search field above them, matching what each is called
 * (`labelOf`), each in its own language when `langOf` gives one (a language's own name).
 * `compact` is the small trigger that sits next to a text box's send button; `triggerClassName`
 * sizes the trigger to sit beside other controls. */
export function SearchPicker<T extends string>({
  items,
  value,
  onChange,
  labelOf,
  langOf,
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
  langOf?: (item: T) => string
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
  // Named by its label and the value it shows, so the visible text is in its name (WCAG 2.5.3).
  const labelId = useId()
  const valueId = useId()

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
        aria-labelledby={`${labelId} ${valueId}`}
        className={cn(
          "relative flex items-center justify-between gap-3 rounded-xl border border-transparent normal-case transition-colors outline-none hover:bg-surface focus-visible:border-ring-gradient disabled:opacity-50",
          // Compact, it sits inside a grey input card, a bit lighter than the card.
          compact
            ? cn(PILL_FILL, "h-9 w-48 bg-(--pill) px-4 text-sm")
            : "h-12 w-full max-w-xs bg-surface px-5 text-base",
          triggerClassName
        )}
      >
        <span id={labelId} className="sr-only">
          {label}
        </span>
        <span id={valueId} {...languageOf(langOf?.(value))}>
          <Combobox.Value>
            {valueLabel ? (item: T) => valueLabel(item) : undefined}
          </Combobox.Value>
        </span>
        <ChevronDownIcon
          className={cn("text-muted-foreground", compact ? "size-4" : "size-5")}
        />
      </Combobox.Trigger>
      <Combobox.Portal>
        <Combobox.Positioner sideOffset={6} align="start" className="z-50">
          <Combobox.Popup className="w-max max-w-[calc(100vw-2rem)] min-w-(--anchor-width) overflow-hidden rounded-xl bg-popover text-popover-foreground shadow-md ring-1 ring-foreground/10">
            <div className="flex items-center gap-2 border-b px-3 focus-within:border-ring">
              <SearchIcon className="size-4 text-muted-foreground" />
              <Combobox.Input
                maxLength={MAX_PICKER_SEARCH_LENGTH}
                placeholder={placeholder}
                aria-label={placeholder}
                dir="auto"
                className="h-11 w-full bg-transparent text-base outline-none placeholder:text-placeholder"
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
                  className="flex cursor-default items-center justify-between gap-4 rounded-lg px-3 py-2 text-base outline-none select-none data-highlighted:bg-surface data-highlighted:text-accent-foreground sm:whitespace-nowrap"
                >
                  <span {...languageOf(langOf?.(item))}>{labelOf(item)}</span>
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
