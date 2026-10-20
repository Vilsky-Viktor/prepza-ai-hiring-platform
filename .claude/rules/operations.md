---
paths:
  - "infra/**"
  - "scripts/ops/**"
  - "docs/runbooks.md"
  - "docs/deployment.md"
  - "packages/common/src/prepza_common/logging.py"
  - "packages/common/src/prepza_common/health.py"
---

# Operations: alerts, incidents, backups

Run by one person: keep the process small (rule 4): two SLOs, two severities, runbook links, a
one-page postmortem. No incident-commander roles, severity ladders or automatic billing stops.

## SLOs

- Two SLOs, measured at the load balancer, not one per service: the public APIs' availability
  (good requests / all, every `/api/*` together, e.g. 99.5%) and candidates' answer latency
  (rounds). The error budget is 1 − SLO; when it's spent, reliability work comes before
  features. Review the SLOs monthly at first, then quarterly.

## Alerts

- Page on symptoms users feel: an SLO burning, an uptime check down, work stuck (dead letters,
  AI stopped, a failed migration, web hook signatures failing). Causes (CPU, memory, database
  connections, disk, instances at `max`, queue depth) are tickets, not pages, unless users
  already wait.
- SLO alerts use the burn rate over two windows at once: a fast burn pages (about 14× over 1 h
  and 5 min), a slow burn is a ticket (about 1–2× over a day or more).
- Every alert policy sets its `severity` and its documentation's `links` to its section in
  `docs/runbooks.md`; a new alert ships with that section. Pages go to the phone (the Cloud
  Monitoring app, SMS as a backup, never SMS alone) and email; tickets to email only.
- AI spend alerts on the day's total as well as on spikes, beside the provider's hard limit.
- Uptime checks: at least three checker regions, content matching to prove the right page
  answered. An outside status page covers Google Cloud itself being down.

## Runbooks and incidents

- `docs/runbooks.md` sections keep their format: how you notice, what the system does itself,
  what to do, when it's resolved. Short; a recurring manual step becomes automation.
- Declare an incident early: customers see it, help is needed, or an hour of work hasn't solved
  it. Keep a timeline, post on the status page; when unsure of severity, take the higher one. A
  breach also follows the breach response plan's clocks.
- A short blameless postmortem (impact, timeline, root and contributing causes, actions) after an
  outage users saw, any data loss, a manual intervention, a long resolution, or a problem users
  reported before an alert; each action becomes a test, an alert or a fix.
- Write down when you're unreachable and what's accepted then: the maintenance switch and the
  status page are the fallback.

## Backups and restores

- A backup counts only once restored: drills are timed and compared with the recovery time in
  `infra/README.md`, kept with the quarterly review.
- Standard Cloud SQL backups live in the project; protection against losing the project
  (enhanced backups in a separate vault) is a stated trade-off in `infra/README.md`, as is a
  shared-core or single-zone database, which the Cloud SQL SLA doesn't cover.
- Restores follow `.claude/rules/privacy.md` (replay erasures, delete dumps).

## Health checks and logs

- A startup probe on `/ready` (dependencies) holds traffic until the instance is ready; a
  liveness probe, if any, checks only `/health` (the process), with a generous period, so a
  database outage never restarts every instance.
- Logs are structured as `.claude/rules/python-services.md` says (`time`, `severity`, `message`,
  trace), so Cloud Logging nests them under their request.

## Capacity and cost

- Budgets alert below what can be afforded (their first alert can take hours; they never cap
  spending); the OpenAI hard limit and the emergency pause are the stops.
- Instance sizes, connections and monthly costs: `internal_docs/capacity-and-costs.md` (local);
  how to scale and what to watch first: `.claude/rules/scalability.md`.

Research (local notes, git-ignored): `internal_docs/operations-best-practices.md`.
