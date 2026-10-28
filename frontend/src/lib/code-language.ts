// The language last picked in any code editor's menu, shared by every editor on the page, so
// examples shown in several languages all switch together. Kept while the site stays open in
// the tab.
let chosen: string | null = null
const listeners = new Set<() => void>()

export function chosenCodeLanguage() {
  return chosen
}

export function chooseCodeLanguage(language: string) {
  chosen = language
  listeners.forEach((listener) => listener())
}

export function onCodeLanguage(listener: () => void) {
  listeners.add(listener)

  return () => {
    listeners.delete(listener)
  }
}
