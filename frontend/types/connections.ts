// An AI app asking to use the user's account, on the consent page; unknown apps are flagged by
// the API.
export type ConnectRequest = {
  client_name: string
  redirect_host: string
  known_client: boolean
  // The app asked only to read: no choice to offer.
  read_only: boolean
}

// Where the AI app goes back to after Allow or Deny.
export type ConnectAnswer = { redirect_url: string }

// An AI app the user connected to their account.
export type AiConnection = {
  id: string
  client_name: string
  redirect_host: string
  created_at: string
  last_used_at: string | null
}
