// Voice mode's listening in the browser: how loud and how long counts as speech. The rules of
// what an answer means live in rounds; these only decide when a stretch of speech is sent.

// The microphone's level (root mean square, 0 to 1) that counts as speech.
export const SPEECH_LEVEL = 0.02
// Speech starts after this long above the level, and ends after this long below it.
export const SPEECH_START_MS = 150
export const SPEECH_END_MS = 650
// "Got it." only after at least this much voiced sound: a cough or a click is shorter.
export const ACK_MIN_VOICED_MS = 500
// A spoken answer is sent at most this long (the service's limit is 30 seconds).
export const MAX_ANSWER_MS = 25_000
// Without speech, the recording starts afresh this often, so little silence is ever sent.
export const IDLE_RESTART_MS = 4_000
// How often the level is read.
export const LEVEL_EVERY_MS = 50
// A moment of silence played on the start button's press, which lets the page play sound
// afterwards (browsers allow audio only after a tap).
export const SILENT_WAV =
  "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="

// The voice screen's waves: Mira's bars (the level of what she says) and the candidate's smaller
// ones (the microphone's level). A bar's height is the level times GAIN, at least FLAT_BAR of it
// (a flat line in silence), eased by EASE each frame so it moves smoothly.
export const MIRA_BARS = 28
export const YOU_BARS = 28
export const WAVE_GAIN = 7
// The candidate's wave: its height is the square root of the microphone's level times this gain,
// so ordinary speech fills it well and a loud voice doesn't pin every bar; room noise under
// YOU_WAVE_FLOOR leaves it flat.
export const YOU_WAVE_GAIN = 15
export const YOU_WAVE_FLOOR = 0.006
export const FLAT_BAR = 0.06
export const WAVE_EASE = 0.3
// How long a context may take to start its sound without a tap before the screen asks for one.
export const SOUND_WAIT_MS = 300
