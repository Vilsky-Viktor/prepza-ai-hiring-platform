import re
from urllib.parse import urlsplit

from publicsuffixlist import PublicSuffixList

from companies.constants.verification import FREE_EMAIL_DOMAINS, FREE_EMAIL_NAMES

DOMAIN = re.compile(r"^(?=.{1,253}$)([a-z0-9-]{1,63}\.)+[a-z]{2,63}$")
# The public suffix list bundled with the package (co.uk, github.io, ...); nothing is fetched.
SUFFIXES = PublicSuffixList()


def registrable_domain(host: str) -> str | None:
    """The domain one owner registered ("eng.acme.co.uk" is "acme.co.uk"), or None for a public
    suffix such as "co.uk" or "github.io"."""

    return SUFFIXES.privatesuffix(host.lower())


def website_domain(website: str) -> str | None:
    """The registrable domain of a website as typed ("https://www.Acme.com/jobs" is "acme.com"),
    or None when it isn't one."""
    text = website.strip().lower()
    host = urlsplit(text if "://" in text else f"https://{text}").hostname or ""
    host = host.removeprefix("www.")

    if not DOMAIN.match(host):
        return None

    return registrable_domain(host)


def is_free_domain(domain: str) -> bool:
    """True for a free mail service's domain, regional ones too (mail.yahoo.co.uk)."""
    registrable = registrable_domain(domain) or domain

    if registrable in FREE_EMAIL_DOMAINS:
        return True

    name = registrable.removesuffix(f".{SUFFIXES.publicsuffix(registrable)}")

    return name in FREE_EMAIL_NAMES


def email_on_domain(email: str, domain: str) -> bool:
    """True for an address whose registrable domain is the domain itself (ann@eu.acme.com is on
    acme.com, ann@ox.ac.uk isn't on ac.uk); a free mail address never is."""
    email_domain = email.rsplit("@", 1)[-1].lower()

    return registrable_domain(email_domain) == domain and not is_free_domain(email_domain)
