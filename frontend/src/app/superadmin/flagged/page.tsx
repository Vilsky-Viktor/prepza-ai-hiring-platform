import { redirect } from "next/navigation"

/** The flagged tab moved into the questions tab, as a tab of its own. */
export default function FlaggedPage() {
  redirect("/superadmin/questions/flagged")
}
