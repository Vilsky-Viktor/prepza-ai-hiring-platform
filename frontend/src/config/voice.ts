// Voice mode's listening in the browser: what counts as speech. A speech-trained detector (Silero
// VAD, run in the page: lib/voice-vad.ts) gives each 32 ms frame of the microphone a probability
// of being speech; the rules of what an answer means live in rounds, these only decide when a
// stretch of speech is sent.

// The detector's model and its files, copied from its packages into public/ when the site is
// built or started (scripts/copy-vad.mjs), under their versions, so a cached file is never
// another version's.
export const VAD_MODEL = "v5"
export const VAD_FILES = "/vad/0.0.31-1.30.0/"
// One frame: 512 samples at 16 kHz.
export const FRAME_MS = 32
// A frame is speech from this probability, and silence under the lower one; the speech ends after
// SPEECH_END_MS of silence. In between, a frame changes nothing.
export const SPEECH_PROBABILITY = 0.6
export const SILENCE_PROBABILITY = 0.45
export const SPEECH_END_MS = 650
// A frame of speech counts as voiced only this loud too (root mean square, 0 to 1): a voice on a
// television in the next room is speech, but not the candidate's.
export const SPEECH_LEVEL = 0.015
// A stretch is the candidate speaking (and is sent) after this much voiced: a short "B" or "yes"
// has about five such frames, a cough or a creaking chair at most two (evals:
// voice_listening_test.mjs).
export const MIN_VOICED_MS = 3 * FRAME_MS
// The detector's options (vad-web's FrameProcessorOptions); its own minimum is the frame, so
// MIN_VOICED_MS decides.
export const VAD_OPTIONS = {
  positiveSpeechThreshold: SPEECH_PROBABILITY,
  negativeSpeechThreshold: SILENCE_PROBABILITY,
  redemptionMs: SPEECH_END_MS,
  preSpeechPadMs: 0,
  minSpeechMs: FRAME_MS,
  submitUserSpeechOnPause: false,
}
// "Got it." only after at least this much voiced sound: a short word gets no acknowledgement.
export const ACK_MIN_VOICED_MS = 500
// A spoken answer is sent at most this long (the service's limit is 30 seconds).
export const MAX_ANSWER_MS = 25_000
// Without speech, the recording starts afresh this often, so little silence is ever sent.
export const IDLE_RESTART_MS = 4_000
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
