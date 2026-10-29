# Actions on interviews, their questions and candidates (see actions.py for the entries' keys).

INTERVIEW_PAGE = "/companies/{company_id}/interviews/{interview_id}"
CANDIDATES_PAGE = INTERVIEW_PAGE + "?tab=candidates"
INTERVIEW_SUBJECT = {
    "service": "companies",
    "path": "/interviews/{interview_id}",
    "field": "title",
}
CANDIDATE_SUBJECT = {
    "service": "companies",
    "path": "/interviews/{interview_id}/candidates",
    "match": "invite_id",
    "field": "email",
}
INTERVIEW_FIELDS = ["id", "title", "status", "pass_mark", "question_seconds", "hired"]


def interview_action(method: str, path: str, description: str, **more) -> dict:
    """An action on one interview, its page the result opens."""
    params = ["interview_id", *more.pop("params", [])]

    return {
        "service": "companies",
        "method": method,
        "path": path,
        "params": params,
        "confirm": True,
        "description": description,
        "subject": INTERVIEW_SUBJECT,
        "render": "link",
        "link": INTERVIEW_PAGE,
        **more,
    }


INTERVIEW_ACTIONS = {
    "create_interview": {
        "service": "companies",
        "method": "POST",
        "path": "/interviews",
        "params": ["company_id"],
        "body": ["text", "generate_in"],
        "preview": ["text", "generate_in"],
        "confirm": True,
        "description": (
            "Create an interview from a job description (`text`, the user's own words or a "
            "description they pasted); `generate_in` is the language its questions are written "
            "in (the interface's when left out). prepza then proposes topics, which the user "
            "reviews before the questions are written."
        ),
        "fields": ["id", "generation_id", "title", "status"],
        "render": "link",
        "link": "/generate/{generation_id}?next=/companies/{company_id}/interviews/{id}",
    },
    "create_interview_from_template": {
        "service": "companies",
        "method": "POST",
        "path": "/interviews/from-template",
        "params": ["company_id"],
        "body": ["template_id"],
        "confirm": True,
        "description": "Create an interview from a ready-made template (search_templates).",
        "preview": [],
        "fields": INTERVIEW_FIELDS,
        "render": "link",
        "link": "/companies/{company_id}/interviews/{id}",
        "result_label": "title",
    },
    "delete_interview": interview_action(
        "DELETE",
        "/interviews/{interview_id}",
        "Delete an interview with its candidates' results. Can't be undone.",
        destructive=True,
        link="/companies/{company_id}/interviews",
    ),
    "rename_interview": interview_action(
        "PATCH", "/interviews/{interview_id}/title", "Rename an interview.", body=["title"]
    ),
    # One setting each, so a change can't carry values the user didn't ask for.
    "set_pass_mark": interview_action(
        "PATCH",
        "/interviews/{interview_id}/settings",
        "Set an interview's pass mark (%), the grade a candidate needs to pass.",
        body=["pass_mark"],
        required=["pass_mark"],
        fields=INTERVIEW_FIELDS,
    ),
    "set_question_seconds": interview_action(
        "PATCH",
        "/interviews/{interview_id}/settings",
        "Set an interview's average time per question, in seconds: each question gets its own "
        "time from its length and any code it shows, and the total stays the questions times "
        "this average.",
        body=["question_seconds"],
        required=["question_seconds"],
        fields=INTERVIEW_FIELDS,
    ),
    "mark_hired": interview_action(
        "PATCH",
        "/interviews/{interview_id}/settings",
        "Mark an interview as hired (someone was hired through it), or not.",
        body=["hired"],
        required=["hired"],
        fields=INTERVIEW_FIELDS,
    ),
    "keep_questions_private": interview_action(
        "PATCH",
        "/interviews/{interview_id}/settings",
        "Keep an interview's questions out of prepza's shared question bank, which other "
        "companies' interviews reuse questions from (true), or let them join it again (false). "
        "Questions already reused in other interviews stay there.",
        body=["keep_private"],
        required=["keep_private"],
        fields=[*INTERVIEW_FIELDS, "keep_private"],
    ),
    "set_interview_link": interview_action(
        "PUT",
        "/interviews/{interview_id}/link",
        "Turn the interview's shareable link (for a job ad) on or off.",
        body=["on"],
        link=CANDIDATES_PAGE,
        fields=["link_url"],
    ),
    "set_topic_limit": interview_action(
        "PUT",
        "/interviews/{interview_id}/topics/{topic_id}/limit",
        "Set how many questions of a topic each candidate gets; 0 leaves the topic out.",
        params=["topic_id"],
        body=["limit"],
    ),
    "regenerate_question": interview_action(
        "POST",
        "/interviews/{interview_id}/questions/{question_id}/regenerate",
        "Replace a question with a newly written one.",
        params=["question_id"],
    ),
    "mark_question_wrong": interview_action(
        "POST",
        "/interviews/{interview_id}/questions/{question_id}/wrong",
        "Mark a question as wrong, so candidates no longer get it.",
        params=["question_id"],
    ),
    "review_generation": interview_action(
        "POST",
        "/interviews/{interview_id}/generation/review",
        "Confirm the topics prepza proposed (get_generation), keeping the `selected` ones, "
        "optionally with changes described in `instructions`; then the questions are written.",
        body=["selected", "instructions"],
    ),
    "retry_generation": interview_action(
        "POST",
        "/interviews/{interview_id}/generation/retry",
        "Try again an interview whose generation failed.",
    ),
    "cancel_generation": interview_action(
        "POST",
        "/interviews/{interview_id}/generation/cancel",
        "Cancel an interview still being generated; it's removed.",
        destructive=True,
        link="/companies/{company_id}/interviews",
    ),
    "invite_candidate": interview_action(
        "POST",
        "/interviews/{interview_id}/candidates",
        "Invite one candidate to an interview by email, with their name when the user gave it (it "
        "costs credits once they answer).",
        body=["email", "name"],
        fields=["id", "email", "status"],
        link=CANDIDATES_PAGE,
    ),
    "invite_candidates": interview_action(
        "POST",
        "/interviews/{interview_id}/candidates/bulk",
        "Invite several candidates at once: `text` holds their emails, separated by commas, "
        "spaces or new lines.",
        body=["text"],
        fields=["invited", "skipped"],
        link=CANDIDATES_PAGE,
    ),
    "revoke_candidate": interview_action(
        "DELETE",
        "/interviews/{interview_id}/candidates/{invite_id}",
        "Revoke a candidate's invite that hasn't been used yet.",
        params=["invite_id"],
        subject=CANDIDATE_SUBJECT,
        destructive=True,
        link=CANDIDATES_PAGE,
    ),
    "rename_candidate": interview_action(
        "PATCH",
        "/interviews/{interview_id}/candidates/{invite_id}/name",
        "Correct a candidate's name (a blank one makes it not known).",
        params=["invite_id"],
        body=["name"],
        subject=CANDIDATE_SUBJECT,
        link=CANDIDATES_PAGE,
    ),
    "set_extra_time": interview_action(
        "PUT",
        "/interviews/{interview_id}/candidates/{invite_id}/extra-time",
        "Give a candidate extra time (a percentage, as an accommodation).",
        params=["invite_id"],
        body=["extra_time"],
        subject=CANDIDATE_SUBJECT,
        link=CANDIDATES_PAGE,
    ),
}
