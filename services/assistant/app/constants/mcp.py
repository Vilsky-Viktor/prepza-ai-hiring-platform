# AI apps (Claude, ChatGPT, ...) connected over MCP: they call the assistant's tools as the user,
# with an access token prepza issued once the user allowed them (OAuth 2.1 with PKCE).

# The one scope an app is given: everything the user may do, as they would in the app.
MCP_SCOPE = "prepza"
# Where the MCP endpoint is, on the site (the resource the access is for), and where the user
# allows or denies an app (the frontend's page).
MCP_PATH = "/mcp"
# The request headers a browser-based app (MCP Inspector) may send to it: every protocol
# revision's, up to 2026-07-28's Mcp-Method and Mcp-Name, which its preflight must allow.
MCP_REQUEST_HEADERS = [
    "Authorization",
    "Content-Type",
    "Last-Event-ID",
    "Mcp-Method",
    "Mcp-Name",
    "Mcp-Protocol-Version",
    "Mcp-Session-Id",
]
CONNECT_PATH = "/connect"
AUTHORIZATION_METADATA_PATH = "/.well-known/oauth-authorization-server"
# Some apps look for the resource's metadata at the root, without the resource's path.
ROOT_RESOURCE_METADATA_PATH = "/.well-known/oauth-protected-resource"
# Apps registered without a secret (most do: Claude Code, MCP Inspector) are welcome too.
AUTH_METHODS = ["none", "client_secret_post", "client_secret_basic"]

# Tokens: this prefix and random bytes; only their hashes are kept.
TOKEN_PREFIX = "pzm_"
TOKEN_BYTES = 32
CODE_BYTES = 32
# How long each lasts: the access an hour, the refresh 90 days from its last use (each refresh
# makes new ones); a code 5 minutes, and a request waiting for the user 10.
ACCESS_SECONDS = 60 * 60
REFRESH_SECONDS = 90 * 24 * 60 * 60
CODE_SECONDS = 5 * 60
REQUEST_SECONDS = 10 * 60
# A replaced refresh token used again within this long is an app refreshing twice at once: just
# refused. Later, it was likely stolen, and the connection is revoked.
REFRESH_REUSE_GRACE_SECONDS = 60
# A connection's "last used" is written at most this often.
LAST_USED_EVERY_SECONDS = 60 * 60
# An app that registered but has had no connection for this many days is deleted.
IDLE_CLIENT_DAYS = 30
# An app may name itself by its Client ID Metadata Document instead of registering: its client_id
# is the document's HTTPS address (with a path), read when it first asks to connect, kept a day,
# then read again (the kept copy serves while the app's site doesn't answer). The read is bounded
# in time and in size (MAX_REGISTRATION_BYTES), and only public addresses are read (SSRF).
METADATA_DOCUMENT_SECONDS = 24 * 60 * 60
METADATA_DOCUMENT_TIMEOUT_SECONDS = 5
# Such an app has no secret: its document can't hold one.
METADATA_DOCUMENT_AUTH = "none"
# The longest app name kept from what an app says about itself.
MAX_CLIENT_NAME_LENGTH = 80

# Redis: a request waiting for the user, a code waiting to be exchanged, and the day an app was
# last counted as active for a user (the funnel's mcp_active, once a day).
REQUEST_KEY = "mcp:request:{request_id}"
CODE_KEY = "mcp:code:{code_hash}"
ACTIVE_KEY = "mcp:active:{user_id}:{client}"

# Apps known by the address they return to: the name the consent page shows, whatever the app
# says it's called. Any other address gets a warning there.
KNOWN_CLIENTS = {
    "claude.ai": "Claude",
    "claude.com": "Claude",
    "chatgpt.com": "ChatGPT",
    "chat.mistral.ai": "Le Chat",
    # VS Code on the web returns through vscode.dev/redirect.
    "vscode.dev": "VS Code",
}
# Desktop apps known by their own scheme (cursor://...), exactly these.
KNOWN_SCHEMES = {"cursor": "Cursor", "vscode": "VS Code"}
# An app on the user's own computer (Claude Code, Claude Desktop, MCP Inspector): its code never
# leaves that computer, so it's known too, named as it says.
LOOPBACK_HOSTS = ("localhost", "127.0.0.1", "[::1]", "::1")
LOCAL_APP = "Local app"
# What the funnel calls each app.
FUNNEL_CLIENTS = {
    "Claude": "claude",
    "ChatGPT": "chatgpt",
    "Le Chat": "le_chat",
    "Cursor": "cursor",
    "VS Code": "vscode",
}

