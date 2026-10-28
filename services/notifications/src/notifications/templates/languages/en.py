# Email texts in English. Values are filled in with str.format; the HTML version escapes them.

# The footer of reminders to a company's owners and admins.
MEMBER_FOOTER = (
    "This email was sent to {email} because you're an owner or admin of a company on prepza."
)

TEXTS = {
    "candidate": {
        "subject": "Interview invite from {company}",
        "preheader": "Take “{title}” on prepza. Sign in with {email} to start.",
        "heading": "Interview invitation",
        "lines": [
            "{company} invited you to the “{title}” interview on prepza.",
            (
                "Sign in with {email} to start. Only this address can take the "
                "interview, and you get one attempt."
            ),
        ],
        "button": "Open the invite",
    },
    "joined": {
        "subject": "Your link to “{title}”",
        "preheader": "If you leave the interview, continue with this link. Sign in with {email}.",
        "heading": "Your interview link",
        "lines": [
            "You started the “{title}” interview for {company} on prepza.",
            (
                "If you leave, continue with this link: sign in with {email}. It keeps working "
                "even if {company} takes down the link you started from. The clock keeps running "
                "while you're away."
            ),
        ],
        "button": "Continue the interview",
        "footer": (
            "This email was sent to {email} because you started an interview on prepza with this "
            "address."
        ),
    },
    "reminder": {
        "subject": "Reminder: your {company} interview",
        "preheader": "“{title}” is still open. Sign in with {email} to start.",
        "heading": "Your interview is waiting",
        "lines": [
            (
                "{company} invited you to the “{title}” interview on prepza a few days ago, and "
                "you haven't started it yet."
            ),
            (
                "Sign in with {email} to start. Only this address can take the interview, and "
                "you get one attempt. The invite expires 30 days after it was sent."
            ),
        ],
        "button": "Open the invite",
    },
    "member": {
        "subject": "Join {company} on prepza",
        "preheader": "Join {company} as {role}. Sign in with {email} to accept.",
        "heading": "Team invitation",
        "lines": [
            "{inviter} invited you to join {company} on prepza as {role}.",
            "Sign in with {email} to accept. Only this address can accept the invitation.",
        ],
        "button": "Open the invitation",
        # The role's name as the lines use it.
        "roles": {"admin": "an admin", "viewer": "a viewer"},
    },
    "report": {
        "subject": "Report: {candidate}",
        "preheader": "{candidate} took “{title}” at {company}. The report is attached.",
        "heading": "Candidate report",
        "lines": [
            "{sender} from {company} shared the report of {candidate} for the “{title}” interview.",
            (
                "It's attached as a one-page PDF: the overall grade, each topic's score and "
                "what the candidate's browser showed. Reply to this email to answer {sender}."
            ),
        ],
        "button": "Visit prepza",
        "footer": "This email was sent to {email} because {sender} shared a candidate report "
        "with this address on prepza. If you weren't expecting it, you can ignore it.",
    },
    "candidates": {
        "subject": "All candidates: {title}",
        "preheader": "Every candidate for “{title}” at {company}. The report is attached.",
        "heading": "Candidates report",
        "lines": [
            "{sender} from {company} shared the report of all candidates for the “{title}” interview.",
            (
                "It's attached as a PDF: each candidate's grade, progress and what their browser "
                "showed, best first. Reply to this email to answer {sender}."
            ),
        ],
        "button": "Visit prepza",
        "footer": "This email was sent to {email} because {sender} shared a candidates report "
        "with this address on prepza. If you weren't expecting it, you can ignore it.",
    },
    "digest": {
        "subject": "Your activity digest on prepza",
        "preheader": "What happened in your companies in the last 24 hours.",
        "heading": "Your activity digest",
        "lines": [
            "Here's what happened in your companies on prepza in the last 24 hours.",
        ],
        "rows": {
            "candidate_finished": "Candidates who finished: {count} · “{title}”",
            "invite_undelivered": "Undelivered invites: {count} · “{title}”",
            "ats_not_invited": "Candidates not invited from {ats}: {count}",
            "interview_ready": "Interview ready: “{title}”",
        },
        "button": "Open prepza",
        "footer": (
            "This email was sent to {email} because you're a member of a company on prepza "
            "and get its activity digest."
        ),
    },
    "low_credits": {
        "subject": "Your credits are running low",
        "preheader": "Top up to keep inviting candidates.",
        "heading": "Credits are running low",
        "lines": [
            (
                "These companies don't have enough credits to invite another candidate. Top"
                " up to keep inviting candidates."
            ),
        ],
        "rows": {
            "company": "{company} · credits available: {available}",
        },
        "button": "Top up",
        "footer": MEMBER_FOOTER,
    },
    "no_candidates": {
        "subject": "Waiting for candidates",
        "preheader": "Invite candidates by email, or share the interview's link.",
        "heading": "Waiting for candidates",
        "lines": [
            (
                "These interviews have been ready for a few days, but nobody has been "
                "invited yet. Invite candidates by email, or share the interview's link."
            ),
        ],
        "rows": {
            "interview": "“{title}” · {company}",
        },
        "button": "Invite candidates",
        "footer": MEMBER_FOOTER,
    },
    "review_waiting": {
        "subject": "Your topics are waiting for review",
        "preheader": "Confirm the topics, and the questions get generated.",
        "heading": "Review your topics",
        "lines": [
            (
                "The topics of the interviews you started are waiting for your review. Once"
                " you confirm them, the questions are generated. A review left open for 14 "
                "days is cancelled."
            ),
        ],
        "rows": {
            "interview": "{company} · days waiting: {days}",
        },
        "button": "Review your topics",
        "footer": MEMBER_FOOTER,
    },
    # Notices of a significant change to a legal document, sent at least 14 days before it
    # applies; service emails, whatever the email settings.
    "legal_terms": {
        "subject": "Terms update on {date}",
        "preheader": "The new terms apply from {date}.",
        "heading": "We're updating our terms",
        "lines": [
            "We've published a new version of prepza's terms. It applies from {date}; until then, the current terms apply.",
            "Using prepza after {date} means you accept the new terms. If you don't, you can delete your account in Settings before then.",
        ],
        "button": "Read the new terms",
        "footer": (
            "This email was sent to {email} because you have a prepza account. It's a notice"
            " about our terms, so it's sent whatever your email settings."
        ),
    },
    "legal_privacy": {
        "subject": "Privacy policy update on {date}",
        "preheader": "The new privacy policy applies from {date}.",
        "heading": "We're updating our privacy policy",
        "lines": [
            "We've published a new version of prepza's privacy policy, which says how we use your data. It applies from {date}; until then, the current one applies.",
            "You can download or delete your data in Settings at any time.",
        ],
        "button": "Read the new privacy policy",
        "footer": (
            "This email was sent to {email} because you have a prepza account. It's a notice"
            " about how we use your data, so it's sent whatever your email settings."
        ),
    },
    "legal_dpa": {
        "subject": "DPA update on {date}",
        "preheader": "The new agreement applies to your company from {date}.",
        "heading": "We're updating our data processing agreement",
        "lines": [
            "We've published a new version of the data processing agreement under which prepza processes your candidates' data. It applies from {date}; until then, the current one applies.",
            "A company that objects for reasonable data protection reasons can stop using prepza and delete its company before then.",
        ],
        "button": "Read the new agreement",
        "footer": (
            "This email was sent to {email} because you're an owner or admin of a company on"
            " prepza. It's a notice about our agreement with your company, so it's sent"
            " whatever your email settings."
        ),
    },
    # Campaigns (services/campaign_sends.py), named after the setting they need: a superadmin's
    # subject and text, and its button's text, or "open_site" when it has none.
    "updates": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "Open prepza",
        "footer": (
            "This email was sent to {email} because you chose to get product updates and news"
            " from prepza."
        ),
    },
    "promotions": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "Open prepza",
        "footer": (
            "This email was sent to {email} because you chose to get offers and promotions"
            " from prepza."
        ),
    },
    # An important notice: a service email about prepza itself (a security incident, planned
    # downtime, a change to how it works), whatever the email settings; never a promotion.
    "notices": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "Open prepza",
        "footer": (
            "This email was sent to {email} because you have a prepza account. It's an important"
            " notice about the service, such as its security or availability, so it's sent"
            " whatever your email settings."
        ),
    },
    "top_up_failed": {
        "subject": "Top-up failed: {company}",
        "preheader": "The card couldn't be charged. Top up to keep inviting candidates.",
        "heading": "Automatic top-up failed",
        "lines": [
            "Automatic top-up couldn't charge the card for {company}, so no credits were added.",
            "Top up to keep inviting candidates. Automatic top-up will try the card again later.",
        ],
        "button": "Top up",
        "footer": (
            "This email was sent to {email} because you're an owner or admin of {company} "
            "on prepza. It's about your company's billing, so it's sent whatever your email"
            " settings."
        ),
    },
    "top_up_paused": {
        "subject": "Top-up paused: {company}",
        "preheader": "The card was declined. Update it to turn automatic top-up back on.",
        "heading": "Automatic top-up is paused",
        "lines": [
            (
                "The card for {company}'s automatic top-up was declined, and trying it again "
                "won't help, so automatic top-up is paused and won't charge it."
            ),
            (
                "Update the card on the billing page to turn automatic top-up back on. Until "
                "then, top up by hand to keep inviting candidates."
            ),
        ],
        "button": "Update the card",
        "footer": (
            "This email was sent to {email} because you're an owner or admin of {company} "
            "on prepza. It's about your company's billing, so it's sent whatever your email"
            " settings."
        ),
    },
    "top_up_price_change": {
        "subject": "New top-up price for {company}",
        "preheader": "From {date}, each automatic top-up costs {new_price} instead of {price}.",
        "heading": "Automatic top-up's price changes",
        "lines": [
            (
                "From {date}, each automatic top-up for {company} costs {new_price} instead of "
                "{price}, plus VAT or sales tax where it applies. It buys the same candidates."
            ),
            (
                "Charges before then still cost {price}. If you'd like a different amount, "
                "change or turn off automatic top-up on the billing page before {date}."
            ),
        ],
        "button": "Open billing",
        "footer": (
            "This email was sent to {email} because you're an owner or admin of {company} "
            "on prepza. It's about your company's billing, so it's sent whatever your email"
            " settings."
        ),
    },
    "footer": "This email was sent to {email} because someone invited this address on prepza. If "
    "you weren't expecting it, you can ignore it.",
    # An invite from a company prepza hasn't verified, at the end of the footer.
    "unverified": "prepza hasn't verified {company}.",
    "paste_link": "Or paste this link into your browser",
    # The footer's links: optional emails' unsubscribe and settings, and a candidate's own.
    "unsubscribe": "Unsubscribe",
    "email_settings": "Change your email settings",
    "stop_reminders": "Don't send me reminders for this interview",
    "stop_company": "Don't email me for {company}",
    # Who runs prepza, at the end of every email.
    "operator": "prepza is run by {name}, {address}.",
}
