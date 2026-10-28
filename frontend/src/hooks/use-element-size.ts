import { useEffect, useRef, useState } from "react"

/** The size of the element at `ref` in pixels, kept up to date as it changes; null until it's
 * first measured. */
export function useElementSize<T extends Element>() {
  const ref = useRef<T>(null)
  const [size, setSize] = useState<{ width: number; height: number } | null>(
    null
  )

  useEffect(() => {
    const element = ref.current

    if (!element) {
      return
    }

    const observer = new ResizeObserver(([entry]) =>
      setSize({
        width: entry.contentRect.width,
        height: entry.contentRect.height,
      })
    )
    observer.observe(element)

    return () => observer.disconnect()
  }, [])

  return { ref, size }
}
