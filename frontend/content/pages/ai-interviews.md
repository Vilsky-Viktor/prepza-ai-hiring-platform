---
title: "AI interviews: what they are and how to use them fairly"
seoTitle: "AI Interview Tools: Types, Risks and How to Use Them Fairly"
description: "What AI interview tools do: chatbots, video analysis and generated tests. How prepza's timed multiple-choice approach works, and the compliance basics."
updated: "2026-10-29"
---

# AI interviews: what they are and how to use them fairly

"AI interview" means very different things depending on the vendor. Some tools hold a conversation with the candidate. Some record video and score it. Some use AI only to write the questions, then score answers by fixed rules. For a hiring team, the difference matters: it changes what you can explain to a candidate, what can go wrong, and what the law expects from you.

This page sorts out the main kinds of AI interview tools, explains the approach prepza takes, and covers the compliance basics.

## Three kinds of AI interview tools

| Kind | What the AI does | What the candidate does | Main questions to ask |
| --- | --- | --- | --- |
| Chatbot or voice interviewer | Asks questions, follows up, and often scores the conversation | Talks or types answers in their own words | How are free-text answers scored? Can you see why someone got their score? |
| Video interview analysis | Records the candidate and may score speech, wording or delivery | Answers on camera | What exactly is analyzed? Is anything inferred from face, voice or emotion? |
| Generated tests | Writes the questions (and often the answer keys) from a job description | Answers questions under set conditions | Who checks the questions? How is an answer marked right or wrong? |

### Chatbot and voice interviewers

These tools feel closest to a real interview. A model asks questions, reacts to answers and produces a summary or a score. They can test communication and reasoning in a candidate's own words. The trade-off is explainability: when a model grades open answers, two similar answers can get different scores, and it can be hard to say exactly why.

### Video interview analysis

