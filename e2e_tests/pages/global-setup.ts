import { deleteLeftovers } from "./helpers/db";

// Before a run, what stopped runs left behind (helpers/db.ts), so no test meets another run's
// templates or opt-outs.
export default async function globalSetup() {
  await deleteLeftovers();
}
