// Lets Node import the frontend's TypeScript (its types stripped by Node itself) as the browser
// gets it: "@/…" is frontend/src/…, and a file is named without its .ts. For
// voice_listening_test.mjs: node --import ./evals/scripts/frontend_alias.mjs …
import { existsSync } from "node:fs"
import { registerHooks } from "node:module"
import { fileURLToPath, pathToFileURL } from "node:url"

const SOURCE = fileURLToPath(new URL("../../frontend/src/", import.meta.url))

registerHooks({
  resolve(specifier, context, next) {
    if (specifier.startsWith("@/")) {
      const path = `${SOURCE}${specifier.slice(2)}`

      return next(pathToFileURL(existsSync(`${path}.ts`) ? `${path}.ts` : path).href, context)
    }

    return next(specifier, context)
  },
})