Here candidates record answers on camera. Some products only transcribe and let people watch; others score what the candidate said or how they said it. Analysis of faces, voices or emotions raises the most concerns. The EU AI Act bans AI systems that infer emotions in the workplace, except for medical or safety reasons ([Article 5(1)(f)](https://artificialintelligenceact.eu/article/5/)).

### Generated tests

In this model, AI does the writing work: it reads the job description, proposes what to test and drafts questions. Candidates then answer questions with clear right and wrong answers, and scoring follows fixed rules. This is the model prepza uses.

## prepza's approach

prepza uses AI to write a skills interview from your job description. People stay in control of what is tested and of every decision.

1. **AI reads your job description** and picks out what a candidate must know: the requirements, the level and a set of topics with subtopics.
2. **You review the topics.** Keep, uncheck, rename or edit them, or tell the AI in plain text what to change. No question is written until you approve.
3. **AI writes the questions.** Each topic gets a bank of multiple-choice questions with four options each: most have one correct option and three plausible wrong ones, and about 1 in 10 are "select all that apply", with 2 or 3 correct options. For technical topics, many questions show a short code example and ask what it outputs, what it does, why it fails or which change fixes it. You can open every question and its options, and re-generate any you don't like.
4. **Candidates answer timed questions.** Each candidate gets their own random set from each topic's bank, in their own order, with a countdown on every question.
5. **Answers are marked against an answer key.** AI writes the keys. A sample of each topic's keys is checked before release, and the rest when a question is flagged. Marking itself follows fixed rules, and no AI reads or judges a candidate's answer. If a key is corrected later, the fix applies to candidates who start after it; past results don't change. Speed, page leaves and copy attempts are shown to you as signals; they don't change the score.
6. **People decide.** You see a ranked list and a scorecard per candidate, with every answer and its timing. A person at your company reviews results and makes the hiring call.

What prepza does not do:

- No video, voice or face analysis.
- No personality or emotion inference.
- No automatic rejections. prepza doesn't reject candidates or send rejection messages; your team decides.
- Your data isn't used to train AI models. prepza's AI provider, OpenAI, doesn't train on API data under its terms.

### Questions improve over time

AI-written questions can be wrong or unclear, especially in a new interview. prepza watches for that: candidates' answers, ratings and reports flag weak questions, and an AI verifier fixes or replaces them. If you spot a question with a wrong answer key, mark it, and it goes to the verifier right away.

You can also preview your own interview as a candidate before inviting anyone: the same timed questions, free, and kept out of your results.

## Why this approach is easier to explain and review

**Every result can be traced.** A score is the share of points earned: each question is worth one point, and a "select all that apply" question earns part of it for each correct option ticked, and nothing if a wrong one is ticked. For any candidate you can show the exact questions they saw, what they picked, the right answer and how long they took.

**The content is reviewable.** You approve the topics before anything is written, and the questions are open to you. If a topic isn't a real job requirement, you can remove it.

**Everyone faces similar conditions.** Same topics, same number of questions per topic, same average time per question and the same total time. Each candidate's questions are drawn at random, so sets differ a little in difficulty. Candidates who need more time can get it: you can add extra time per candidate.

**Fewer irrelevant signals.** A multiple-choice answer doesn't carry an accent, a face, a background or a writing style, so the score doesn't depend on how someone looks or sounds. That doesn't rule out bias: knowledge tests can show score differences between groups, and a test in a candidate's second language can hold them back. Monitor results across groups.

**Sharing answers is harder.** With each candidate's own random set of questions and a timer on every question, sharing answers or looking things up takes more effort. The integrity signals help you decide where to look closer; they aren't proof of cheating.

None of this makes a test fair by default. The questions still need to match the job, the time limits need to suit the role, and people need to read results with care. A score is evidence, not a verdict. If you are weighing timed tests against other screening methods, read [Skills tests vs CV screening](/guides/skills-tests-vs-cv-screening).

### What multiple-choice can't do

Be clear about the limits. A multiple-choice test checks knowledge. Code-reading questions show whether someone understands code, not whether they can write it. A test like this doesn't show how someone writes, talks to a customer or designs a system end to end. For those, combine prepza with a work sample or a structured interview for your short list. For hands-on coding, use a developer platform or your own exercise alongside prepza; see [HackerRank alternatives](/compare/hackerrank-alternatives) and [Interviewing engineers in the age of AI](/guides/interviewing-in-the-age-of-ai).

## Compliance basics for AI interview tools

This is a summary as of October 2026, not legal advice. Check with your own counsel.

### EU AI Act

AI systems "intended to be used for the recruitment or selection of natural persons, in particular to place targeted job advertisements, to analyse and filter job applications, and to evaluate candidates" are high-risk under [Annex III, point 4(a)](https://artificialintelligenceact.eu/annex/3/) of the AI Act. Tools that score or rank candidates are very likely covered. prepza's own analysis concludes that prepza very likely is high-risk, with the obligations applying from 2 December 2027; a lawyer is to confirm.

High-risk status means duties on both sides:

- **The vendor (provider):** risk management, data governance, technical documentation, logging, instructions for use, human oversight by design, accuracy and security, a quality management system, conformity assessment and registration.
- **The employer (deployer):** use the tool as instructed, assign people to oversee it, keep the logs, and inform candidates and workers' representatives.

The dates and the details are in [Is AI hiring legal in the EU?](/guides/is-ai-hiring-legal-in-the-eu)

### GDPR

Interview results are personal data, under the EU GDPR and the UK GDPR alike. Expect a data processing agreement, a candidate notice, limited retention and a way for candidates to access or delete their data. [Article 22](https://gdpr-info.eu/art-22-gdpr/) also limits decisions based solely on automated processing that significantly affect people, so have a person review results before acting on them. prepza is hosted in the EU (some sub-processors are in the US; see the [privacy policy](/privacy)), deletes candidate data 12 months after the invite, and includes a data processing agreement and instructions for companies.

### United States

AI tools used in hiring fall under the same anti-discrimination rules as any selection method. Watch selection rates across groups (the four-fifths rule of thumb in [29 CFR 1607.4(D)](https://www.law.cornell.edu/cfr/text/29/1607.4)), offer accommodations, and check state and local rules. For example, New York City's [Local Law 144](https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page) requires a bias audit within one year before using an automated employment decision tool, a public summary of it, and notice to candidates. See [Pre-employment testing](/pre-employment-testing) for an overview.

## How to evaluate an AI interview tool

Ask each vendor:

- Which steps use AI, and which are fixed rules?
- Can I see and change what is tested before candidates start?
- How is each answer scored, and can I see the reasoning for any score?
- Is any face, voice or emotion analysis involved?
- What do candidates see before they start?
- Who makes the final decision, and how does the product support human review?
- What is the vendor's position on the EU AI Act, and what documents can they share?
