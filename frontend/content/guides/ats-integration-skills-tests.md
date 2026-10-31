---
title: "How to connect skills tests to your ATS"
seoTitle: "How to Connect Skills Tests to Your ATS: A Practical Guide"
description: "Send skills tests and get results through your ATS automatically, keep people in charge of hiring decisions, and know what to check first."
updated: "2026-10-21"
---

# How to connect skills tests to your ATS

Most hiring teams keep candidates in an applicant tracking system (ATS) and run skills tests in another tool. Without a link between the two, someone copies emails out of the ATS, sends invites by hand, waits, then copies scores back. It works for five candidates. At fifty, invites go out late, results sit in a second tab nobody opens, and good applicants accept other offers while they wait.

This guide explains what a good connection between an ATS and a testing tool does, what to check before you rely on one, and how to set it up so that automation handles the busywork while people still make every hiring decision.

## Why connect them at all

| Without a connection | With a connection |
| --- | --- |
| Someone exports or copies candidate emails | Moving a candidate to a stage sends the invite |
| Invites go out when someone has time | Invites go out within minutes of the move |
| Results live in the testing tool | Results appear on the candidate in the ATS |
| Hiring managers ask "has anyone tested them?" | The ATS shows who was tested and how they did |
| Typos in emails and missed candidates | The ATS is the single list of who applied |

Speed matters more than it looks. The longer the gap between applying and hearing back, the more candidates drop out or take another job. Exact drop-off rates vary a lot by role and market, so treat published figures with care, but the direction is consistent: a slow process loses people, and the strongest applicants usually have the most options.

## What a good flow looks like

A sound integration follows the stages you already use. It doesn't invent a new process.

1. **A candidate applies** and lands in your ATS as usual.
2. **A person moves them to a testing stage,** for example "Skills test". That move is the trigger, so a human still decides who gets tested.
3. **The testing tool sends the invite** automatically, for the test linked to that job.
4. **The candidate takes the test** on their own time, within any deadline you set.
5. **Results are written back to the candidate in the ATS:** the score, whether they passed, any integrity flags and a link to the full answers.
6. **A person reviews the result** and moves the candidate on, or not.

Two things stay manual on purpose: choosing who gets tested and deciding what happens next. The connection only removes the copying in between.

### Why not trigger on every new application?

Some tools invite everyone who applies. That can be fine for high-volume roles where every applicant takes the same test. But a stage you move candidates into is easier to control: you can skip applicants who clearly fail a hard requirement (no work permit, wrong location), and you never test, or pay for, someone you were going to reject anyway.

## What to check before choosing an integration

Not every "integrates with your ATS" claim means the same thing. Ask these questions before you connect anything.

| Question | Why it matters | A good answer |
| --- | --- | --- |
| How do you connect? | Shared passwords and vendor-held accounts are hard to audit or revoke | An API key or token your company creates and can delete at any time |
| What can the key do? | A key with full access is a risk if it leaks | The narrowest permissions the integration needs, listed in the docs |
| What triggers an invite? | You need to know exactly when candidates get emailed | A specific stage you choose, per job |
| Where do results land? | Results nobody sees don't help | On the candidate's profile, as a note or comment your team already reads |
| What happens when an invite fails? | Out of credits, a typo, a paused account: candidates silently stuck | Someone is told, and the candidate can be invited again |
| Can an event be processed twice? | ATSs resend events; a candidate shouldn't get two invites | Each candidate is invited once per test, however often the event arrives |
| How are incoming events verified? | An unverified address can be sent fake events | Signed requests that the tool checks |
| How long is candidate data kept? | Privacy laws like the GDPR expect a clear retention period | A stated limit, and deletion when you delete the job, the test or your account |
| What does it cost? | Per-seat plans can make automation expensive | A cost you can predict per candidate tested |

If the vendor can't answer the failure and duplicate questions clearly, expect to find out the hard way.

### Data protection

Connecting two systems means candidate data, at least names and emails, moves between two companies. Under the GDPR and similar laws, your testing vendor is usually your data processor, so you need a data processing agreement and should tell candidates, in your privacy notice or the invite, that a skills test is part of the process. Keep the data you pass to the minimum the test needs. For more on the legal side of tests and AI in hiring, see [Is AI hiring legal in the EU?](/guides/is-ai-hiring-legal-in-the-eu)

## A setup checklist

Before you switch it on for a live role:

