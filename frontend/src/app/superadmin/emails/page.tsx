import { redirect } from "next/navigation"

/** The emails tab moved into support: an account's settings on its page, a candidate's
 * company email stops on theirs. */
export default function EmailsPage() {
  redirect("/superadmin/support")
}
