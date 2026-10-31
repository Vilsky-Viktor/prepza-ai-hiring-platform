#!/usr/bin/env bash
# What load runs left in the local databases. `ids` prints the throwaway companies' and users' ids
# (two lines, ready for SQL's IN); `count "$ids"`, after the clean-up, counts every row still
# holding one of them and fails when any is left. Only rows of load runs ever match: companies
# named "Load <run> <n>" and candidates at delivered+load-<run>-candidate-<n>@resend.dev.
set -euo pipefail

postgres="${E2E_POSTGRES:-testee-postgres-1}"
companies="name ~ '^Load [a-z0-9]+ [0-9]+\$'"
candidates="email ~ '^delivered\\+load-[a-z0-9]+-candidate-[0-9]+@resend\\.dev\$'"

sql() {
  docker exec "$postgres" psql -U testee -d "$1" -tAc "$2"
}

# Quoted and comma-separated; '' when there's none, which matches nothing.
list() {
  local rows

  rows="$(sql "$1" "$2" | sed "s/.*/'&'/" | paste -sd, -)"
  echo "${rows:-''}"
}

if [[ "${1:?usage: leftovers.sh ids | count IDS}" == "ids" ]]; then
  company_ids="$(list companies "SELECT id FROM companies WHERE $companies")"
  echo "$company_ids"
  list companies "SELECT user_id FROM members WHERE company_id::text IN ($company_ids)
    UNION SELECT user_id FROM candidate_invites WHERE $candidates AND user_id IS NOT NULL"

  exit 0
fi

company_ids="$(echo "$2" | sed -n 1p)"
user_ids="$(echo "$2" | sed -n 2p)"
left=0

check() {
  local count

  count="$(sql "$1" "SELECT count(*) FROM $2 WHERE $3")"
  echo "$1.$2: $count left"
  left=$((left + count))
}

check companies companies "$companies OR id::text IN ($company_ids)"
check companies members "company_id::text IN ($company_ids) OR user_id::text IN ($user_ids)"
check companies interviews "company_id::text IN ($company_ids)"
check companies candidate_invites "$candidates OR user_id::text IN ($user_ids)"
check companies audit_events "company_id::text IN ($company_ids)"
check rounds sessions "user_id::text IN ($user_ids)"
check library sets "owner_id::text IN ($company_ids, $user_ids)"
check billing wallets "owner_id::text IN ($company_ids)"
check billing holds "owner_id::text IN ($company_ids)"
check ats ats_connections "company_id::text IN ($company_ids)"
check api api_keys "company_id::text IN ($company_ids)"
check notifications notifications "(recipient = 'user' AND recipient_id::text IN ($user_ids))
  OR (recipient = 'company' AND recipient_id::text IN ($company_ids))"

if [[ "$left" -gt 0 ]]; then
  echo "FAIL $left rows of throwaway companies and users left" >&2

  exit 1
fi

echo "nothing left"
