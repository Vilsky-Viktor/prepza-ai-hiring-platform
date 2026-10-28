import type { User } from "firebase/auth"

export type AuthState = {
  user: User | null
  loading: boolean
}
