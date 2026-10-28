import { redirect } from "next/navigation"

/** The questions tab opens on its flagged tab. */
export default function QuestionsPage() {
  redirect("/superadmin/questions/flagged")
}
