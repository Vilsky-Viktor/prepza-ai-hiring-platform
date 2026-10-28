# The action that makes a company: the user's companies are read again after it.
CREATE_COMPANY = "create_company"

# Actions on companies, their team and verification (see actions.py for the entries' keys).

COMPANY_PAGE = "/companies/{company_id}/interviews"
MEMBERS_PAGE = "/companies/{company_id}/members"
COMPANY_SUBJECT = {"service": "companies", "path": "/companies/{company_id}", "field": "name"}
MEMBER_SUBJECT = {
    "service": "companies",
    "path": "/members",
    "query": ["company_id"],
    "match": "member_id",
    "field": "email",
}

COMPANY_ACTIONS = {
    CREATE_COMPANY: {
        "service": "companies",
        "method": "POST",
        "path": "/companies",
        "params": [],
        "body": ["name"],
        "confirm": True,
        "description": (
            "Create a company the user will own; needs only its name. When the user gave no "
            "name, ask for it instead of calling this."
        ),
        "fields": ["id", "name", "role"],
        "render": "link",
        "link": "/companies/{id}/interviews",
        "result_label": "name",
    },
    "rename_company": {
        "service": "companies",
        "method": "PATCH",
        "path": "/companies/{company_id}/name",
        "params": ["company_id"],
        "body": ["title"],
        "confirm": True,
        "description": "Rename a company (its new name is `title`).",
        "subject": COMPANY_SUBJECT,
        "fields": ["id", "name"],
        "render": "link",
        "link": COMPANY_PAGE,
        "result_label": "name",
    },
    "delete_company": {
        "service": "companies",
        "method": "DELETE",
        "path": "/companies/{company_id}",
        "params": ["company_id"],
        "confirm": True,
        "destructive": True,
        "description": (
            "Delete a company the user owns, with its interviews, candidates' results and "
            "credits. Can't be undone."
        ),
        "subject": COMPANY_SUBJECT,
        # Its credits are lost with it: the card says how many.
        "credits": True,
        "render": "link",
        "link": "/companies",
    },
    "set_company_website": {
        "service": "companies",
        "method": "PUT",
        "path": "/companies/{company_id}/website",
        "params": ["company_id"],
        "body": ["website"],
        "confirm": True,
        "description": (
            "Set the company's website (like acme.com), which starts its verification: prepza "
            "checks it against the email domains of its owner and admins."
        ),
        "subject": COMPANY_SUBJECT,
        "fields": ["website_domain", "verified_domain", "verification_status", "decline_reason"],
        "render": "link",
        "link": COMPANY_PAGE,
    },
    "remove_company_logo": {
        "service": "companies",
        "method": "DELETE",
        "path": "/companies/{company_id}/logo",
        "params": ["company_id"],
        "confirm": True,
        "description": "Remove the company's logo.",
        "subject": COMPANY_SUBJECT,
        "render": "link",
        "link": COMPANY_PAGE,
    },
    "turn_off_auto_top_up": {
        "service": "billing",
        "method": "DELETE",
        "path": "/companies/{company_id}/auto-top-up",
        "params": ["company_id"],
        "confirm": True,
        "description": "Turn off the company's automatic top-up.",
        "subject": COMPANY_SUBJECT,
        "done_when": {
            "service": "billing",
            "path": "/companies/{company_id}/auto-top-up",
            "field": "on",
            "value": False,
        },
        "render": "link",
        "link": "/top-up",
    },
    "invite_member": {
        "service": "companies",
        "method": "POST",
        "path": "/members",
        "params": ["company_id"],
        "body": ["email", "role"],
        "confirm": True,
        "description": "Invite someone to the company's team by email, as an admin or a viewer.",
        "subject": COMPANY_SUBJECT,
        "fields": ["id", "email", "role", "joined"],
        "render": "link",
        "link": MEMBERS_PAGE,
    },
    "change_member_role": {
        "service": "companies",
        "method": "PUT",
        "path": "/members/{member_id}/role",
        "params": ["member_id", "company_id"],
        "body": ["role"],
        "confirm": True,
        "description": "Change a team member's role to admin or viewer.",
        "subject": MEMBER_SUBJECT,
        "fields": ["id", "email", "role"],
        "render": "link",
        "link": MEMBERS_PAGE,
    },
    "remove_member": {
        "service": "companies",
        "method": "DELETE",
        "path": "/members/{member_id}",
        "params": ["member_id", "company_id"],
        "confirm": True,
        "destructive": True,
        "description": "Remove someone from the company's team.",
        "subject": MEMBER_SUBJECT,
        "render": "link",
        "link": MEMBERS_PAGE,
    },
}
