import { SignInPrompt } from "@/components/common/sign-in-prompt"

/** A signed-in page, for a visitor who isn't: the sign-in prompt at the page's width. Signing in
 * shows the page itself. */
export function SignInPage() {
  return (
    <main className="mx-auto max-w-page px-6 py-12">
      <SignInPrompt />
    </main>
  )
}
