---
title: "Interviewing engineers in the age of AI: what to test now"
seoTitle: "Interviewing in the Age of AI: What to Test Now"
description: "AI assistants are part of everyday engineering work. How that changes what interviews should test, how companies adapt, and where knowledge tests fit."
updated: "2026-10-29"
---

# Interviewing engineers in the age of AI: what to test now

For years, the classic technical interview asked a candidate to write code from scratch: reverse a list, implement a cache, solve a puzzle on a whiteboard or in a shared editor. The idea was simple. If someone can write the code, they can probably do the job.

AI coding assistants have weakened that link. Many routine pieces of code can now be drafted by an assistant in seconds, both at work and, unless you prevent it, during a remote interview. That doesn't make engineering skill less important. It changes which skills matter most, and so it changes what an interview should check.

This guide reviews what has changed, how some companies are adapting, and how to design an interview process that still tells you who can do the job. It's written for hiring managers and engineering leads.

## What has changed

AI assistants are now part of many developers' everyday work. In the 2025 Stack Overflow Developer Survey, 84% of respondents said they use or plan to use AI tools in their development process, and 51% of professional developers said they use them daily ([Stack Overflow, 2025](https://survey.stackoverflow.co/2025/ai)). GitHub's Octoverse 2025 report says that 80% of new developers on GitHub use Copilot in their first week ([GitHub, October 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/)).

