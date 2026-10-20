#!/usr/bin/env bash
# Runs an offline test script inside a service container of the local stack, which has the
# service's code, packages and OpenAI key, then copies new datasets and results back.
#
#   evals/run.sh <generation|generation-worker|rounds|library|assistant> <script.py> [arguments]
#
# generation-worker has generation's code too: a second container, so two tests can run at once.
# MODEL, EFFORT, JUDGE_MODEL, JUDGE_EFFORT and OVERSAMPLE are passed through when set.
set -euo pipefail

service="$1"
script="$2"
shift 2

here="$(cd "$(dirname "$0")" && pwd)"
container="prepza-${service}-1"
code="${service%-worker}"

docker exec "$container" rm -rf /tmp/evals
docker cp "$here" "$container:/tmp/evals"
# What this run writes is copied back alone: copying all of datasets/ and results/ would undo
# changes made here while it ran (a concurrent run's results, a dataset edited meanwhile).
docker exec "$container" touch /tmp/evals/.started

# The commit a result was made on; "+changes" when the service or evals/ differ from it.
commit="$(git -C "$here" rev-parse --short HEAD)"

if [[ -n "$(git -C "$here" status --porcelain -- "../services/$code" .)" ]]; then
  commit="$commit+changes"
fi

env_args=(-e "EVAL_COMMIT=$commit")

for name in MODEL EFFORT JUDGE_MODEL JUDGE_EFFORT OVERSAMPLE; do
  if [[ -n "${!name:-}" ]]; then
    env_args+=(-e "$name=${!name}")
  fi
done

# Langfuse tracing off (its keys emptied): test runs would fill it with eval traffic.
docker exec -w "/services/$code" -e "PYTHONPATH=/services/$code:/tmp/evals/scripts" \
  -e LANGFUSE_PUBLIC_KEY= -e LANGFUSE_SECRET_KEY= \
  "${env_args[@]+"${env_args[@]}"}" "$container" \
  uv run --no-sync python "/tmp/evals/scripts/$script" "$@"

# Build scripts write datasets/; every script writes results/.
docker exec "$container" find /tmp/evals/datasets /tmp/evals/results -type f \
  -newer /tmp/evals/.started |
  while read -r path; do
    mkdir -p "$(dirname "$here/${path#/tmp/evals/}")"
    docker cp "$container:$path" "$here/${path#/tmp/evals/}"
  done
