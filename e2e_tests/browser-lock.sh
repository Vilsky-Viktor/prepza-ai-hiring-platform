# Sourced by pages.sh and signed-in.sh: at most BROWSER_RUNS browser runs (default 1) use the
# local stack at once, whoever starts them; the dev frontend can't serve more without pages
# timing out. A run takes a free slot, a directory in the repo's git folder (shared by every
# worktree and every agent's shell, whatever its TMPDIR) holding its pid, or waits for one;
# a slot whose run is gone (killed, crashed) is taken over. The slot is freed when the run exits.
# Waiting runs queue in the order they started: each takes the next numbered ticket, and only the
# lowest live ticket may take a slot, so no run waits behind later ones.
# mkdir is atomic, so this needs no flock (which macOS lacks).

browser_slots="$(cd "$(git rev-parse --git-common-dir)" && pwd)/prepza-browser-runs"
browser_queue="$browser_slots/queue"
browser_slot=""
browser_ticket=""

release_browser_slot() {
  if [ -n "$browser_slot" ]; then
    rm -rf "$browser_slot"
  fi

  if [ -n "$browser_ticket" ]; then
    rm -rf "$browser_ticket"
  fi
}

# Whether a slot's or a ticket's run is gone: its pid is dead, or it has had no pid for a minute
# (a live run writes it at once).
browser_run_gone() {
  local holder

  holder="$(cat "$1/pid" 2>/dev/null || true)"

  if [ -n "$holder" ]; then
    ! kill -0 "$holder" 2>/dev/null

    return
  fi

  [ -n "$(find "$1" -maxdepth 0 -mmin +1 2>/dev/null)" ]
}

# The next number after every ticket in the queue, taken atomically.
take_browser_ticket() {
  local next

  next=$(($(ls "$browser_queue" | sort -n | tail -n 1) + 1))

  until mkdir "$browser_queue/$next" 2>/dev/null; do
    next=$((next + 1))
  done

  echo "$$" >"$browser_queue/$next/pid"
  browser_ticket="$browser_queue/$next"
}

# The lowest ticket whose run is still alive; tickets of runs that are gone are removed.
first_browser_ticket() {
  local ticket

  for ticket in $(ls "$browser_queue" | sort -n); do
    if ! browser_run_gone "$browser_queue/$ticket"; then
      echo "$browser_queue/$ticket"

      return 0
    fi

    rm -rf "${browser_queue:?}/$ticket"
  done
}

take_browser_slot() {
  local most="${BROWSER_RUNS:-1}"
  local waiting=""
  local slot
  local i

  mkdir -p "$browser_queue"
  trap release_browser_slot EXIT
  take_browser_ticket

  while true; do
    if [ "$(first_browser_ticket)" = "$browser_ticket" ]; then
      for ((i = 1; i <= most; i++)); do
        slot="$browser_slots/$i"

        if mkdir "$slot" 2>/dev/null; then
          echo "$$" >"$slot/pid"
          browser_slot="$slot"
          rm -rf "$browser_ticket"
          browser_ticket=""

          return 0
        fi

        if browser_run_gone "$slot"; then
          rm -rf "$slot"
        fi
      done
    fi

    if [ -z "$waiting" ]; then
      echo "waiting for earlier browser runs to end (BROWSER_RUNS=$most at once)" >&2
      waiting=1
    fi

    sleep "${BROWSER_POLL_SECONDS:-5}"
  done
}
