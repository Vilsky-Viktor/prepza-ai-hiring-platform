// The home page's "create an interview" demo: its steps, and what its pointer moves to in each
// panel.
import {
  DEMO_ADDED_SUBTOPIC,
  DEMO_CHANGE,
  DEMO_DESCRIPTION,
  DEMO_INVITE_EMAIL,
  DEMO_NEW_TOPIC,
  DEMO_TOPICS,
} from "@/config/create-demo"
import type { DemoStep } from "@/hooks/use-demo-steps"

// The topics the questions are written for: the adjusted ones.
export const WRITTEN = [...DEMO_TOPICS, DEMO_NEW_TOPIC].map(({ name }) => name)

// The pointer clicks into the box and the description is typed, then it clicks send; the topics
// show one by one; it clicks into a topic and a subtopic is typed, then into the request for
// changes, which is typed, then clicks apply and a topic is added; then it clicks approve, the
// questions are written, topic by topic, and the interview is ready: it clicks to invite, the
// invite dialog opens, a candidate's email is typed and sent, and the "sent" notice shows. Last,
// the interview alone: the still frame.
export const STEPS: DemoStep[] = [
  { name: "empty", ms: 900, point: "field" },
  { name: "focus", ms: 300, click: true },
  { name: "typing", ms: 30, repeat: DEMO_DESCRIPTION.length },
  { name: "aim", ms: 800, point: "send" },
  { name: "send", ms: 500, click: true },
  { name: "sent", ms: 400, point: "none" },
  { name: "topics", ms: 400, repeat: DEMO_TOPICS.length },
  { name: "review", ms: 900, point: "topic" },
  { name: "open", ms: 300, click: true },
  { name: "adding", ms: 90, repeat: DEMO_ADDED_SUBTOPIC.length },
  { name: "edited", ms: 900, point: "ask" },
  { name: "ask", ms: 300, click: true },
  { name: "asking", ms: 50, repeat: DEMO_CHANGE.length },
  { name: "aimApply", ms: 800, point: "apply" },
  { name: "apply", ms: 500, click: true },
  { name: "applying", ms: 800, point: "none" },
  { name: "applied", ms: 1200 },
  { name: "aimGo", ms: 800, point: "apply" },
  { name: "go", ms: 500, click: true },
  { name: "writing", ms: 700, repeat: WRITTEN.length, point: "none" },
  { name: "written", ms: 1500 },
  { name: "ready", ms: 1500 },
  { name: "aimInvite", ms: 800, point: "invite" },
  { name: "invite", ms: 500, click: true },
  { name: "aimEmail", ms: 700, point: "email" },
  { name: "focusEmail", ms: 300, click: true },
  { name: "typingEmail", ms: 70, repeat: DEMO_INVITE_EMAIL.length },
  { name: "aimSendInvite", ms: 700, point: "sendInvite" },
  { name: "sendInvite", ms: 450, click: true },
  { name: "invited", ms: 2500, point: "none" },
  { name: "rest", ms: 600 },
]

// The steps the invite dialog is open for.
export const INVITING = [
  "aimEmail",
  "focusEmail",
  "typingEmail",
  "aimSendInvite",
  "sendInvite",
]

// What the pointer moves to in each panel.
export const DESCRIBE = ["field", "send"]
export const ADJUST = ["topic", "ask", "apply"]
export const RESULT = ["invite", "email", "sendInvite"]

export const APPLIED = STEPS.findIndex(({ name }) => name === "applied")
export const WRITING = STEPS.findIndex(({ name }) => name === "writing")
export const READY = STEPS.findIndex(({ name }) => name === "ready")
export const GO = STEPS.findIndex(({ name }) => name === "go")
