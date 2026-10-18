import { cn } from "cn"
import { useTranslations } from "next-intl"

/** What the interview adds up to for each candidate, as the API counts it: every question they
 * get, the time each has, and the whole interview's time; three outlined cards in a row, each
 * with its title beside its number (stacked on phones). `small`, for the landing's picture: the
 * cards stay in a row at every width, each with its title above its number. */
export function InterviewEstimate({
  questions,
  questionSeconds,
  minutes,
  small = false,
}: {
  questions: number
  questionSeconds: number
  minutes: number
  small?: boolean
}) {
  const t = useTranslations("interviews")
  const tInvite = useTranslations("invite")
  const facts = [
    { key: "total-questions", label: t("totalQuestions"), value: questions },
    {
      key: "question-seconds",
      label: tInvite("timePerQuestion"),
      value: questionSeconds,
      unit: tInvite("secondsUnit"),
    },
    {
      key: "total-minutes",
      label: tInvite("wholeInterview"),
      value: minutes,
      unit: tInvite("minutesUnit"),
    },
  ]

  return (
    <ul
      className={cn(
        "grid",
        small ? "grid-cols-3 gap-2" : "gap-3 sm:grid-cols-3"
      )}
      data-testid="interview-estimate"
    >
      {facts.map(({ key, label, value, unit }) => (
        <li
          key={key}
          data-testid={key}
          className={cn(
            "flex rounded-2xl border",
            small
              ? "flex-col justify-between gap-1 px-2.5 py-2"
              : "items-center justify-between gap-4 p-5"
          )}
        >
          <span
            className={cn(
              "text-muted-foreground",
              small ? "text-xs leading-tight" : "text-sm"
            )}
          >
            {label}
          </span>
          <span
            className={cn(
              "shrink-0 whitespace-nowrap text-muted-foreground",
              small ? "text-xs" : "text-base"
            )}
          >
            <span
              className={cn(
                "font-medium text-foreground tabular-nums",
                small ? "text-lg" : "text-3xl"
              )}
            >
              {value}
            </span>
            {unit && ` ${unit}`}
          </span>
        </li>
      ))}
    </ul>
  )
}
