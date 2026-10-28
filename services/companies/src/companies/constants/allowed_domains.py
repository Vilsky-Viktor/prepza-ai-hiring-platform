# The sites a company lets embed its interviews (the SDK's frame) and send candidates back to
# (the API's return_url): its allowed domains. A domain allows that host exactly; "*.acme.com"
# allows every subdomain of acme.com (not acme.com itself). Pages are on HTTPS, but on the
# developer's own computer (localhost), which a company allows only when it opts in: with the
# allow-localhost switch, or a localhost entry (with its port, or any port without one).
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
# What a company's API page says while the return address isn't on an allowed domain.
RETURN_URL_OFF_DOMAIN = (
    "return_url must be an https address on one of the company's allowed domains; add the domain "
    "on its API page in prepza first."
)
