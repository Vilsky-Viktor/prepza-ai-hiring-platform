import { readdirSync, statSync } from "node:fs"
import path from "node:path"

// The frontend's folder, and its code in src/. Tests that read the code by path start from
// SOURCE_ROOT; messages/, content/ and public/ stay in the frontend's folder.
export const FRONTEND = path.resolve(__dirname, "..")
export const SOURCE_ROOT = path.join(FRONTEND, "src")

function files(dir: string, pattern: RegExp): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = path.join(dir, name)

    if (statSync(full).isDirectory()) {
      return files(full, pattern)
    }

    return pattern.test(name) ? [full] : []
  })
}

/** Every file matching `pattern` in the given source folders (absolute paths). A missing
 * folder throws, and so does finding nothing, so no check passes on reading no code. */
export function sourceFiles(dirs: string[], pattern: RegExp): string[] {
  const found = dirs.flatMap((dir) =>
    files(path.join(SOURCE_ROOT, dir), pattern)
  )

  if (found.length === 0) {
    throw new Error(`No ${pattern} files in ${dirs.join(", ")}`)
  }

  return found
}
