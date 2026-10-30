"use client"

import { cn } from "cn"

import { DemoTopicEditor } from "@/features/landing/components/demo-topic-editor"
import { TopicCard } from "@/features/landing/components/topic-card"
import {
  DEMO_ADDED_SUBTOPIC,
  DEMO_EDITED,
  DEMO_NEW_TOPIC,
  DEMO_TOPICS,
} from "@/config/create-demo"

/** The topic review's list (features/generation/components/topic-review.tsx), small: the first
 * `shown` topics, the edited one with its subtopic once `added` and its editor in its place
 * while `editing` (`typed` so far, `typing`, the button `pressed`), and the topic the AI added
 * once `applied`. */
export function DemoTopicList({
  aimed = false,
  shown,
  added,
  applied,
  editing,
  typed,
  typing,
  pressed,
}: {
  // Whether its buttons and fields are the pointer's targets.
  aimed?: boolean
  shown: number
  added: boolean
  applied: boolean
  editing: boolean
  typed: string
  typing: boolean
  pressed: string | null
}) {
  return (
    <ul className="divide-y rounded-xl border">
      {DEMO_TOPICS.slice(0, shown).map((topic) => {
        if (topic.name !== DEMO_EDITED) {
          return (
            <li key={topic.name}>
              <TopicCard name={topic.name} subtopics={topic.subtopics} />
            </li>
          )
        }

        const subtopics = added
          ? [...topic.subtopics, DEMO_ADDED_SUBTOPIC]
          : topic.subtopics

        // The edited topic: its row and its editor in one place, as tall as the taller.
        return (
          <li key={topic.name} className="grid *:[grid-area:1/1]">
            <span className={cn("grid items-center", editing && "invisible")}>
              <TopicCard
                name={topic.name}
                subtopics={subtopics}
                aimed={aimed}
                pressed={pressed === "open"}
              />
            </span>
            <span className={cn(!editing && "invisible")}>
              <DemoTopicEditor
                aimed={aimed}
                subtopics={subtopics}
                typed={typed}
                typing={typing}
                pressed={pressed}
              />
            </span>
          </li>
        )
      })}
      {applied && (
        <li>
          <TopicCard
            name={DEMO_NEW_TOPIC.name}
            subtopics={DEMO_NEW_TOPIC.subtopics}
          />
        </li>
      )}
    </ul>
  )
}
