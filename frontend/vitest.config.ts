import { fileURLToPath } from "node:url"
import { defineConfig } from "vitest/config"

// Unit tests of the pure helpers, in tests/ (`pnpm test`); "@/" is the app's root, as in
// tsconfig.json. Every test starts clean: spies, stubbed globals and env are restored after each
// one, and files and tests run in a random order (the seed is printed; `--sequence.seed=<seed>`
// repeats it), so none can lean on another's leftovers. `pnpm test --coverage` writes the
// coverage of the code these tests are for to coverage/ (CI's changed-lines report).
export default defineConfig({
  resolve: { alias: { "@": fileURLToPath(new URL(".", import.meta.url)) } },
  test: {
    include: ["tests/**/*.test.ts"],
    restoreMocks: true,
    unstubGlobals: true,
    unstubEnvs: true,
    sequence: { shuffle: true },
    coverage: {
      provider: "v8",
      reporter: ["cobertura"],
      include: ["lib/**", "hooks/**", "constants/**"],
    },
  },
})
