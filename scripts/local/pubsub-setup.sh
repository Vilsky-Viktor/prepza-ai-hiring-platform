#!/bin/sh
# Creates the local Pub/Sub topic and its push subscriptions in the emulator, as Terraform does in
# Google Cloud. The emulator's container runs it at every start, as a restart empties the emulator.
# Safe to repeat: existing ones answer 409 and are left as they are. Funnel events
# aren't pushed; locally nothing stores them (in Google Cloud they go to BigQuery).
set -eu

base="http://${PUBSUB_EMULATOR_HOST}/v1/projects/${GOOGLE_CLOUD_PROJECT}"

until curl -sf "http://${PUBSUB_EMULATOR_HOST}/" >/dev/null; do
  sleep 1
done

# Creates a topic or subscription; 409 means it already exists, anything else but 200 stops here.
put() {
  status="$(curl -sS -o /dev/null -w '%{http_code}' -X PUT "$@")"

  case "$status" in
    200 | 409) ;;
    *)
      echo "pubsub-setup: $1 answered $status" >&2
      exit 1
      ;;
  esac
}

put "$base/topics/events"

for consumer in library companies notifications ats api assistant billing; do
  put "$base/subscriptions/$consumer-events" \
    -H "Content-Type: application/json" \
    -d "{\"topic\": \"projects/${GOOGLE_CLOUD_PROJECT}/topics/events\",
         \"filter\": \"NOT hasPrefix(attributes.type, \\\"funnel.\\\")\",
         \"pushConfig\": {\"pushEndpoint\": \"http://$consumer:8000/internal/events\"}}"
done

echo "pubsub ready"
