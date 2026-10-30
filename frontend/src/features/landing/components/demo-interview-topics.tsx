"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"

import { Caret } from "@/features/landing/components/caret"
import { SubtopicList } from "@/components/common/subtopic-list"
import { TopicQuestionLimit } from "@/components/common/topic-question-limit"
import { buttonVariants } from "@/components/ui/button"

/** An interview's topics (features/company/components/interview-topics.tsx), small: each with
 * its subtopics, its questions' button and how many of its `count` questions each candidate
 * gets (`limits`), in the editable number's look (components/common/topic-limit.tsx): borderless
 * at rest, its border in the focus colour while `focused` (the topic's name). A changed topic's
 * number is `limit<n>` for the pointer, n its place in `changed`. */
export function DemoInterviewTopics({
  topics,
  count,
  limits,
  changed,
  focused,
}: {
  topics: { name: string; subtopics: string[] }[]
  count: number
  limits: Record<string, number>
  changed: string[]
  focused: string | null
}) {
  const t = useTranslations("questions")

  return (
    <ul className="divide-y rounded-xl border">
      {topics.map((topic) => {
        const target = changed.indexOf(topic.name)

        return (
          // On phones the questions' button and their number take the line under the topic.
          <li
            key={topic.name}
            className="flex items-center justify-between gap-4 p-3 max-sm:flex-col max-sm:items-stretch max-sm:gap-3"
          >
            <span className="min-w-0 space-y-2">
              <span className="block text-base font-medium">{topic.name}</span>
              <SubtopicList subtopics={topic.subtopics} />
            </span>
            <span className="flex shrink-0 flex-col items-center gap-2 max-sm:flex-row max-sm:flex-wrap max-sm:justify-between">
              <span
                className={buttonVariants({
                  variant: "outline",
                  className: "h-8 shrink-0 px-3",
                })}
              >
                {t("manage")}
              </span>
              <TopicQuestionLimit
                count={count}
                limit={limits[topic.name]}
                field={
                  <span
                    data-demo-target={target < 0 ? undefined : `limit${target}`}
                    className={cn(
                      "flex h-9 w-14 items-center justify-center rounded-xl border bg-surface px-1 text-base font-semibold text-foreground tabular-nums",
                      focused === topic.name
                        ? "border-ring-gradient-field"
                        : "border-transparent"
                    )}
                  >
                    {limits[topic.name]}
                    {focused === topic.name && <Caret />}
                  </span>
                }
              />
            </span>
          </li>
        )
      })}
    </ul>
  )
}