1. **Create a stage just for testing** in your ATS, such as "Skills test". Don't reuse a stage that means something else, or candidates get invited by accident.
2. **Create the key from an admin account** that can see every job you want to link, with only the permissions the docs list.
3. **Link each job to its test** and pick the stage that triggers the invite.
4. **Set up the web hook** if your ATS needs you to do it by hand, and paste its secret where the tool asks.
5. **Test with yourself.** Add a candidate with your own email, move them to the stage, take the test and check the note appears in the ATS.
6. **Decide who watches for failures:** who gets told when an invite can't be sent, and who fixes it.
7. **Agree how results are read.** A pass mark is a guide, not an automatic rejection. Decide that before results come in, not after.

## Common mistakes

- **Automating the decision, not the paperwork.** Auto-rejecting everyone below a score removes the human check that catches a bad question or a candidate who had a connection problem. Let the score sort; let a person decide.
- **Triggering from the wrong stage.** A stage that recruiters use for other reasons sends tests to people who shouldn't get them.
- **One test for every job.** The connection makes it easy to send the same test everywhere. A test helps most when it's built for the job in question. See [Skills tests vs CV screening](/guides/skills-tests-vs-cv-screening).
- **Nobody watching failures.** If an invite fails quietly, the candidate waits for an email that never comes, and you think they ignored it.
- **A key tied to someone who leaves.** Some ATS keys act as the person who made them. When that person's account is closed, the connection stops. Use an account that will stay, and reconnect when people change roles.
- **Forgetting candidates outside the ATS.** Referrals and direct applicants who never enter the ATS still need an invite. Keep a manual way to invite them too.

## How testee does it

testee connects to **Workable, Greenhouse, Teamtailor, Recruitee and Breezy HR**. It follows the flow above.

- **Your key, your control.** An owner or admin connects the ATS on the company's Integrations tab with a key your company creates in the ATS. testee checks it before saving, stores it encrypted and never shows it again. Disconnecting deletes the key and the linked jobs at once.
- **Link a job to an interview.** Pick an ATS job and the stage that triggers the invite, and link it to an existing testee interview or make a new one from the job's text in the ATS. You review the topics before any question is written.
- **Move a candidate, the invite goes out.** Each candidate is invited once per interview, even if the ATS sends the same event twice.
- **Results back in the ATS.** When a candidate finishes, testee adds a note or comment to them in the ATS with their grade, whether they passed, any integrity flags (leaving the page, copy attempts, answers picked too fast to have read the question) and a link to their scorecard with every answer.
- **Failures don't go unnoticed.** If a candidate can't be invited, for example because the company is out of credits, has hit an email limit, or because testee has paused invites for a while, every member of the company gets a notification naming the ATS. Candidates not invited for lack of credits are invited automatically after a top-up, and any job's waiting candidates can be invited again with one click.
- **Slack, if you use it.** testee can post notifications, such as a finished candidate or an ATS candidate who couldn't be invited, to a Slack channel you choose.
- **Your own platform.** If your ATS isn't on the list, testee's [API](/api-docs) lets you invite candidates with an API key and receive a signed web hook when a candidate starts, finishes, isn't reached, expires or is removed, and when an interview is ready.
- **Data kept for a set time.** Candidates saved from an ATS are deleted after 365 days, or earlier with their interview or company.

Some ATSs need a step on their side. Greenhouse, Teamtailor and Recruitee ask you to add a web hook by hand; testee's Instructions dialog shows the address and where to paste its secret. testee sets up Workable's and Breezy HR's web hooks itself.

Pricing is per candidate, with no subscription: you pay only for candidates who answer at least one question, $5 each on the $50 top-up, $4 from a $200 top-up, $3 from a $600 top-up and $2 from a $1,000 top-up. Prices are in US dollars here, and in the local currency in Canada, Australia, Israel, Poland, Switzerland, Japan, South Korea, Taiwan, Hong Kong, Thailand, Singapore, India, the rest of Europe and the UK; VAT or sales tax is handled at checkout. Connecting an ATS and making interviews is free, and your first company's first 3 candidates are free. See [pricing](/pricing).

## Related reading

- [How to screen 100 applicants in a day](/guides/screen-100-applicants-in-a-day)
- [Skills tests vs CV screening](/guides/skills-tests-vs-cv-screening)
- [Pre-employment testing: a practical guide](/pre-employment-testing)
