from enum import StrEnum


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    # Sees everything and shares reports, but changes nothing and spends no credits.
    VIEWER = "viewer"


# The roles that change the company, its tests and candidates, and spend its credits.
EDITORS = (Role.OWNER, Role.ADMIN)

# Team invites email whoever the owner names, from prepza's domain: a company holds at most this
# many not yet accepted (MAX_PENDING_INVITES), and one that never topped up sends at most this
# many a day (MEMBER_INVITES_PER_UNPAID_DAY).
TOO_MANY_PENDING = "Too many invites waiting. Remove some, or wait for them to join."

# Making a member the company's owner (the owner becomes an admin then): only a member who joined
# as an admin, and not one who already owns as many companies as one person may.
ONLY_ADMINS_OWN = "Only an admin who has joined can become the owner."
OWNS_TOO_MANY = "They already own as many companies as one person may: {limit}."
ALREADY_INVITED = "That email is already invited"
