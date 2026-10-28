import { redirect } from "next/navigation"

/** The companies tab became the support tab, which finds a company and acts on it there. */
export default function CompaniesPage() {
  redirect("/superadmin/support")
}
