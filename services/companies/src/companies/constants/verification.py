from enum import StrEnum

# Mail services anyone can sign up to: an address there says nothing about a company. Matched
# against an address's registrable domain (mail.yahoo.co.uk is yahoo.co.uk).
FREE_EMAIL_DOMAINS = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "msn.com",
        "ymail.com",
        "rocketmail.com",
        "icloud.com",
        "me.com",
        "mac.com",
        "proton.me",
        "protonmail.com",
        "protonmail.ch",
        "pm.me",
        "web.de",
        "t-online.de",
        "freenet.de",
        "mail.com",
        "email.com",
        "zoho.com",
        "zohomail.com",
        "mail.ru",
        "inbox.ru",
        "list.ru",
        "bk.ru",
        "rambler.ru",
        "ya.ru",
        "ukr.net",
        "i.ua",
        "seznam.cz",
        "wp.pl",
        "o2.pl",
        "interia.pl",
        "onet.pl",
        "libero.it",
        "virgilio.it",
        "orange.fr",
        "free.fr",
        "laposte.net",
        "sfr.fr",
        "wanadoo.fr",
        "btinternet.com",
        "sky.com",
        "comcast.net",
        "att.net",
        "verizon.net",
        "qq.com",
        "foxmail.com",
        "163.com",
        "126.com",
        "yeah.net",
        "sina.com",
        "sohu.com",
        "aliyun.com",
        "naver.com",
        "daum.net",
        "hanmail.net",
        "rediffmail.com",
        "uol.com.br",
        "bol.com.br",
        "terra.com.br",
        "fastmail.com",
        "fastmail.fm",
        "tutanota.com",
        "tuta.io",
        "hey.com",
        "mailbox.org",
        "posteo.de",
        "gmx.at",
        "gmx.ch",
    }
)
# Free mail services with an address in many countries (yahoo.co.uk, hotmail.fr, gmx.de): matched
# by the registrable domain's name before its public suffix.
FREE_EMAIL_NAMES = frozenset(
    {"yahoo", "hotmail", "outlook", "live", "windowslive", "aol", "gmx", "yandex", "gmail"}
)
MAX_WEBSITE_LENGTH = 253
NOT_A_WEBSITE = "Enter the company's website, like acme.com"
FREE_DOMAIN = "That's a free mail service, not a company's website."


class VerificationStatus(StrEnum):
    """Where a company's verification stands. A work email on the website's domain is the
    proof; a superadmin then approves or declines it, and only approved shows the badge."""

    NONE = "none"
    WAITING_EMAIL = "waiting_email"
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"


# A rename takes the badge away until a superadmin reviews the new name.
# Re-saving the same website changes nothing for these: a declined company goes for review
# again only after its name or website changes.
REVIEWED = (VerificationStatus.PENDING, VerificationStatus.APPROVED, VerificationStatus.DECLINED)
# A rename sends these back for review.
RENAME_REVIEWED = (VerificationStatus.PENDING, VerificationStatus.APPROVED)
MAX_DECLINE_REASON_LENGTH = 500
REQUEST_CHANGED = "This request changed; check it again."
