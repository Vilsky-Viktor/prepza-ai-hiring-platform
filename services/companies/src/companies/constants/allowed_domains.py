# The sites a company lets embed its interviews with the SDK (the frame's frame-ancestors): its
# allowed domains, used for nothing else (the API and web hooks are limited by IP per key). A
# domain allows that host exactly; "*.acme.com" allows every subdomain of acme.com (not acme.com
# itself). Pages are on HTTPS, but on the developer's own computer (localhost), which a company
# allows only when it opts in: with the allow-localhost switch, or a localhost entry (with its
# port, or any port without one).
MAX_ALLOWED_DOMAINS = 20
MAX_DOMAIN_LENGTH = 260
# The longest page address the embedded frame passes on to be checked.
MAX_URL_LENGTH = 2000
# The loopback hosts a developer's own computer uses, as a page's origin names them.
LOOPBACK_HOSTS = ("localhost", "127.0.0.1", "[::1]")
# A refused entry, as the 422 names it.
NOT_A_DOMAIN = (
    "{entry} isn't a domain a page can be on: use a domain like jobs.acme.com, *.acme.com for its "
    "subdomains, or localhost:3000"
)
