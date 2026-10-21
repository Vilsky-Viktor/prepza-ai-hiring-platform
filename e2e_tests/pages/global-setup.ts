import { deleteLeftovers } from "./helpers/db";
import { warmUp } from "./helpers/warm-up";

// Before a run, what stopped runs left behind (helpers/db.ts), so no test meets another run's
// templates or opt-outs; then every page is compiled once (helpers/warm-up.ts).
export default async function globalSetup() {
  await deleteLeftovers();
  await warmUp();
}
