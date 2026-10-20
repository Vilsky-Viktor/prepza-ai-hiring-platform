---
paths:
  - "evals/**"
---

# Evals

`evals/` (README with metrics, targets and baselines; `run.sh`; `datasets/`, `judges/`,
`scripts/`; git-ignored `results/`) judges AI changes on numbers before they ship.

- Datasets are frozen, versioned by date, model and prompt, and mix typical, edge and trap
  cases; each real AI failure adds a case. Only made-up or public data, never a company's text,
  not even anonymised.
- Check by code where possible. A judge works out the answer first, compares pairs blind in
  shuffled order, and is checked on traps before its scores count.
- Every result records model, effort, prompt, judge, scores and cost. Compare only with a
  baseline on the same dataset and judge, acting only on differences beyond the judge's noise.
  A shipped change updates the README's baselines (rule 9).
- Running one: the `run-eval` skill.

## Success criteria

- Each metric is specific and measurable with a target taken from a baseline or expert
  judgement, never "good quality". Measure several dimensions: task fidelity with edge cases,
  consistency, tone, privacy, latency and price (price and latency have targets too).
- Every model-calling feature has an eval; a feature without one (translations, campaigns,
  titles) changes only once it has one.
- Keep capability evals (room to grow) apart from regression evals (near 100%, guarding against
  backsliding); retire a saturated eval.

## Datasets

- Mirror the real distribution, then add edge cases (missing, irrelevant or overlong input,
  harmful input, cases experts disagree on) and traps; balance cases where a behaviour should
  happen with cases where it shouldn't. Cover every script family we ship (right to left, CJK,
  Thai, Devanagari, plural-heavy Slavic).
- A real failure (a reported key, a thumbs-down) becomes a made-up case that fails the same way,
  with the answer an expert would give as its reference, not the disliked one. Read a sample of
  feedback first: it leans negative. Feedback-derived cases stay apart from hand-written
  requirement cases.
- A good case is one two experts would grade alike; it ships with a reference answer that proves
  it's solvable and the grader works.
- More cases with automatic grading beat a few graded by hand. Size a dataset for the difference
  it must show (a power calculation, `evals/datasets/README.md`, "How big").
- Each dataset has its section in `evals/datasets/README.md`: what it is, how it was made, when
  it was refreshed. `check_datasets.py` checks shape, duplicates and overlap with prompt
  examples. Prefer made-up, held-out sets over public ones a model may have seen.
- A fast set (`--sample`, fixed seed) for iterating; decisions on the full set.

## Graders and judges

- Code graders first, then model graders calibrated against human labels, then humans.
- A judge has a role, a rubric and output code can read; it runs on a strong model, a different
  one from the model judged where one is available. Pass/fail or pairwise over open 1–5 scales;
  any scale is anchored (1 = …, 5 = …). Grade each dimension apart; allow "unknown" when
  information is missing; use reference answers.
- Control known biases: shuffle or swap positions, control for length, hide self-identifying
  marks.
- Calibrate before trusting a judge: report Cohen's kappa against the reference, and true positive
  and true negative rates apart when failures are rare; plant broken answers (traps) and require
  them caught.
- Agents: grade the final outcome and the transcript, don't punish valid other paths, give partial
  credit for multi-part tasks, repeat trials and report pass^k where consistency matters.

## Results and statistics

- Every score comes with its interval (Wilson for shares, ±1.96·SE for means; `stats.py`);
  cluster errors when items are related; compare variants on the same items with paired
  differences where possible; repeat stochastic runs per item.
- Every result records the date, the commit, a hash of the prompts, judge and constants, the
  model, effort, scores, tokens, time and cost (`run_record()`); `system_fingerprint` when a
  run-to-run difference needs explaining.
- Production feedback: votes are scores on the trace with a stable id, so a changed vote updates.

Research (local notes, git-ignored): `internal_docs/eval-best-practices.md`.
