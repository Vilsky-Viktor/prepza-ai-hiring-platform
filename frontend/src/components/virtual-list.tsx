"use client"

import {
  useVirtualizer,
  useWindowVirtualizer,
  type Virtualizer,
} from "@tanstack/react-virtual"
import { cn } from "cn"
import { useEffect, useLayoutEffect, useRef, useState } from "react"
import type { ReactNode, RefObject } from "react"

import { INITIAL_VIEWPORT, LOAD_AHEAD, OVERSCAN } from "@/constants/lists"

type VirtualListProps<T> = {
  items: T[]
  getKey: (item: T) => string
  renderItem: (item: T, index: number) => ReactNode
  // A typical row's height; rows are measured once rendered.
  estimateSize: number
  // Called when the last rows come into view, to load the next page.
  onEndReached?: () => void
  // Classes for a scroll box the list renders and scrolls in (inside a dialog, say), instead
  // of scrolling with the page. The list owns the box, so it exists when the list starts.
  scrollClassName?: string
  className?: string
}

/** Renders only the rows in and near the viewport, however long the list is. */
export function VirtualList<T>(props: VirtualListProps<T>) {
  return props.scrollClassName !== undefined ? (
    <ElementList {...props} scrollClassName={props.scrollClassName} />
  ) : (
    <WindowList {...props} />
  )
}

function WindowList<T>(props: VirtualListProps<T>) {
  const listRef = useRef<HTMLUListElement>(null)
  // The list's distance from the top of the page, so the page scroll lines up with its rows.
  // Measured again whenever the page changes size: content above the list can grow.
  const [offset, setOffset] = useState(0)

  useLayoutEffect(() => {
    function measure() {
      const top = listRef.current?.getBoundingClientRect().top ?? 0
      setOffset(top + window.scrollY)
    }

    measure()
    const observer = new ResizeObserver(measure)
    observer.observe(document.body)

    return () => observer.disconnect()
  }, [])

  const virtualizer = useWindowVirtualizer({
    count: props.items.length,
    estimateSize: () => props.estimateSize,
    overscan: OVERSCAN,
    scrollMargin: offset,
    initialRect: INITIAL_VIEWPORT,
    // The first render matches the server's even if the user scrolled before the page became
    // interactive; the real position is read right after.
    initialOffset: 0,
  })

  return (
    <Rows
      {...props}
      virtualizer={virtualizer}
      listRef={listRef}
      offset={offset}
    />
  )
}

function ElementList<T>(
  props: VirtualListProps<T> & { scrollClassName: string }
) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLUListElement>(null)
  // The virtualizer's functions change every render, so React Compiler leaves this unmemoized.
  // eslint-disable-next-line react-hooks/incompatible-library
  const virtualizer = useVirtualizer({
    count: props.items.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => props.estimateSize,
    overscan: OVERSCAN,
  })

  return (
    <div ref={scrollRef} className={props.scrollClassName}>
      <Rows {...props} virtualizer={virtualizer} listRef={listRef} offset={0} />
    </div>
  )
}

function Rows<T>({
  items,
  getKey,
  renderItem,
  onEndReached,
  className,
  virtualizer,
  listRef,
  offset,
}: VirtualListProps<T> & {
  virtualizer:
    Virtualizer<Window, Element> | Virtualizer<HTMLDivElement, Element>
  listRef: RefObject<HTMLUListElement | null>
  offset: number
}) {
  const rows = virtualizer.getVirtualItems()
  const last = rows.at(-1)?.index ?? -1

  useEffect(() => {
    if (onEndReached && items.length > 0 && last >= items.length - LOAD_AHEAD) {
      onEndReached()
    }
  }, [last, items.length, onEndReached])

  return (
    <ul
      ref={listRef}
      // box-content: the height is the rows' total, so a border sits outside it.
      className={cn("relative box-content", className)}
      style={{ height: virtualizer.getTotalSize() }}
    >
      {rows.map((row) => (
        <li
          key={getKey(items[row.index])}
          data-index={row.index}
          ref={virtualizer.measureElement}
          className="absolute inset-x-0 top-0"
          style={{ transform: `translateY(${row.start - offset}px)` }}
        >
          {renderItem(items[row.index], row.index)}
        </li>
      ))}
    </ul>
  )
}
