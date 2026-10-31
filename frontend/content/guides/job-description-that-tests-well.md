---
title: "How to write a job description that tests well"
seoTitle: "How to Write a Job Description That Tests Well"
description: "What a job description needs for a skills test built from it to check the right things: concrete skills and tools, the level, the daily work, what to omit."
updated: "2026-10-29"
---

# How to write a job description that tests well

A job description does two jobs. It tells applicants what the role is, and it's the starting point for everything you check later: the CV screen, the skills test, the interview questions. When the description is vague, every later step has to guess what the job needs, and a skills test built from it ends up testing the guess.

This guide is about the second job: writing a description that a skills test can be built from. It's for hiring managers and recruiters, whatever tool you use. The same habits make a clearer ad, too.

## Why the description decides the test

A knowledge test is useful when it tests what the job actually needs. Hiring research ranks job knowledge tests among the better predictors of job performance on average, but the estimate is for tests built for the job in question; knowledge tests unrelated to the job predict less (see [Skills tests vs CV screening](/guides/skills-tests-vs-cv-screening)).

US employment rules say the same from the legal side. The Uniform Guidelines on Employee Selection Procedures expect a test supported by its content to rest on a job analysis, one that focuses on "the work behavior(s) and the tasks associated with them" ([29 CFR 1607.14(C)](https://www.law.cornell.edu/cfr/text/29/1607.14)). In practice, for most teams, the job description is that analysis written down. And under the Americans with Disabilities Act, a written description prepared before advertising or interviewing is considered evidence of a job's essential functions ([42 U.S.C. 12111(8)](https://www.law.cornell.edu/uscode/text/42/12111)).

So the description is worth an extra half hour. Whatever it says, the test will ask about.

## What a good description gives a test

### 1. Concrete skills, tools and concepts

Name the things a person must know to do the work, in words a test can ask about.

| Hard to test | Testable |
| --- | --- |
| Strong finance background | Reconciles bank statements, knows VAT rules, posts journal entries in a general ledger |
| Data-driven mindset | Writes SQL queries with joins and aggregations; builds dashboards in Power BI |
| Excellent customer skills | Handles refunds and complaints by policy; uses Zendesk macros and escalation rules |
| Modern web development | Builds React components with hooks; calls REST APIs; writes unit tests with Jest |

Name the actual tool or standard when it matters. "Accounting software" leaves the test to pick one; "Xero" doesn't. When any of several tools would do, say so plainly ("a relational database such as PostgreSQL"), and expect a test to cover the kind of tool, not each name on the list.

### 2. The level

The same topic can be tested at very different depths. A junior analyst should know what a join does; a senior one should know why a query is slow and what to change. Say which you need:

- **Scope:** what the person decides alone, and what they hand to someone else.
- **Complexity:** routine cases, or unusual ones and trade-offs.
- **Seniority:** junior, mid-level or senior, in the title or the text.

Years of experience are a rough stand-in for level, and a weak one: in the research above they rank among the weakest predictors of performance. If you include them, also describe the work that the years are supposed to prepare someone for.

### 3. What the person does day to day

Duties are the most useful lines for a test. "Prepares the monthly VAT return" or "triages incoming bugs and reproduces them" tells a test writer which knowledge is used and in what situations. Write duties as a verb and an object, the way you'd describe the work to a new colleague.

If you're unsure what a role usually involves, [O*NET OnLine](https://www.onetonline.org/) lists the typical tasks, technology and knowledge for hundreds of occupations. Use it as a checklist, then keep only what your role actually does.

### 4. A clear line between must-have and nice to have

A test that checks nice-to-haves filters people out for things you could teach in a month. Decide which skills a person needs on day one, and keep the rest clearly marked or out of the text you build the test from.

Knowledge your team expects to teach on the job doesn't belong in a screening test at all. The Uniform Guidelines say a test supported by its content isn't appropriate for knowledge "which an employee will be expected to learn on the job" ([29 CFR 1607.14(C)(1)](https://www.law.cornell.edu/cfr/text/29/1607.14)).

## What to leave out

Some lines help an ad and do nothing for a test. Others shouldn't be there at all.

- **Personality and attitude words:** "self-starter", "rockstar", "passionate". They can't be checked with a knowledge question, and they tend to read as a type of person rather than a job.
- **Culture, perks and slogans.** Keep them in the ad if you like; they aren't test material.
- **Hard requirements:** a license, a right to work, a language, availability. They're yes-or-no checks for the CV screen, not knowledge to test.
- **Wording that discourages groups of people.** The US EEOC gives the example of an ad that seeks "females" or "recent college graduates", which "may discourage men and people over 40 from applying" and may violate the law ([EEOC](https://www.eeoc.gov/prohibited-employment-policiespractices)). Similar rules apply in the EU and the UK. Describe the work, not the person you picture doing it.
- **Everything the company does.** A paragraph about a product the role never touches can end up as a topic.

## The public ad and the text you test from can differ

The ad has to sell the role; the test only needs the requirements. If your ad is long, you don't have to build the test from all of it. Paste the requirements and duties, plus a line on the level, and leave the rest out. A test built from 15 precise lines usually beats one built from three pages.

## An example

**Before:**

> We're looking for a rockstar data analyst with 5+ years of experience and a passion for data. You'll work with our amazing team on exciting projects using modern tools (SQL, Python, BI tools, etc.). Great communication skills and a growth mindset are a must. Free lunch and a dog-friendly office!

A test built from this has to guess the level, which SQL, which BI tool, and what "exciting projects" involve. Half the text is untestable.

**After:**

> **Data analyst (mid-level).** Works independently on routine analysis and with a senior analyst on new models.
>
> - Writes SQL in PostgreSQL: joins, aggregations, window functions, query plans for slow queries
> - Builds and maintains Power BI dashboards for the sales team
> - Cleans and joins data in Python with pandas
> - Defines and checks metrics: conversion, retention, cohort analysis
> - Presents findings to non-technical managers, in writing and in short meetings
>
> Nice to have, not tested: dbt, experience in e-commerce.

Every line names something a question can ask about, the level is stated, and the nice-to-haves are marked.

## A checklist before you build a test

- Each skill names a tool, a method or a concept, not a trait.
- The level is stated: seniority, what they decide alone, how complex the cases are.
- Duties are written as verb and object.
- Must-haves and nice-to-haves are clearly separated.
- Nothing is in it that you expect to teach on the job.
- Hard requirements are left for the CV screen.
- No wording about the person you imagine, only about the work.

## How testee uses a job description

testee is one example of a tool that builds a timed multiple-choice skills test from a job description. Here is what it does with the text, so you can see how the advice above plays out:

- **It reads every requirement.** AI picks out each skill, tool, concept, qualification and day-to-day duty, from every section, including the ones marked preferred or nice to have. Culture statements, perks and slogans are left out.
- **Interchangeable examples become one.** "Tools such as A, B or similar" is kept as the kind of tool, with the one the text prefers (or the most widely used) as the example. Items joined by "and" stay separate. So if you need one specific tool, name only that one.
- **Years and traits are dropped.** Years of experience, seniority, motivation and similar phrasing can't be tested, so only the skill they refer to is used.
- **The level comes from the text.** The seniority, years of experience and scope of responsibility the description asks for set the test's level: basic, medium or hard. The level decides how deep the questions go, and the default time per question: 60 seconds for basic or medium, 75 for hard (see [How to time a skills test](/guides/skills-test-timing-and-extra-time)).
- **You approve the topics before any question is written.** Requirements become up to 10 topics with up to 5 subtopics each. You can uncheck a topic, rename it, edit its subtopics, or describe a change in plain words ("leave out dbt"). Nice-to-haves that slipped through are easy to remove here.
- **Then each topic gets its own question bank,** and each candidate gets a random set from it.

You can paste up to 10,000 characters, or just describe the role in a line or two. A text that names nothing to test, such as a recipe or small talk, is refused. A short list of skills works, but a description with the level and the daily work gives better topics.

To try it, paste a description on the home page, or start from a ready-made test on [skills tests by role](/tests).

## Related reading

- [How to screen 100 applicants in a day](/guides/screen-100-applicants-in-a-day)
- [Skills tests vs CV screening](/guides/skills-tests-vs-cv-screening)
- [How to time a skills test](/guides/skills-test-timing-and-extra-time)
- [Pre-employment testing: a practical guide](/pre-employment-testing)

## Sources

- Uniform Guidelines on Employee Selection Procedures, [29 CFR 1607.14(C)](https://www.law.cornell.edu/cfr/text/29/1607.14), content validity studies.
- Americans with Disabilities Act, [42 U.S.C. 12111(8)](https://www.law.cornell.edu/uscode/text/42/12111), definition of a qualified individual.
- U.S. Equal Employment Opportunity Commission, [Prohibited employment policies/practices](https://www.eeoc.gov/prohibited-employment-policiespractices), job advertisements.
- National Center for O*NET Development, [O*NET OnLine](https://www.onetonline.org/).
- Sackett, P. R., Zhang, C., Berry, C. M., & Lievens, F. (2022). Revisiting meta-analytic estimates of validity in personnel selection. *Journal of Applied Psychology, 107*, 2040–2068. [doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)
