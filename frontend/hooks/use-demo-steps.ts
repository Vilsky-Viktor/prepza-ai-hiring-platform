import { useCallback, useEffect, useRef, useState } from "react"

/** A demo's step: how long it shows, in milliseconds; one that `repeat`s counts up to it, a
 * count each `ms` (a letter typed, a row shown). For a demo with a pointer, `point` names what
 * the pointer moves to as the step starts ("none" hides it), and `click` clicks there. */
export type DemoStep = {
  name: string
  ms: number
  repeat?: number
  point?: string
  click?: boolean
}

// A picture that's still until it's seen, then playing for as long as it's on screen.
export const ON_SCREEN: DemoStep[] = [
  { name: "still", ms: 0 },
  { name: "playing", ms: 86_400_000 },
]

// How much of a demo must be on screen for it to play: this share of it, or of the screen for a
// demo taller than that (on phones, panels stacked one under another).
const IN_VIEW = 0.4
// The visible shares the observer reports at, so a tall demo's share of the screen is known.
const STEPS_SEEN = Array.from({ length: 21 }, (_, i) => i / 20)

/** Where a looping demo is in its `steps`: the step's index and its count, and a `ref` for the
 * element whose coming into view starts it. It rests on its first step until then, plays the
 * steps over and over while in view, and starts again from the first when it's back; `skipTo`
 * moves it on to a later step. Without
 * scripts and with reduced motion it rests on the last step, a complete frame. */
export function useDemoSteps<T extends Element>(steps: readonly DemoStep[]) {
  const ref = useRef<T>(null)
  // Set while it plays: moves it on to a later step.
  const jump = useRef<((to: number) => void) | null>(null)
  const last = steps.length - 1
  const [at, setAt] = useState({ index: last, n: steps[last].repeat ?? 0 })

  useEffect(() => {
    const element = ref.current

    if (
      !element ||
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      return
    }

    let index = 0
    let n = 0
    let timer: number | undefined

    function next() {
      if (n < (steps[index].repeat ?? 0)) {
        n += 1
      } else {
        index = (index + 1) % steps.length
        n = 0
      }

      setAt({ index, n })
      timer = window.setTimeout(next, steps[index].ms)
    }

    let shown = false

    jump.current = (to) => {
      if (!skips(shown, index, to)) {
        return
      }

      window.clearTimeout(timer)
      index = to
      n = 0
      setAt({ index, n })
      timer = window.setTimeout(next, steps[index].ms)
    }

    // On the first step until it's seen, and again each time it leaves the screen; scrolling
    // within it doesn't restart it.
    const observer = new IntersectionObserver(
      ([entry]) => {
        const seen = seenOnScreen(
          entry,
          entry.rootBounds?.height ?? window.innerHeight
        )

        if (seen === shown) {
          return
        }

        shown = seen
        window.clearTimeout(timer)
        index = 0
        n = 0
        setAt({ index, n })

        if (seen) {
          timer = window.setTimeout(next, steps[0].ms)
        }
      },
      { threshold: STEPS_SEEN }
    )
    observer.observe(element)

    return () => {
      observer.disconnect()
      window.clearTimeout(timer)
      jump.current = null
    }
  }, [steps])

  // On to step `to` now, if it's playing and hasn't got there yet.
  const skipTo = useCallback((to: number) => jump.current?.(to), [])

  return { ref, skipTo, ...at }
}

/** Whether a demo is seen: IN_VIEW of it on a `screen` this tall, or, for one taller than the
 * screen, IN_VIEW of the screen. */
export function seenOnScreen(
  entry: Pick<
    IntersectionObserverEntry,
    "isIntersecting" | "intersectionRatio" | "intersectionRect"
  >,
  screen: number
) {
  return (
    entry.isIntersecting &&
    (entry.intersectionRatio >= IN_VIEW ||
      entry.intersectionRect.height >= screen * IN_VIEW)
  )
}

/** Whether a demo at step `index` moves on to step `to`: only while it plays, and only forward. */
export function skips(playing: boolean, index: number, to: number) {
  return playing && index < to
}

/** How far the step called `name` of `steps` has counted at `index` and `n`: nothing before
 * it, all of `full` after it. */
export function countedAt(
  steps: readonly DemoStep[],
  { index, n }: { index: number; n: number },
  name: string,
  full: number
) {
  const at = steps.findIndex((step) => step.name === name)

  return index < at ? 0 : index === at ? n : full
}

/** What the pointer is on at step `index` of `steps`: the last step so far that moved it. */
export function pointedAt(steps: readonly DemoStep[], index: number) {
  return steps.slice(0, index + 1).findLast((step) => step.point)?.point
}
