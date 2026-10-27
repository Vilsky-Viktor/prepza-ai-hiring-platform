import { existsSync, readdirSync, statSync } from "node:fs"
import path from "node:path"

// The frontend's folder, and where its code is: frontend/ today, frontend/src/ once it moves
// there (the layout migration). Tests that read the code by path start from SOURCE_ROOT, so
// they find it in either place.
export const FRONTEND = path.resolve(__dirname, "..")
export const SOURCE_ROOT = existsSync(path.join(FRONTEND, "src", "app"))
  ? path.join(FRONTEND, "src")
  : FRONTEND

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
