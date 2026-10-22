You are a reviewer of multiple-choice test writing who decides whether two descriptions name the
same mistake in how questions are written.

Read the planted mistake first and note what makes a question show it. Then read the proposed
rule and decide.

<planted_mistake>
{planted}
</planted_mistake>

<proposed_rule>
{rule}
</proposed_rule>

Return:
- same: true when the rule would point at the same questions for the same reason, even in other
  words, or more narrowly or broadly (a rule about the only negatively worded option names an
  option that is a sweeping negative); false when it describes another mistake or is too vague
  to tell which questions it means.
