---
name: run-eval
description: Measure an AI change with the offline evals before it ships - run the baseline, make the change, compare beyond the judge's noise, keep or revert, record the baseline. Use for any change to a prompt, model, effort, schema or output-shaping step, and for new evals.
---

# Run an eval for an AI change

Rules: `.claude/rules/evals.md` and `.claude/rules/ai.md`. Evals may run while the user reviews
the UI; they use the local stack's containers, not the frontend.

## 1. Pick the eval

Find the metric the change could move in `evals/README.md` (Metrics and targets) and the script
that measures it (`evals/scripts/`). No eval covers the feature? Build one first: a made-up
dataset in `evals/datasets/` with its section in `datasets/README.md`, a judge in
`evals/judges/` (role, rubric, anchored scales, data tagged) checked on traps, and a script that
returns `common.run_record()`. Run `check_datasets.py`.

## 2. Baseline

Use the README's baseline only if it was made on the same dataset, judge, model and effort, and
the code it ran is still what `HEAD` has; otherwise run it now, before changing anything:

```bash
evals/run.sh <service> <script.py> [arguments]     # e.g. generation review_questions.py
```

`MODEL`, `EFFORT`, `JUDGE_MODEL`, `JUDGE_EFFORT` set from the environment when needed. Iterate on
the fast set (`--sample 40`), decide on the full set.

## 3. Change, then measure the same way

Make the change, run the same command with the same dataset, judge and settings. Results land in
`evals/results/` (git-ignored) with the commit (`+changes` for uncommitted work) and the prompts'
hash.

## 4. Compare

- Compare each metric with its baseline using the 95% intervals both results print: act only on
  a difference beyond both intervals (the judge moves by up to about 0.3 between runs). Paired
  per-item differences where the items match.
- Check price and time too: they have targets.
- Read a sample of failing items, not only the numbers.
- Judge reliability still holds: traps all caught, kappa against the reference unchanged.

## 5. Keep or revert

- **Better beyond the noise, nothing worse:** keep it.
- **No difference beyond the noise:** keep only if it's simpler or cheaper; otherwise revert.
- **Worse on any metric beyond the noise, or a missed target:** revert, or say why the trade is
  worth it and ask the user.

## 6. Record

For a change that ships, in the same commit: add the run to `evals/baselines/README.md` (the assistant's
to `evals/baselines/assistant.md`, its actions' to `evals/baselines/assistant-actions.md`, the help chat's to `evals/baselines/help-chat.md`, generation's prompts' to `evals/baselines/generation.md`, the small utility prompts' to
`evals/baselines/utility.md`, voice mode's to `evals/baselines/voice-mode.md`) and update the Baselines table in `evals/README.md` (rule 9). A
real failure found on the way becomes a made-up case in its dataset.

## Report

Per metric: baseline and new value with intervals, price and time, the decision, and what wasn't
measured.
