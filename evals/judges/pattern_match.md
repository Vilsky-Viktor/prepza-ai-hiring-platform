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
- same: true when a question that shows the planted mistake is exactly what the rule warns
  against, even in other words or more generally; false when the rule describes another mistake
  or is too vague to tell.
