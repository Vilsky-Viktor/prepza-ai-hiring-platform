# How lists and actions narrow to one parent, for the panel's assistant and AI apps over MCP alike.
PARENTS_RULE = (
    "Things in prepza sit inside one another: a company has interviews, an interview has "
    "candidates. Never list, compare or act on things from different parents mixed together: "
    "candidates belong to one interview of one company, interviews to one company. When a list "
    "or an action needs a parent the user hasn't given, ask for it first, in one short question "
    'with the choices by name from your tools (for example "Which interview? Store Manager or '
    "Field Technician?\"); ask for the company first, then the interview. Don't ask when there's "
    "only one choice: use it and say which. For candidates that means two questions: which "
    "company, then which interview (list_interviews gives the choices); then list them with "
    'list_candidates, newest first (sort "date"). search_candidates only finds a person the user named, by name or email, '
    "never a list. Totals and how-to questions need no parent."
)
