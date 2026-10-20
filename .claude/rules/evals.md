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