The same survey shows the limits. More respondents distrusted the accuracy of AI output (about 46%) than trusted it (about 33%). The most common frustration, named by 66%, was "AI solutions that are almost right, but not quite", and 45% said debugging AI-generated code takes more time ([Stack Overflow, 2025](https://survey.stackoverflow.co/2025/ai)).

Put together, these numbers describe a shift in the work itself. Producing a first draft of code is getting cheaper. Judging whether that draft is right, and fixing it when it isn't, is where much of the skill now lies.

## How companies are adapting

There is no single industry answer yet. Reported approaches go in different directions:

- **Allowing or requiring AI in the interview.** In June 2025, Canva said it now expects backend, machine learning and frontend candidates to use AI tools such as Copilot, Cursor and Claude in a new "AI-Assisted Coding" round. It assesses whether candidates can "break down complex, ambiguous requirements", "identify and fix issues in AI-generated code" and "ensure AI-generated solutions meet production standards" ([Canva Engineering, June 2025](https://canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews)).
- **Piloting AI-assisted coding rounds.** In July 2025, Business Today, citing 404 Media, reported that Meta was building a coding interview in which candidates have an AI assistant. It quoted Meta saying this is "more representative of the developer environment that our future employees will work in, and also makes LLM-based cheating less effective" ([Business Today, July 2025](https://www.businesstoday.in/amp/technology/news/story/meta-to-test-job-applicants-with-ai-assisted-coding-interviews-amid-ai-expansion-plans-487200-2025-07-31)).
- **Restricting tools and meeting in person.** In March 2025, CNBC reported on a tool built to help candidates use AI unnoticed in remote coding interviews. In the same report, Amazon said candidates must acknowledge they won't use unauthorized tools, Google's CEO suggested hiring managers consider some in-person interviews, and Deloitte had brought back in-person interviews for its UK graduate program ([CNBC via NBC New York, March 2025](https://www.nbcnewyork.com/news/business/money-report/meet-the-21-year-old-helping-coders-use-ai-to-cheat-in-google-and-other-tech-job-interviews/6178911/?amp=1)).

These are a few large companies, not a survey of the market, and policies change. But they point the same way: a remote "write this from scratch" task is now harder to trust, and the interesting question has moved from "can you produce code?" to "do you understand it well enough to judge it?"

## Why knowledge matters more as an early filter

If an assistant can draft the code, what separates a strong engineer from a weak one? Mostly the things an assistant can't supply on their behalf:

- **Concepts and theory.** Knowing how a database uses an index, why a race condition happens or what a framework does on each request lets an engineer see when generated code is wrong.
- **Reading code.** Before using AI output, someone has to read it and know what it will print, return or change.
- **Debugging.** When code that is "almost right" fails, the fix comes from understanding why.
- **Judgment.** Choosing between two working approaches takes knowledge of trade-offs: performance, security, maintainability.

These are knowledge and reasoning skills, and they can be tested directly and quickly. Hiring research already ranks job knowledge tests among the better predictors of job performance on average: in a 2022 re-analysis of decades of studies, Sackett, Zhang, Berry and Lievens estimated a validity of .40 for job knowledge tests, close to structured interviews at .42 ([doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)). That research predates AI assistants, so it doesn't prove anything about AI-era work. But it supports using a job-specific knowledge test as an early filter, and the shift described above makes the knowledge it tests more central to the job, not less.

## Hands-on exercises still have a place

None of this makes coding exercises useless. It changes when you run them and what they look like:

- **Pairing with AI.** Like Canva's round, give candidates an assistant and a realistic, open-ended task. Watch how they break it down, what they ask the assistant, and what they accept or reject.
- **Code review.** Hand over a pull request, perhaps one written by AI, with a few real bugs. Ask what they'd change and why.
- **Debugging.** Give a small codebase with a failing test. This is close to the daily work the survey describes and hard to fake.
- **System design.** For senior roles, a discussion of trade-offs shows judgment that no single prompt produces.

These exercises take an engineer's time to run and to score. That's the main reason to put a quick, broad knowledge check before them, so they go to the candidates most likely to succeed.

## A process for the AI era

1. **Screen applications for hard requirements only:** right to work, location, must-have experience.
2. **Run a short knowledge screen** on concepts, theory and code reading for your stack.
3. **Run a hands-on exercise** in a form that fits how your team works: AI-assisted pairing, code review or debugging, remote or in person.
4. **Add system design** for senior roles.
5. **Hold a structured interview** with set questions and a scoring rubric, including how the candidate uses AI tools and checks their output.
6. **Let people decide,** with every result as one input.

Tell candidates up front which tools are allowed at each stage. A clear rule is fairer than a guessing game, and it makes the results easier to compare.

For the full step-by-step version, see [How to hire engineers](/guides/hiring-engineers).

## Where testee fits

testee is well suited to step 2. It turns your job description into a timed multiple-choice knowledge interview, and you review the proposed topics before any question is written, so the test covers your stack and nothing else.

- **Concepts and theory from the job description:** databases, APIs, architecture, a framework's behavior, security practices.
- **Code-reading questions:** a short piece of code with questions about what it prints or returns, what it does, why it fails or which change fixes it. That's the same reviewing skill AI-assisted work depends on.
- **A timer on every question:** each question has its own countdown, enforced by the server, and each candidate gets their own random set of questions. That makes looking answers up, including asking an AI assistant, harder. It doesn't make it impossible.
- **Integrity signals:** scorecards flag answers too fast to have read the question, times the candidate left the page, and copy attempts. Once a candidate finishes, their report also points out answer patterns that relaying questions to an AI tends to leave: about the same time on every question whatever its length or difficulty, or hard questions right while easy ones were wrong. A flag or a pattern is a reason to look closer, not proof of cheating.
- **Questions for the live interview:** the report suggests up to 3 questions the candidate got right, from their strongest topics, to talk through in a live interview, where no AI can answer for them.

What testee doesn't do: candidates don't write, run or debug code in testee, and it doesn't watch them use an AI assistant. That belongs in the hands-on stage, run in-house or on a developer platform, which complements the knowledge screen. See [skills tests by role](/tests) for ready-made tests to start from, and [AI interviews](/ai-interviews) for how testee uses AI and what it leaves to people.

## Fairness and candidate experience

Changing your process is a good moment to check that it's fair:

- **Be clear about AI rules** at every stage, in writing.
- **Keep conditions the same** for everyone at a given stage.
- **Offer accommodations,** such as extra time, to candidates who ask.
- **Don't treat a signal as a verdict.** Pausing, looking away or answering quickly can have innocent causes.
- **Keep it short.** Every stage you add costs strong candidates time they may spend on another offer.

## Summary

AI assistants have made producing code cheaper and judging code more important. A good process reflects that: test knowledge, theory and code reading early, where it's quick and, with a timer on each question, harder to outsource, then use hands-on exercises, often with AI allowed, to see how candidates work. Be clear about the rules, and keep people in charge of the decision.

## Sources

- Stack Overflow, [2025 Developer Survey: AI](https://survey.stackoverflow.co/2025/ai).
- GitHub, [Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/), 28 October 2025.
- Canva Engineering, [Yes, you can use AI in our interviews](https://canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews), 11 June 2025.
- Business Today, [Meta to test job applicants with AI-assisted coding interviews](https://www.businesstoday.in/amp/technology/news/story/meta-to-test-job-applicants-with-ai-assisted-coding-interviews-amid-ai-expansion-plans-487200-2025-07-31), 31 July 2025, citing 404 Media.
- CNBC via NBC New York, [Meet the 21-year-old helping coders use AI to cheat in Google and other tech job interviews](https://www.nbcnewyork.com/news/business/money-report/meet-the-21-year-old-helping-coders-use-ai-to-cheat-in-google-and-other-tech-job-interviews/6178911/?amp=1), 9 March 2025.
- Sackett, P. R., Zhang, C., Berry, C. M., & Lievens, F. (2022). Revisiting meta-analytic estimates of validity in personnel selection. *Journal of Applied Psychology, 107*, 2040–2068. [doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)

## Related reading

- [How to hire engineers](/guides/hiring-engineers)
- [Skills tests by role](/tests)
- [Cheating in online assessments, and what works against it](/guides/cheating-in-online-assessments)
- [AI interviews: what they are and how to use them fairly](/ai-interviews)
- [Skills tests vs CV screening](/guides/skills-tests-vs-cv-screening)
