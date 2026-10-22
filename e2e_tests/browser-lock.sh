# Sourced by pages.sh and signed-in.sh: at most BROWSER_RUNS browser runs (default 1) use the
# local stack at once, whoever starts them; the dev frontend can't serve more without pages
# timing out. A run takes a free slot, a directory under /tmp holding its pid, or waits for one;
# a slot whose run is gone (killed, crashed) is taken over. The slot is freed when the run exits.
# mkdir is atomic, so this needs no flock (which macOS lacks).

browser_slots="${TMPDIR:-/tmp}/prepza-browser-runs"
browser_slot=""

release_browser_slot() {
  if [ -n "$browser_slot" ]; then
    rm -rf "$browser_slot"
  fi
}

take_browser_slot() {
  local most="${BROWSER_RUNS:-1}"
  local waiting=""
  local slot
  local holder
  local i

  mkdir -p "$browser_slots"

  while true; do
    for ((i = 1; i <= most; i++)); do
      slot="$browser_slots/$i"

      if mkdir "$slot" 2>/dev/null; then
        echo "$$" >"$slot/pid"
        browser_slot="$slot"
        trap release_browser_slot EXIT

        return 0
      fi

      holder="$(cat "$slot/pid" 2>/dev/null || true)"

      # A slot without a live run: its run was killed before it could free it (or is still
      # writing its pid: a slot without one is taken over only after a minute).
      if [ -n "$holder" ] && ! kill -0 "$holder" 2>/dev/null; then
        rm -rf "$slot"
      elif [ -z "$holder" ] && [ -n "$(find "$slot" -maxdepth 0 -mmin +1 2>/dev/null)" ]; then
        rm -rf "$slot"
      fi
    done

    if [ -z "$waiting" ]; then
      echo "waiting for another browser run to end (BROWSER_RUNS=$most at once)" >&2
      waiting=1
    fi

    sleep 5
  done
}
