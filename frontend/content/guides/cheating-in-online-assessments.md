---
title: "Cheating in online assessments, and what works against it"
seoTitle: "Cheating in Online Assessments: What Works Against It"
description: "How candidates cheat on online tests, why screen tricks and webcam proctoring fall short, and what works: tight timing, evidence for people, follow-ups."
updated: "2026-10-29"
---

# Cheating in online assessments, and what works against it

Any test a candidate takes at home, on their own device, can be gamed. That was true before AI assistants; now a phone can read a question off the screen and suggest an answer in seconds. Hiring teams respond in two ways: they try to lock the screen down and watch the candidate, or they design the process so that cheating gains little and shows up when it happens.

This guide covers what candidates actually do, why the first approach mostly fails, what works better, and where fairness and the law draw the line. It's written for hiring managers and recruiters running any kind of online test.

## What candidates actually do

There's little reliable data on how often candidates cheat on hiring tests, because people rarely admit it. Surveys give a lower bound: as Personnel Today reported, in a Gartner survey of 3,000 job candidates 6% admitted to interview fraud, such as posing as someone else or having someone pose as them; in another, of 3,290 candidates, 39% said they had used AI during the application process ([Personnel Today](https://www.personneltoday.com/hr/by-2028-one-in-four-candidate-profiles-will-be-fake), on [Gartner's July 2025 release](https://www.gartner.com/en/newsroom/press-releases/2025-07-31-gartner-survey-shows-just-26-percent-of-job-applicants-trust-ai-will-fairly-evaluate-them)). Not all AI use is cheating, but it shows how close at hand the tools are.

The common methods:

- **Relaying the question to an AI.** Copying the text into a chat, or, when copying is blocked, photographing the screen with a phone and asking an AI app. Current models read a photographed question as easily as typed text.
- **Looking answers up.** A search engine, notes, or documentation in another window.
- **A second person.** Someone sitting beside the candidate, or on a call, answering for them. In the extreme case, someone else takes the whole test. The FBI has warned of applicants for remote jobs using stolen identities and voice spoofing or deepfakes in online interviews ([FBI IC3, June 2022](https://www.ic3.gov/PSA/2022/PSA220628)).
- **Shared answers.** Candidates who took the test pass the questions and answers on, in a group chat or a leaked question bank.

Each of these needs time, or a test that's the same for everyone. That's where the useful defenses are.

## Why screen tricks fail: the analog hole

Whatever a person can read on a screen, a camera can read too. This is the "analog hole": once content is shown to a human, it can be recorded outside any software's control. A test page can block copy and paste, block right-click, or go full-screen. None of that stops a phone pointed at the monitor.

Researchers have tried to make screens readable to the eye but not to cameras, by splitting each image into rapidly alternating frames that the eye blends and a camera catches one at a time. The approach was built for video piracy, needed high refresh rates, and its own authors note that single captured frames can still be read ([Zhang et al., MobiCom 2015](https://old.sigmobile.org/mobicom/2015/papers/p372-zhangA.pdf)). A still photo with a slightly longer exposure, or a short video, blends the frames just as the eye does. On the 60 Hz screens most people use, the alternation becomes visible flicker, and flashing content carries a seizure risk that accessibility standards limit ([WCAG 2.2, Understanding 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html)).

Two lighter ideas fare no better:

- **Notices aimed at the AI** ("AI assistants must not answer this question") are easy to crop out or ignore, and models are trained to treat text in images as content, not instructions.
- **Watermarks** can help trace who leaked a question, but they don't stop anyone answering it.

At prepza we tried both on our own questions: AI models answered photographed questions with a watermark or a notice just as they did without one. So we stopped trying to defend the screen.

## What works better

### 1. Little time per question

Relaying a question takes time: pick up the phone, take the photo, wait for the answer, read it, pick the option. Someone who knows the material recognizes the right answer much faster. A countdown on each question, set to what a capable person needs to read and answer it, leaves knowledgeable candidates enough time and leaves little for a round trip to an AI or a friend.

The time should fit the question: a short question needs less, a question with a code example or a calculation needs more. One flat limit for every question is either too generous for the short ones or too tight for the long ones. [How to time a skills test](/guides/skills-test-timing-and-extra-time) covers the numbers, and how to give extra time fairly to candidates who need it.

### 2. A different test for each candidate

If everyone gets the same questions in the same order, answers spread. Draw each candidate's questions at random from a larger bank per topic, and shuffle the order of questions and options. A leaked set then covers only part of what the next candidate sees.

### 3. Evidence for a person to weigh, not automatic verdicts

The test page and the answers themselves leave traces that tell you where to look:

- **Leaving the page,** and how long for.
- **Copy attempts.**
- **Answers too fast to have read the question.**
- **Timing that doesn't follow the question.** People take longer on longer and harder questions; someone relaying every question to an AI tends to take about the same time on all of them. Testing research has long used response times to spot aberrant behavior ([van der Linden & Guo, 2008](https://doi.org/10.1007/s11336-007-9046-8)).
- **An unusual pattern of right and wrong answers.** Most people get easy questions right more often than hard ones. Hard ones right and easy ones wrong is unusual; "person-fit" statistics measure this ([Meijer & Sijtsma, 2001](https://doi.org/10.1177/01466210122031957)).

Each of these has innocent explanations. A notification steals focus; a nervous candidate answers a question too quickly; someone happens to know the hard topic and not the easy one. Treat a signal as a reason to look closer, never as proof, and never reject anyone on a signal alone. In the EU, the GDPR also gives people the right not to be subject to a decision based solely on automated processing where it significantly affects them ([Article 22](https://gdpr-info.eu/art-22-gdpr/)).

### 4. Follow-up questions in a live interview

The most reliable check is a conversation. An AI can answer a multiple-choice question; it can't sit a live interview for the candidate. For the topics where someone scored highest, or where a signal fired, ask two or three short questions about their answers: "Why is this option right and that one wrong?", "What would change if…?" Someone who knew the answer explains it easily. Someone who relayed it usually can't.

This also turns the test into what it should be: a screen that decides who gets a conversation, not the final decision. For how interviews themselves are changing, see [Interviewing in the age of AI](/guides/interviewing-in-the-age-of-ai).

### 5. Clear rules and an honesty pledge

Tell candidates up front what's allowed: no AI tools, no other people, no notes, or whatever your rules are. Then ask them to confirm it before they start.

Be realistic about what a pledge does. Studies of moral reminders and signed statements haven't held up well: a large replication of the "Ten Commandments" experiment found no effect on cheating ([Verschuere et al., 2018](https://doi.org/10.1177/2515245918781032)), and the authors of a well-known "sign at the top" study later found no effect when they repeated it ([Kristal et al., 2020](https://doi.org/10.1073/pnas.1911695117)). Research on universities does link honor codes, as part of a wider integrity culture, to less cheating ([McCabe, Treviño & Butterfield, 2001](https://doi.org/10.1207/S15327019EB1103_2)). A pledge's main value is clarity: nobody can say they didn't know the rules, and you have a record that they agreed to them.

## The limits of proctoring: fairness and the law

Webcam proctoring, screen recording and room scans promise to catch everything above. In hiring they bring problems of their own.

- **They exclude people.** Not every candidate has a webcam, a quiet room of their own or a stable connection. A requirement to show your home to an employer weighs most on people in shared or crowded housing.
- **They flag the wrong people.** Automated face detection doesn't work equally well for everyone. In a study of one widely used proctoring tool, women with the darkest skin tones were far more likely than other students to be flagged for review ([Yoder-Himes et al., 2022](https://doi.org/10.3389/feduc.2022.881449)).
- **They still miss the phone.** A camera sees what's in its frame; a phone held below the screen, or a person on the other side of the room, is outside it.

The law adds limits, especially in Europe:

- **GDPR.** Video of a candidate is personal data, and analysis of their face can be biometric data, which is specially protected ([Article 9](https://gdpr-info.eu/art-9-gdpr/)). In 2021 the Italian data protection authority fined Bocconi University over its remote exam proctoring, finding among other things that the facial analysis was biometric processing without a valid legal basis, that consent wasn't freely given given the imbalance between university and students, and that students weren't properly told about it ([Garante, decision 317 of 16 September 2021](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9703988)). The power imbalance between employer and candidate is, if anything, larger.
- **EU AI Act.** Since 2 February 2025, AI that infers people's emotions in the workplace is banned, with narrow medical and safety exceptions ([Article 5(1)(f)](https://artificialintelligenceact.eu/article/5/)), and the European Commission's guidelines read "workplace" as including recruitment ([Commission guidelines on prohibited AI practices](https://digital-strategy.ec.europa.eu/en/library/commission-publishes-guidelines-prohibited-artificial-intelligence-ai-practices-defined-ai-act)). Proctoring that judges "suspicious" behavior from video comes close to that line. AI used to evaluate candidates is also very likely high-risk, with duties such as human oversight. [Is AI hiring legal in the EU?](/guides/is-ai-hiring-legal-in-the-eu) explains the rules and their dates.
- **United States.** A federal court held in 2022 that a public university's webcam scan of a student's bedroom before an online exam violated the Fourth Amendment ([Ogletree v. Cleveland State University, as reported by Higher Ed Dive](https://www.highereddive.com/news/test-proctoring-room-scans-violated-college-students-privacy-judge-rules/630340/)). Private employers aren't bound by the Fourth Amendment, but state laws on biometrics, such as Illinois's Biometric Information Privacy Act, set their own rules for face data.

**This section is practical guidance, not legal advice.** Check your own obligations where you hire.

None of this means you can't verify anything. It means the checks with the best balance are the ones that use what the test already sees, leave the decision to a person, and move identity and depth checks into a live conversation.

## A setup that works

1. **Tell candidates the rules** in the invite and before they start, and ask them to confirm.
2. **Give each candidate their own random questions** from a bank per topic.
3. **Time every question** to what a capable person needs, and offer extra time to anyone who asks for it.
4. **Read the signals as pointers,** next to the answers themselves.
5. **Ask follow-up questions** about the test in the first live interview, especially where a signal fired.
6. **Let a person decide,** and write down why.

## How prepza handles it

prepza runs timed multiple-choice skills tests built from a job description. Here's what it does about cheating today:

- **Each candidate gets their own questions:** a random set from each topic's question bank, in their own order, with the options shuffled.
- **Every question has its own countdown,** fitted to its length: its words, any code or example, and time to work out the answer. The server keeps the clock, so reloading the page doesn't stop it.
- **The scorecard flags** answers too fast to have read the question, times the candidate left the page (a leave counts from 2 seconds, so a passing notification doesn't), and copy attempts. Any of them flags the candidate, and the scorecard and PDF report say plainly that a flag is a reason to look closer, not proof.
- **Answer patterns, once a candidate finishes.** The candidate's report points out answer times that stay about the same on every question, whatever its length and difficulty, and hard questions right while easy ones were wrong, with the counts behind it ("9 of 10 hard questions right, 4 of 8 easy ones wrong"). The second needs enough answers from other candidates to know how hard each question is. Both thresholds were set on a test with simulated candidates so that at most 1% of honest ones are flagged; they caught about a third of those relaying every question to an AI. The report notes that such patterns can have innocent causes.
- **Questions for the live interview.** Every finished candidate's page suggests up to 3 questions they got right, from their strongest topics, to talk through in the next conversation, starting with the hard questions behind a pattern when there is one.
- **Candidates pledge** to answer on their own, without AI tools or other people, before they can start, and the scorecard shows when they did.
- **No camera, microphone or screen recording.** prepza uses only what the test page itself sees: answers, times, page leaves and copy attempts.
- **People decide.** Nothing rejects a candidate automatically.

## Related reading

- [How to time a skills test](/guides/skills-test-timing-and-extra-time)
- [Interviewing in the age of AI](/guides/interviewing-in-the-age-of-ai)
- [Is AI hiring legal in the EU?](/guides/is-ai-hiring-legal-in-the-eu)
- [How to screen 100 applicants in a day](/guides/screen-100-applicants-in-a-day)

## Sources

- Gartner, [Gartner survey shows just 26% of job applicants trust AI will fairly evaluate them](https://www.gartner.com/en/newsroom/press-releases/2025-07-31-gartner-survey-shows-just-26-percent-of-job-applicants-trust-ai-will-fairly-evaluate-them), 31 July 2025; figures as reported by [Personnel Today](https://www.personneltoday.com/hr/by-2028-one-in-four-candidate-profiles-will-be-fake).
- FBI Internet Crime Complaint Center, [Deepfakes and stolen PII utilized to apply for remote work positions](https://www.ic3.gov/PSA/2022/PSA220628), 28 June 2022.
- Zhang, L., et al. (2015). Kaleido: You can watch it but cannot record it. *MobiCom 2015*. [PDF](https://old.sigmobile.org/mobicom/2015/papers/p372-zhangA.pdf)
- W3C, [Understanding Success Criterion 2.3.1: Three Flashes or Below Threshold](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html), WCAG 2.2.
- van der Linden, W. J., & Guo, F. (2008). Bayesian procedures for identifying aberrant response-time patterns in adaptive testing. *Psychometrika, 73*(3), 365–384. [doi:10.1007/s11336-007-9046-8](https://doi.org/10.1007/s11336-007-9046-8)
- Meijer, R. R., & Sijtsma, K. (2001). Methodology review: Evaluating person fit. *Applied Psychological Measurement, 25*(2), 107–135. [doi:10.1177/01466210122031957](https://doi.org/10.1177/01466210122031957)
- Verschuere, B., et al. (2018). Registered replication report on Mazar, Amir, and Ariely (2008). *Advances in Methods and Practices in Psychological Science, 1*(3), 299–317. [doi:10.1177/2515245918781032](https://doi.org/10.1177/2515245918781032)
- Kristal, A. S., Whillans, A. V., Bazerman, M. H., Gino, F., Shu, L. L., Mazar, N., & Ariely, D. (2020). Signing at the beginning versus at the end does not decrease dishonesty. *PNAS, 117*(13), 7103–7107. [doi:10.1073/pnas.1911695117](https://doi.org/10.1073/pnas.1911695117)
- McCabe, D. L., Treviño, L. K., & Butterfield, K. D. (2001). Cheating in academic institutions: A decade of research. *Ethics & Behavior, 11*(3), 219–232. [doi:10.1207/S15327019EB1103_2](https://doi.org/10.1207/S15327019EB1103_2)
- Yoder-Himes, D. R., et al. (2022). Racial, skin tone, and sex disparities in automated proctoring software. *Frontiers in Education, 7*. [doi:10.3389/feduc.2022.881449](https://doi.org/10.3389/feduc.2022.881449)
- Garante per la protezione dei dati personali, [decision no. 317 of 16 September 2021](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9703988) (Università Bocconi).
- Regulation (EU) 2024/1689 (AI Act), [Article 5](https://artificialintelligenceact.eu/article/5/); European Commission, [Guidelines on prohibited AI practices](https://digital-strategy.ec.europa.eu/en/library/commission-publishes-guidelines-prohibited-artificial-intelligence-ai-practices-defined-ai-act), 4 February 2025.
- GDPR, [Article 9](https://gdpr-info.eu/art-9-gdpr/) and [Article 22](https://gdpr-info.eu/art-22-gdpr/).
- Higher Ed Dive, [Test proctoring room scans violated college student's privacy, judge rules](https://www.highereddive.com/news/test-proctoring-room-scans-violated-college-students-privacy-judge-rules/630340/), August 2022 (Ogletree v. Cleveland State University, N.D. Ohio).
