import type { KeyboardEvent } from "react"

/** ⌘/Ctrl + Enter sends every multi-line input; plain Enter adds a new line. */
export function isSubmitShortcut(event: KeyboardEvent) {
  return (
    event.key === "Enter" &&
    (event.metaKey || event.ctrlKey) &&
    !event.nativeEvent.isComposing
  )
}

/** In a chat: plain Enter sends; ⌘/Ctrl + Enter (and Shift + Enter) add a new line. */
export function isChatSend(event: KeyboardEvent) {
  return (
    event.key === "Enter" &&
    !event.metaKey &&
    !event.ctrlKey &&
    !event.shiftKey &&
    !event.nativeEvent.isComposing
  )
}

/** ⌘/Ctrl + Enter, the chat's new line (the browser adds none for it). */
export function isChatNewLine(event: KeyboardEvent) {
  return (
    event.key === "Enter" &&
    (event.metaKey || event.ctrlKey) &&
    !event.nativeEvent.isComposing
  )
}
