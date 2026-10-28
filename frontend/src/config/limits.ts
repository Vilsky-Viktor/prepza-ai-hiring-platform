// The longest text each field takes, as the services accept it (the service's constant is named
// after each). The services enforce these; the fields stop typing at the same point, so nothing
// is refused on sending.

// prepza_common MAX_GOAL_LENGTH: a learner's goal or a job description.
export const MAX_GOAL_LENGTH = 10000
// generation MAX_INSTRUCTIONS_LENGTH: changes described in words during topic review.
export const MAX_INSTRUCTIONS_LENGTH = 500
// generation MAX_TOPIC_NAME_LENGTH: a topic or subtopic edited during review.
export const MAX_TOPIC_NAME_LENGTH = 50
// prepza_common MAX_TITLE_LENGTH: a kit's or an interview's title.
export const MAX_TITLE_LENGTH = 70
// prepza_common MAX_CANDIDATE_NAME_LENGTH: a candidate's name.
export const MAX_CANDIDATE_NAME_LENGTH = 200
// companies MAX_COMPANY_NAME_LENGTH: a company's name.
export const MAX_COMPANY_NAME_LENGTH = 45
// companies MAX_DECLINE_REASON_LENGTH: why a superadmin declined a company's verification.
export const MAX_DECLINE_REASON_LENGTH = 500
// library MAX_REPORT_COMMENT_LENGTH: details of a question report.
export const MAX_REPORT_COMMENT_LENGTH = 1000
// The error page's problem report, sent to Sentry.
export const MAX_PROBLEM_REPORT_LENGTH = 2000
// assistant MAX_HELP_QUESTION_LENGTH: a question to the help chat.
export const MAX_HELP_QUESTION_LENGTH = 1000
// rounds MAX_CONTACT_NAME_LENGTH and MAX_CONTACT_MESSAGE_LENGTH: the contact form.
export const MAX_CONTACT_NAME_LENGTH = 100
export const MAX_CONTACT_MESSAGE_LENGTH = 5000
// A picker's search (languages, currencies): it only filters the list in the browser, and names
// are short.
export const MAX_PICKER_SEARCH_LENGTH = 50
// The longest email address there can be (RFC 5321); the services check every address.
export const MAX_EMAIL_LENGTH = 254
// companies MAX_SEARCH_LENGTH: a search through candidates' emails.
export const MAX_SEARCH_LENGTH = 254
// companies MAX_BULK_TEXT_LENGTH: a pasted list of candidate emails, in characters, and an
// uploaded one, in bytes (a larger file isn't read).
export const MAX_BULK_TEXT_LENGTH = 50000
// prepza_common MAX_NEWS_TITLE_LENGTH and MAX_NEWS_TEXT_LENGTH: a news post.
export const MAX_NEWS_TITLE_LENGTH = 120
export const MAX_NEWS_TEXT_LENGTH = 500
// prepza_common MAX_CAMPAIGN_SUBJECT_LENGTH, MAX_CAMPAIGN_TEXT_LENGTH and
// MAX_CAMPAIGN_BUTTON_LENGTH: a campaign email.
export const MAX_CAMPAIGN_SUBJECT_LENGTH = 120
export const MAX_CAMPAIGN_TEXT_LENGTH = 2000
export const MAX_CAMPAIGN_BUTTON_LENGTH = 40
// billing MAX_ADJUSTMENT_NOTE: the reason a superadmin gives for adjusting credits.
export const MAX_ADJUSTMENT_NOTE = 200
