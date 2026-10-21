import teardown from "./teardown"

// Before a run, what stopped runs left behind (teardown.ts: accounts older than its STALE_MS).
// An account that can't be deleted now is reported, not a reason to stop the run: the run's own
// clean-up, after it, is the one that must leave nothing.
export default async function cleanBefore() {
  try {
    await teardown()
  } catch (error) {
    console.warn(`clean-up before the run: ${error}`)
  }
}
