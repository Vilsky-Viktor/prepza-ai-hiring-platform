// Copies voice mode's speech detector files (lib/voice-vad.ts) from their packages into
// public/vad/<vad-web version>-<onnxruntime-web version>/, which config/voice.ts's VAD_FILES
// names: the Silero model and ONNX Runtime's WebAssembly with its loader. Run before the site is
// built or started (package.json's build and dev, the Dockerfile's dev server); public/vad is
// not committed. Safe to run twice.
// Usage: node scripts/copy-vad.mjs
import { copyFileSync, mkdirSync, readFileSync, rmSync } from "node:fs"
import { createRequire } from "node:module"
import { dirname, join } from "node:path"

const require = createRequire(import.meta.url)
const vad = dirname(require.resolve("@ricky0123/vad-web/package.json"))
// The runtime vad-web itself loads (its package exports only its code, in dist/).
const ort = dirname(
  dirname(createRequire(join(vad, "package.json")).resolve("onnxruntime-web"))
)
const version = (folder) =>
  JSON.parse(readFileSync(join(folder, "package.json"), "utf8")).version
const target = new URL(
  `../public/vad/${version(vad)}-${version(ort)}/`,
  import.meta.url
)
const files = [
  join(vad, "dist", "silero_vad_v5.onnx"),
  join(ort, "dist", "ort-wasm-simd-threaded.mjs"),
  join(ort, "dist", "ort-wasm-simd-threaded.wasm"),
]

rmSync(new URL("../public/vad/", import.meta.url), {
  recursive: true,
  force: true,
})
mkdirSync(target, { recursive: true })

for (const file of files) {
  copyFileSync(file, new URL(file.split("/").pop(), target))
}
