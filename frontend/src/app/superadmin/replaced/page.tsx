import { redirect } from "next/navigation"

/** The replaced tab moved into the questions tab, as a tab of its own. */
export default function ReplacedPage() {
  redirect("/superadmin/questions/replaced")
}
