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

env_args=()

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
docker cp "$container:/tmp/evals/datasets/." "$here/datasets/"
docker cp "$container:/tmp/evals/results/." "$here/results/"