# An AI agent on a server signs in with a company's API key instead (the api service's, which
# checks it): it acts as the key's maker, in the key's company only, if the key has the mcp
# permission (constants/key_tools.py lists the tools each permission allows).
API_KEY_PREFIX = "pz_"
KEY_MCP_PERMISSION = "mcp"
VERIFY_KEY_PATH = "/internal/keys/verify"
KEY_CLIENT_NAME = "API key"
KEY_FUNNEL_CLIENT = "api_key"
KEY_MISSING_PERMISSION = "This API key doesn't have the {permission} permission."
# The developer docs' list of the tools (routers/mcp_docs.py) is cached this long.
TOOLS_CACHE_SECONDS = 60 * 60

# A request to connect once it's answered or expired, and a connection that isn't the user's:
# the consent page and the connections list say what it means.
NOT_FOUND = "Not found"
# Where an app may never send the browser back to: these run or read something in the browser
# instead of opening an app. Other non-web schemes (cursor://) are desktop apps, named as unknown.
REFUSED_REDIRECT_SCHEMES = {"javascript", "data", "vbscript", "file"}
# The browser that asked to connect (its /authorize answer sets this cookie, with the request's
# id, for the consent page's calls only): only it can allow the request, so a consent link
# someone else started and sent can't connect their app to this account.
CONNECT_COOKIE = "prepza_connect"
CONNECT_COOKIE_PATH = "/api/assistant/connect"
# /authorize's answer to a request it can't take: a page, never a redirect (an app registers
# its own return address, so redirecting errors there would make /authorize an open redirect).
BAD_REQUEST = "This request to connect isn't valid. Start connecting again from your AI app."
OTHER_BROWSER = (
    "This request was started in another browser. Start connecting again from your AI app."
)

# Tools an app never gets: deleting the account or a company (with its paid credits) is done in
# the app only. The panel's own tools (show, sign_out) aren't tools of the registry at all.
MCP_EXCLUDED = frozenset({"delete_account", "delete_company"})
EXCLUDED_TOOL = (
    "This can only be done in prepza itself: deleting an account or a company can't be undone."
)
# Tools an app doesn't see at all: the bell names candidates of every company the user is in,
# past the companies that don't allow AI apps (companies refuses those on its own routes); a
# page's guide is about the page the user is on in prepza, and an app has none.
MCP_UNLISTED = frozenset({"list_notifications", "get_page_guide"})
# What an app reads when the connection's account is gone or disabled.
ACCOUNT_GONE = "This prepza account no longer exists or is disabled."
# The tool that changes the user's language: their kept sign-in is dropped after it, so the next
# calls answer in the new one.
UPDATE_LANGUAGE = "update_language"

# An AI app's Firebase ID token is kept until this long before Firebase says it expires, and
# at most MAX_KEEP_SECONDS, so an account disabled or deleted meanwhile loses its access within
# that on every instance: signing in again checks the account.
EXPIRY_MARGIN_SECONDS = 300
MAX_KEEP_SECONDS = 300
ID_TOKEN_CACHE_KEY = "mcp:id-token:{uid}"
# Firebase's sign-in API, where an AI app's calls get the user's ID token.
IDENTITY_TOOLKIT = "https://identitytoolkit.googleapis.com/v1"
# Its errors when it refuses for its own limits rather than for the token (they may be followed
# by " : <detail>").
FIREBASE_LIMIT_ERRORS = ("TOO_MANY_ATTEMPTS_TRY_LATER", "QUOTA_EXCEEDED", "RESOURCE_EXHAUSTED")
