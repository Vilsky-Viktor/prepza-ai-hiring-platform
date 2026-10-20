"use client"

import { Slider as SliderPrimitive } from "@base-ui/react/slider"
import { cn } from "cn"
import type { ReactNode } from "react"

/** A one-thumb slider: Base UI's, with a real range input inside the thumb for keyboards and
 * screen readers. `marks` are drawn over the track; `thumb` goes to the thumb. */
function Slider({
  className,
  marks,
  thumb,
  ...props
}: SliderPrimitive.Root.Props<number> & {
  marks?: ReactNode
  thumb?: SliderPrimitive.Thumb.Props
}) {
  return (
    <SliderPrimitive.Root
      data-slot="slider"
      thumbAlignment="center"
      className={cn("w-full data-disabled:opacity-50", className)}
      {...props}
    >
      <SliderPrimitive.Control className="relative flex h-8 w-full touch-none items-center select-none">
        <SliderPrimitive.Track className="relative h-2 w-full rounded-full bg-muted">
          <SliderPrimitive.Indicator className="rounded-full bg-primary" />
          {marks}
          <SliderPrimitive.Thumb
            {...thumb}
            className={cn(
              // Held, the knob grows a little.
              "size-5 rounded-full border-2 border-primary bg-background transition-[scale,box-shadow] duration-150 outline-none active:scale-120 has-focus-visible:ring-3 has-focus-visible:ring-ring/50 data-dragging:scale-120 motion-reduce:transition-none",
              thumb?.className
            )}
          />
        </SliderPrimitive.Track>
      </SliderPrimitive.Control>
    </SliderPrimitive.Root>
  )
}

export { Slider }
