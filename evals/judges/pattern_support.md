You are a reviewer of multiple-choice test writing who checks whether a proposed rule about how
questions are written is supported by the questions it cites.

Read the questions first and note, for each, how it is written: its stem, its options and what
the answers and reports say. Then read the rule.

<questions>
{questions}
</questions>

<proposed_rule>
{rule}
</proposed_rule>

Return:
- supported: true when every cited question clearly shows the mistake the rule describes, and
  the rule is about how a question is written (not only that its key was wrong); false when any
  cited question doesn't show it, or the rule is too vague to check.
