# Actions on the user's account, notifications, integrations and practice (see actions.py for
# the entries' keys). Left out on purpose: connecting an ATS and saving its web hook key or
# creating an API key (secrets, which don't belong in a chat), setting a logo or emailing a
# report (files the browser makes), turning on auto top-up (it charges), and links with tokens.

INTEGRATIONS_PAGE = "/companies/{company_id}/integrations"
API_PAGE = INTEGRATIONS_PAGE + "/api"


def company_action(service: str, method: str, path: str, description: str, **more) -> dict:
    """An action on one company's integration."""
    params = [*more.pop("params", []), "company_id"]

    return {
        "service": service,
        "method": method,
        "path": path,
        "params": params,
        "confirm": True,
        "description": description,
        "render": "link",
        "link": INTEGRATIONS_PAGE,
        **more,
    }


ACCOUNT_ACTIONS = {
    "update_language": {
        "service": "library",
        "method": "PUT",
        "path": "/me/settings",
        "params": [],
        "body": ["language"],
        "confirm": True,
        "description": "Set the language of the user's emails and interface.",
        "render": "link",
        "link": "/settings",
    },
    "update_email_preferences": {
        "service": "library",
        "method": "PUT",
        "path": "/me/email-preferences",
        "params": [],
        "body": ["changes", "source"],
        "preview": ["changes"],
        "confirm": True,
        "description": (
            "Turn optional emails on or off (get_email_preferences lists them): `changes` maps "
            'each to true or false; `source` is "settings".'
        ),
        "render": "link",
        "link": "/settings",
    },
    "delete_account": {
        "service": "library",
        "method": "DELETE",
        "path": "/me",
        "params": [],
        "confirm": True,
        "destructive": True,
        "description": (
            "Delete the user's account and all their data, with the companies they alone own. "
            "Refused while they own a company others joined: another member is made its owner "
            "first (on its Team page), or the company deleted. Can't be undone."
        ),
    },
    "mark_notifications_seen": {
        "service": "notifications",
        "method": "POST",
        "path": "/me/seen",
        "params": [],
        "confirm": True,
        "description": "Mark all of the user's notifications as seen.",
    },
    "set_slack_kinds": company_action(
        "notifications",
        "PUT",
        "/slack/kinds",
        "Choose which notifications the company's Slack channel gets (get_slack lists them).",
        body=["kinds"],
        link=INTEGRATIONS_PAGE + "/slack",
    ),
    "disconnect_slack": company_action(
        "notifications",
        "DELETE",
        "/slack",
        "Disconnect the company's Slack.",
        destructive=True,
        link=INTEGRATIONS_PAGE + "/slack",
    ),
    "disconnect_ats": company_action(
        "ats",
        "DELETE",
        "/{provider}",
        "Disconnect the company's applicant tracking system, with its linked jobs.",
        params=["provider"],
        preview=["provider"],
        destructive=True,
    ),
    "link_ats_job": company_action(
        "ats",
        "POST",
        "/links",
        "Link a job of the company's ATS (list_ats_jobs) and its stage (list_ats_stages) to an "
        "interview: candidates reaching that stage are invited to it.",
        body=["provider", "job_id", "stage_id", "interview_id"],
        preview=["provider"],
        subject={
            "service": "companies",
            "path": "/interviews/{interview_id}",
            "field": "title",
        },
    ),
    "unlink_ats_job": company_action(
        "ats",
        "DELETE",
        "/links/{link_id}",
        "Remove the link between an ATS job and an interview.",
        params=["link_id"],
        destructive=True,
    ),
    "retry_ats_candidates": company_action(
        "ats",
        "POST",
        "/links/{link_id}/retry",
        "Invite again the candidates of a linked ATS job whose invites didn't go out.",
        params=["link_id"],
    ),
    "create_webhook": company_action(
        "api",
        "POST",
        "/manage/webhooks",
        "Add a web hook: prepza posts candidates' results to this address.",
        body=["url"],
        fields=["id", "url"],
        link=API_PAGE,
    ),
    "remove_webhook": company_action(
        "api",
        "DELETE",
        "/manage/webhooks/{webhook_id}",
        "Remove a web hook.",
        params=["webhook_id"],
        destructive=True,
        link=API_PAGE,
    ),
    "remove_api_key": company_action(
        "api",
        "DELETE",
        "/manage/keys/{key_id}",
        "Remove an API key: whatever uses it stops working.",
        params=["key_id"],
        destructive=True,
        link=API_PAGE,
    ),
    "start_practice": {
        "service": "rounds",
        "method": "POST",
        "path": "/practice/{template_id}",
        "params": ["template_id"],
        "confirm": True,
        "description": "Start a free practice round of a template (the user practises it).",
        "preview": [],
        "fields": ["session_id"],
        "render": "link",
        "link": "/sessions/{session_id}",
    },
}
