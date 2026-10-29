import { useEffect, useRef, useState } from "react"

/** Whether the element at `ref` scrolls (its content is taller than it), kept up to date as it
 * or its content resizes; such a box takes keyboard focus so the keys can scroll it. `content`
 * names what's in it (a question's id): when it changes, the new element is measured. */
export function useScrolls<T extends HTMLElement>(content: unknown) {
  const ref = useRef<T>(null)
  const [scrolls, setScrolls] = useState(false)

  useEffect(() => {
    const element = ref.current

    if (!element) {
      setScrolls(false)

      return
    }

    const observer = new ResizeObserver(() =>
      setScrolls(element.scrollHeight > element.clientHeight)
    )
    observer.observe(element)

    for (const child of element.children) {
      observer.observe(child)
    }

    return () => observer.disconnect()
  }, [content])

  return { ref, scrolls }
}
