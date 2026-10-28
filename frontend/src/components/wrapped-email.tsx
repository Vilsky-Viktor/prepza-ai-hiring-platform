/** An email that never runs off the screen: it may break before the @, and only where that
 * isn't enough, inside a part (an email has no spaces to wrap at). */
export function WrappedEmail({ email }: { email: string }) {
  const at = email.indexOf("@")

  return (
    <span className="[overflow-wrap:anywhere]">
      {at > 0 ? (
        <>
          {email.slice(0, at)}
          <wbr />
          {email.slice(at)}
        </>
      ) : (
        email
      )}
    </span>
  )
}
