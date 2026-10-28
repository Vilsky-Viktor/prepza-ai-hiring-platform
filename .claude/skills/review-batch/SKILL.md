---
name: review-batch
description: Work through a platform review file (internal_docs/reviews/*.md) in approved batches - propose, fix one item at a time, test, commit, mark done. Use when fixing review findings.
---

# Fix review findings in batches

Review files live in `internal_docs/reviews/` (git-ignored). Each finding is a table row
ending in `⏳ |` while open and `✅ |` once done.

## Propose

1. Count what's open: `grep -c "⏳ |$" internal_docs/reviews/<file>.md`.
2. Pick about six related open items and describe each in one line, in terms of what a user or
   the business sees (not internal service names).
3. Give the open count and ask "Shall I go ahead?". Start only after the user approves.

## Fix, one item at a time

For each item:

1. Read the row in full and the code it names; check the finding still holds (code moves).
   If it no longer applies, say so and mark it done with a note.
2. Fix it the simplest way that solves it (rule 4), reusing code rather than copying (rule 10):
   when the same pattern is copied in several places, fix all of them through one helper.
3. Update everything the change touches: tests (rule 8: behaviour, not wording), docs and READMEs (rule 9), help texts,
   the FAQ, the help chat's guide (`services/rounds/src/rounds/prompts/help.py`), the assistant's
   prompts, and every language (use the `translate` skill).
4. Verify (the `verify` skill).
5. Commit that item alone, by rule 13 of CLAUDE.md, naming the item in the body
   ("(review E15)"). Never push.
6. Mark it done:

   ```bash
   python3 - <<'EOF'
   p='internal_docs/reviews/<file>.md'; s=open(p).read()
   lines=s.split('\n')
   for i,l in enumerate(lines):
       if l.startswith('| E15 |') and l.rstrip().endswith('⏳ |'):
           lines[i]=l.rstrip()[:-3]+'✅ |'
   open(p,'w').write('\n'.join(lines))
   EOF
   ```

## Report the batch

For each item, what changed as the user sees it, then the tests run, anything not verified, the
new open count, and the next proposed batch. Be exact about status: name what isn't done.
