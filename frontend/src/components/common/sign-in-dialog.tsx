"use client"

import { useTranslations } from "next-intl"
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react"

import { SignInOptions } from "@/components/common/sign-in-options"
import { useAuth } from "@/providers/auth-provider"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

// Opens the dialog; resolves true once signed in, false if it's closed. Asked before the page
// knows who's signed in (Firebase loads after the page), it waits for that first: someone
// already signed in is never asked again.
const SignInContext = createContext<() => Promise<boolean>>(async () => false)

/** The sign-in dialog that a "sign in" button opens (the header, starting an interview); a page
 * that only asks to sign in shows the same options inline. */
export function SignInProvider({ children }: { children: React.ReactNode }) {
  const t = useTranslations("signIn")
  const [open, setOpen] = useState(false)
  const done = useRef<((signedIn: boolean) => void) | null>(null)
  const auth = useAuth()
  const known = useRef(auth)
  const waiting = useRef<(() => void)[]>([])

  useEffect(() => {
    known.current = auth

    if (!auth.loading) {
      waiting.current.splice(0).forEach((resume) => resume())
    }
  }, [auth])

  const request = useCallback(async () => {
    if (known.current.loading) {
      await new Promise<void>((resume) => waiting.current.push(resume))
    }

    if (known.current.user) {
      return true
    }

    return new Promise<boolean>((resolve) => {
      done.current = resolve
      setOpen(true)
    })
  }, [])

  function close(signedIn: boolean) {
    setOpen(false)
    done.current?.(signedIn)
    done.current = null
  }

  return (
    <SignInContext value={request}>
      {children}
      <Dialog open={open} onOpenChange={(next) => !next && close(false)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("title")}</DialogTitle>
          </DialogHeader>
          {/* A new instance each time it opens, so a previous link prompt doesn't linger. */}
          {open && <SignInOptions onSignedIn={() => close(true)} />}
        </DialogContent>
      </Dialog>
    </SignInContext>
  )
}

/** Opens the sign-in dialog; true once signed in. */
export function useSignIn() {
  return useContext(SignInContext)
}
