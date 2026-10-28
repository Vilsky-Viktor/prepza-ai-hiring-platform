import { useEffect, useRef, useState } from "react"

// How long a balance takes to count up to its new value, in milliseconds.
const COUNT_MS = 1200

/** A number that counts up when `value` grows (a top-up arriving), and jumps when it falls,
 * when it first loads (null before) or with reduced motion. `rising` is true while it counts, for
 * a highlight. */
export function useCountUp(value: number | null) {
  const [shown, setShown] = useState(value ?? 0)
  const [rising, setRising] = useState(false)
  const previous = useRef(value)

  useEffect(() => {
    const from = previous.current
    previous.current = value
    let frame = 0

    frame = requestAnimationFrame((began) => {
      if (value === null) {
        return
      }

      const reduced = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
      ).matches

      if (from === null || value <= from || reduced) {
        setShown(value)
        setRising(false)

        return
      }

      function tick(now: number, start: number, end: number) {
        const done = Math.min((now - began) / COUNT_MS, 1)
        // Fast at first, easing into the new balance.
        const eased = 1 - (1 - done) ** 3
        setShown(Math.round(start + (end - start) * eased))

        if (done < 1) {
          frame = requestAnimationFrame((next) => tick(next, start, end))
        } else {
          setRising(false)
        }
      }

      setRising(true)
      tick(began, from, value)
    })

    return () => cancelAnimationFrame(frame)
  }, [value])

  return { shown, rising }
}
