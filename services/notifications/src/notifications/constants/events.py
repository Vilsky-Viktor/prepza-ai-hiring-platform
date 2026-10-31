# A service asks for an in-app notification (testee_common.events.notifications).
from testee_common.events.notifications import NOTIFICATION_REQUESTED  # noqa: F401 (re-exported)

CANDIDATE_INVITED = "candidate.invited"
# Companies: someone started through a test's shareable link; they're emailed their own invite
# link, to continue if they leave. The same data as an invite.
CANDIDATE_JOINED = "candidate.joined"
# Companies: the owner invited a member; they're emailed the join link.
MEMBER_INVITED = "member.invited"
# A candidate who hasn't started, reminded once; the same data as the invite.
CANDIDATE_REMINDED = "candidate.reminded"
# A company member emails a candidate's PDF report; it carries the PDF, base64-encoded.
REPORT_SHARED = "report.shared"
# A visitor wrote through the contact page; it's emailed to testee's inbox.
CONTACT_SENT = "contact.sent"
# Companies: a company was deleted; its notifications go with it.
COMPANY_DELETED = "company.deleted"
# Companies: a company erased a candidate; its notifications about them go.
CANDIDATE_REMOVED = "candidate.removed"
# A company deleted an interview, its candidates with it: the notifications about them go.
CANDIDATE_INTERVIEW_DELETED = "candidate.interview_deleted"
# Its own: a Resend web hook received and verified, recorded by its delivery (svix-id); its work
# (suppression, telling companies and accounts) runs from this event, so the web hook is answered
# at once (notifications' `email` family, infra/terraform/pubsub.tf).
EMAIL_WEBHOOK = "email.webhook_received"
