import type { VoiceAnswer, VoiceHandlers } from "@/types/round"

// What Mira's reaction needs from the voice screen (hooks/use-voice-interviewer.ts).
export type Mira = {
  sessionId: string
  questionId: string
  handlers: VoiceHandlers
  // Whether an answer was saved by voice.
  confirmed: { current: boolean }
  // Says a clip, then listens; listens at once.
  say: (path: string) => Promise<void>
  listen: () => void
}

/** What Mira does with a spoken answer, understood: no words are ignored; a yes sends the choice
 * waiting; a clear choice (the service decides) is picked on screen and sent at once, and she
 * says it was saved; any other choice is picked on screen and she asks to confirm it; a no, or
 * words she didn't catch, get a request to say it again, every time. */
export async function react(answer: VoiceAnswer, mira: Mira) {
  if (answer.intent === "noise") {
    mira.listen()

    return
  }

  if (answer.intent === "confirm") {
    mira.confirmed.current = true

    // Moved on: Mira stays thinking until the next question is read. Not sent: she listens.
    if (!(await mira.handlers.onConfirm())) {
      mira.listen()
    }

    return
  }

  if (answer.intent === "choose" && answer.clear) {
    mira.handlers.onPick(mira.questionId, answer.picks)
    mira.confirmed.current = true

    // Moved on: Mira stays thinking until the next question is read. Not sent: she listens.
    if (!(await mira.handlers.onSave(answer.picks))) {
      mira.listen()
    }

    return
  }

  if (answer.intent === "choose") {
    mira.handlers.onPick(mira.questionId, answer.picks)
    const query = answer.picks.map((pick) => `picks=${pick}`).join("&")
    await mira.say(`${mira.sessionId}/voice/confirmations?${query}`)

    return
  }

  const phrase = answer.intent === "reject" ? "again" : "unclear"
  await mira.say(`${mira.sessionId}/voice/phrases/${phrase}`)
}
