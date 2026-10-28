import { ProtectedEmail } from "@/components/protected-email"
import { EMAIL_PATTERN } from "@/constants/contact"

/** Text whose email addresses reach the page only through ProtectedEmail. A server component, so
the full addresses stay out of what's sent to the browser. */
export function EmailText({ text }: { text: string }) {
  // Splitting on a capturing pattern puts each address at an odd index.
  return text.split(EMAIL_PATTERN).map((part, index) => {
    if (index % 2 === 0) {
      return part
    }

    const [user, domain] = part.split("@")

    return <ProtectedEmail key={index} user={user} domain={domain} />
  })
}
