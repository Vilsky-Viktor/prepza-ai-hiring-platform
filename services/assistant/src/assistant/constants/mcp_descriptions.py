# What an AI app reads about the tools whose descriptions in the in-app assistant are short (a
# route's summary): what the tool does, when to use it, and its key arguments. Only the MCP server
# uses these: the in-app assistant's evals measured worse with them (page context and general
# questions, 2026-10-21), so the panel keeps its own; an app has no page context to lean on.

MCP_DESCRIPTIONS = {
    "get_company": (
        "One company by company_id: its name, the user's role and what they may change, how "
        "many interviews it has, and its website and verification state (with the reason when "
        "verification was declined), and the domains allowed to embed its interviews with the "
        "SDK (verification only adds the badge). Use it for questions about a company's setup; "
        "list_companies gives the ids."
    ),
    "get_auto_top_up": (
        "A company's automatic top-up by company_id: whether it's offered and on, the pack it "
        "buys and the balance it tops up below. Use it when the user asks about automatic top-"
        "up; get_credits gives the balance itself."
    ),
    "list_members": (
        "A company's team by company_id: each member's email, role (owner, admin or viewer) and"
        " whether they've joined or are still invited, newest first, in pages (offset, limit). "
        "Use it for who is on the team and who can do what."
    ),
    "get_interview": (
        "One interview by interview_id: title, status, pass mark, average seconds per question, "
        "candidate count, whether someone was hired, its topics and subtopics, question count "
        "and limit, and the shareable link while it's on. Use it for an interview's settings "
        "and questions overview; its candidates come from list_candidates."
    ),
    "get_interview_report": (
        "An interview's results by interview_id: every candidate with status, progress, grade, "
        "whether they passed the pass mark, and integrity signals (tab leaves, copies, fast "
        "answers). Use it to compare, rank or summarise candidates of one interview; "
        "get_scorecard gives one candidate's results and the patterns in their answers."
    ),
    "list_topic_questions": (
        "The questions of one topic of an interview, by interview_id and topic_id (from "
        "get_interview): each question's text, options, the correct answer, whether it's select"
        " all that apply (multi), and candidates' likes, dislikes and reports. Use it to review"
        " or discuss an interview's questions."
    ),
    "get_email_preferences": (
        "Which emails the signed-in user gets from prepza, each on or off: a candidate "
        "finished, an invite undelivered, an ATS candidate not invited, an interview ready, "
        "reminders, product updates and promotions. It reads the current choices, which "
        "update_email_preferences changes, and answers what emails the user gets."
    ),
    "list_ats_stages": (
        "The stages of one job in a connected applicant tracking system, by provider, job_id "
        "(from list_ats_jobs) and company_id: each stage's id and name. Use it to pick the "
        "stage that sends candidates when linking a job with link_ats_job."
    ),
    "list_news": (
        "prepza's product news, newest first, in pages (offset, limit): each post's title, text"
        " and date. Use it when the user asks what's new in prepza itself, not about their "
        "candidates (that's get_updates)."
    ),
    "remove_company_logo": (
        "Removes a company's logo by company_id; candidates then see its name only. Use it only"
        " when the user asks to remove the logo."
    ),
    "remove_member": (
        "Removes a member, or withdraws a pending invitation, from a company's team by "
        "member_id (from list_members) and company_id; they lose access at once. Only the owner"
        " can, and never the owner. Use it only when the user names the person to remove."
    ),
    "rename_interview": (
        "Renames an interview by interview_id to the given title, which candidates and the team"
        " see. Use it only when the user gives the new name."
    ),
    "disconnect_slack": (
        "Disconnects Slack from a company by company_id: its Slack notifications stop. Use it "
        "only when the user asks to disconnect Slack."
    ),
    "remove_webhook": (
        "Removes one of a company's web hooks by webhook_id (from get_api_settings) and "
        "company_id: its endpoint gets no more events. Use it only when the user names the web "
        "hook to remove."
    ),
    "get_price_catalog": (
        "Today's prices in the user's currency: what a candidate costs, the credit packs on "
        "sale with their prices, the free candidates a new company gets and the referral bonus."
        " Use it for price and pack questions; get_credits gives a company's balance."
    ),
    "list_ats_links": (
        "A company's jobs linked to its applicant tracking systems, by company_id: each job, "
        "the stage that sends candidates, the interview they go to, and how many were invited, "
        "not invited (to retry) or are waiting. Use it to see which ATS jobs feed which "
        "interviews."
    ),
    "list_ats_jobs": (
        "The open jobs in one applicant tracking system the company connected, by provider and "
        "company_id. Use it to find a job to link (link_ats_job) or to read its description "
        "(get_ats_job_text)."
    ),
    "get_me": (
        "The signed-in user's own account: name, email, whether the email is verified, and "
        "their language. Use it for questions about their account, and for their name or "
        "language."
    ),
    "search_templates": (
        "Searches prepza's ready-made interview templates by words (q), level and languages, in"
        " pages (offset, limit): each template's id, title, level, language and topic count. "
        "Use it to find a template to start an interview from (create_interview_from_template);"
        " list_template_filters gives the levels and languages to filter by."
    ),
    "list_template_filters": (
        "The levels and languages the interview templates can be filtered by: the values "
        "search_templates takes when the user wants templates of a level or language."
    ),
    # The panel's names its `show` tool, which AI apps don't have.
    "get_guide": (
        "One guide article on hiring or on how prepza works, by its slug from list_guides, in "
        "the user's language: its title and full text. Answer from it and offer its link."
    ),
}
