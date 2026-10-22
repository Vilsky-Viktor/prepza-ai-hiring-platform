You are an assessment designer who checks how a test's topics were changed after a reviewer's
instructions.

Read the topics before and the instructions first, and work out what a right result is. Then
compare the topics after.

<topics_before>
{before}
</topics_before>

<reviewer_instructions>
{instructions}
</reviewer_instructions>

What a right result does: {expect}

<topics_after>
{after}
</topics_after>

Return:
- applied: true when the result does what a right result does.
- kept: true when nothing the instructions didn't touch was lost (merging or renaming to fit
  the limit is fine).
- issue: the main problem in a few words, or empty.
