"use client"

import { cn } from "cn"
import { TimerIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useEffect, useRef, useState } from "react"

import { IconStat } from "@/components/common/icon-stat"
import { clock, warningSeconds } from "@/lib/countdown"

function secondsUntil(end: number) {
  return Math.max(0, Math.ceil((end - Date.now()) / 1000))
}

/** Time left on a timed question; calls onExpire once when it reaches zero, or as soon as it
stops being `paused` after that.

`seconds` comes from the server as time left, not a moment, so a wrong device clock doesn't
matter. `questionSeconds` is the question's whole time, which sets when it turns red; in voice
mode `seconds` also holds the reading aloud, during which the clock shows the whole time and
starts once the reading ends. Render it with a key per question, so each question starts its own
clock. */
export function Countdown({
  seconds,
  questionSeconds,
  paused = false,
  onExpire,
}: {
  seconds: number
  questionSeconds: number
  paused?: boolean
  onExpire: () => void
}) {
  const t = useTranslations("company")
  const [end] = useState(() => Date.now() + seconds * 1000)
  const [untilEnd, setLeft] = useState(() => secondsUntil(end))
  const left = Math.min(untilEnd, questionSeconds)
  const expired = useRef(false)

  useEffect(() => {
    // Recomputed from the end every tick, so a slow tab never drifts.
    const timer = window.setInterval(() => setLeft(secondsUntil(end)), 250)

    return () => window.clearInterval(timer)
  }, [end])

  useEffect(() => {
    if (left === 0 && !paused && !expired.current) {
      expired.current = true
      onExpire()
    }
  }, [left, paused, onExpire])

  // role="timer" is read only when asked; the last seconds are announced once, on reaching
  // them, not every second.
  const warningAt = warningSeconds(questionSeconds)
  const warning = left > 0 && left <= warningAt

  return (
    <>
      <span aria-live="polite" className="sr-only">
        {warning && t("timeLeft", { time: clock(warningAt) })}
      </span>
      <IconStat
        role="timer"
        label={t("timeLeft", { time: clock(left) })}
        icon={<TimerIcon aria-hidden className="size-4" />}
        className={cn(
          "font-medium",
          warning &&
            "text-red-600 hover:text-red-600 dark:text-red-400 dark:hover:text-red-400"
        )}
      >
        {clock(left)}
      </IconStat>
    </>
  )
}
