"use client"

import { cn } from "cn"
import { type RefObject, useEffect, useRef, useState } from "react"

/** A mouse pointer for a landing demo, laid over its panel (whose box must be `relative`): it
 * glides to the middle of `target` and, while `clicking`, presses with a soft glow spreading in
 * the primary colour; hidden while there's no target, and with reduced motion. Each click is keyed
 * by `click`, so the ring plays again for the next one. Measured from the page, so it finds its
 * target at any width. */
export function DemoPointer({
  target,
  clicking,
  click,
}: {
  target: RefObject<HTMLElement | null> | null
  clicking: boolean
  click: number
}) {
  const ref = useRef<HTMLSpanElement>(null)
  // Where the pointer's tip is in its panel; `glide` is off for its first place after hiding.
  const [spot, setSpot] = useState<{
    x: number
    y: number
    glide: boolean
  } | null>(null)

  useEffect(() => {
    const pointer = ref.current
    const panel = pointer?.offsetParent

    if (!pointer || !panel) {
      return
    }

    function place(glide: boolean) {
      const goal = target?.current?.getBoundingClientRect()
      const box = panel!.getBoundingClientRect()

      setSpot((current) =>
        goal
          ? {
              x: goal.left + goal.width / 2 - box.left,
              y: goal.top + goal.height / 2 - box.top,
              glide: glide && current !== null,
            }
          : null
      )
    }

    const frame = requestAnimationFrame(() => place(true))
    // A new width moves the targets: the pointer follows at once. The observer's first call,
    // as it starts, is skipped: the frame above places the pointer.
    let started = false
    const observer = new ResizeObserver(() => {
      if (started) {
        place(false)
      }

      started = true
    })
    observer.observe(panel)

    return () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
    }
  }, [target])

  return (
    <span
      ref={ref}
      aria-hidden
      style={spot ? { transform: `translate(${spot.x}px, ${spot.y}px)` } : {}}
      className={cn(
        "pointer-events-none absolute top-0 left-0 z-10 motion-reduce:hidden",
        spot?.glide && "transition-transform duration-700 ease-in-out",
        !spot && "invisible"
      )}
    >
      {clicking && (
        <span
          key={click}
          className="absolute -top-4 -left-4 size-8 animate-[ripple_0.5s_ease-out_forwards] rounded-full bg-primary/25"
        />
      )}
      <svg
        viewBox="0 0 16 20"
        className={cn(
          "relative h-5 w-4 origin-top-left text-foreground transition-transform duration-150",
          clicking && "scale-85"
        )}
      >
        <path
          d="M1 1 L1 16 L5 12.5 L7.8 18.5 L10.4 17.3 L7.7 11.5 L13 11.5 Z"
          fill="currentColor"
          stroke="var(--background)"
          strokeWidth={1.3}
          strokeLinejoin="round"
        />
      </svg>
    </span>
  )
}
