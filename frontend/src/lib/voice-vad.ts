import { VAD_FILES, VAD_MODEL, VAD_OPTIONS } from "@/config/voice"
import type { Detector, OpenDetector } from "@/lib/voice-listening"

/** Silero VAD (vad-web, on ONNX Runtime's WebAssembly) on the microphone already open: loaded
 * only when voice mode starts, its model and runtime from VAD_FILES (the site's own). It reads
 * `stream` through `context` and never stops the microphone itself. Its steps run one after
 * another, so a pause asked for while it is still loading pauses it once it has. */
export function micDetector(
  context: AudioContext,
  stream: MediaStream
): OpenDetector {
  return async (events) => {
    const { MicVAD } = await import("@ricky0123/vad-web")
    const vad = await MicVAD.new({
      ...VAD_OPTIONS,
      model: VAD_MODEL,
      audioContext: context,
      getStream: async () => stream,
      pauseStream: async () => undefined,
      resumeStream: async () => stream,
      startOnLoad: false,
      // An audio worklet's script would need its own place in the page's script policy.
      processorType: "ScriptProcessor",
      baseAssetPath: VAD_FILES,
      onnxWASMBasePath: VAD_FILES,
      ortConfig: (ort) => {
        ort.env.logLevel = "error"
        // One thread: more need a cross-origin isolated page.
        ort.env.wasm.numThreads = 1
      },
      onFrameProcessed: (probabilities, frame) =>
        events.onFrame(probabilities.isSpeech, frame),
      onSpeechStart: events.onSpeechStart,
      onSpeechEnd: () => events.onSpeechEnd(),
      onVADMisfire: events.onMisfire,
    })
    let queue = Promise.resolve()

    // Never throws: a step that fails leaves listening as it was.
    function step(run: () => Promise<void>) {
      queue = queue.then(run).catch((error) => {
        console.warn("Voice detection step failed", error)
      })

      return queue
    }

    const detector: Detector = {
      start: () => step(vad.start),
      pause: () => step(vad.pause),
      destroy: () => step(vad.destroy),
    }

    return detector
  }
}
