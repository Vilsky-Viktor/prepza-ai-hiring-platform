"use client"

import { type LucideIcon, UserRoundIcon } from "lucide-react"
import { useEffect, useRef } from "react"

import { useStill } from "@/components/landing/motion-pause"
import { PULSE_SECONDS, SPARK_SPEED } from "@/constants/landing"

/** One wire of the landing page, for an SVG in the focused border's colour (`text-ring`): the
 * curve `d`, in pixels, and a traveller running along it that fades in at its start and out at
 * its end, at the same speed on every screen: a small pulsing dot, or an icon in the primary
 * colour on a small disc of the page's background: a person's as `candidate`, or the given ones,
 * one each run, in turn. It runs on a loop from
 * `delay` seconds, calling `onArrive` each time it reaches the end; or, with `fired`, once each
 * time that number changes. `size` scales the icon and `speed` (pixels a second)
 * replaces the usual speed. Without motion, the wire alone. */
export function Wire({
  d,
  delay = 0,
  fired,
  traveller = "dot",
  size = 1,
  thickness = 1,
  speed = SPARK_SPEED,
  onArrive,
}: {
  d: string
  delay?: number
  fired?: number
  traveller?: "dot" | "candidate" | LucideIcon[]
  size?: number
  // The wire's width, times the usual.
  thickness?: number
  speed?: number
  onArrive?: () => void
}) {
  const motion = useRef<SVGAnimateMotionElement>(null)
  const still = useStill()
  const fade = useRef<SVGAnimateElement>(null)
  // A longer wire takes longer.
  const length = wireLength(d) / speed
  const seconds = `${length}s`
  const once = fired !== undefined
  const begin = once ? "indefinite" : `${delay}s`
  const repeat = once ? undefined : "indefinite"
  const icons = traveller === "candidate" ? [UserRoundIcon] : traveller

  useEffect(() => {
    if (fired) {
      motion.current?.beginElement()
      fade.current?.beginElement()
    }
  }, [fired])

  // The looping traveller's arrivals, on the same clock: at its delay and length, then once
  // every length.
  useEffect(() => {
    if (once || !onArrive || still) {
      return
    }

    let interval: number | undefined
    const first = window.setTimeout(
      () => {
        onArrive()
        interval = window.setInterval(onArrive, length * 1000)
      },
      (delay + length) * 1000
    )

    return () => {
      window.clearTimeout(first)
      window.clearInterval(interval)
    }
  }, [once, onArrive, delay, length, still])

  const animations = (
    <>
      <animateMotion
        ref={motion}
        path={d}
        dur={seconds}
        begin={begin}
        repeatCount={repeat}
      />
      <animate
        ref={fade}
        attributeName="opacity"
        values="0;1;1;0"
        keyTimes="0;0.2;0.8;1"
        dur={seconds}
        begin={begin}
        repeatCount={repeat}
      />
    </>
  )

  return (
    <g>
      <path
        d={d}
        fill="none"
        stroke="currentColor"
        strokeOpacity={0.35}
        strokeWidth={1.5 * thickness}
      />
      {icons !== "dot" ? (
        <g opacity={0} className="motion-reduce:hidden">
          {animations}
          <circle r={10 * size} className="fill-background" />
          {icons.map((Icon, at) => (
            <g key={at} opacity={icons.length > 1 ? 0 : 1}>
              {/* With several, each shows for its own run of every few. */}
              {icons.length > 1 && (
                <animate
                  attributeName="opacity"
                  values={icons.map((_, run) => (run === at ? 1 : 0)).join(";")}
                  calcMode="discrete"
                  dur={`${length * icons.length}s`}
                  begin={begin}
                  repeatCount={repeat}
                />
              )}
              <Icon
                x={-8 * size}
                y={-8 * size}
                width={16 * size}
                height={16 * size}
                className="text-primary"
              />
            </g>
          ))}
        </g>
      ) : (
        <circle
          r={3}
          fill="currentColor"
          opacity={0}
          className="motion-reduce:hidden"
        >
          {animations}
          <animate
            attributeName="r"
            values="2;4;2"
            dur={`${PULSE_SECONDS}s`}
            repeatCount="indefinite"
          />
        </circle>
      )}
    </g>
  )
}

/** A wire's length in pixels, measured on a path that's never shown. */
export function wireLength(d: string) {
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path")
  path.setAttribute("d", d)

  return path.getTotalLength()
}
