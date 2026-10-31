# The event loop's heartbeat (observability/loop_watch.py): it beats this often, and a beat late
# by over LOOP_BLOCK_SECONDS is logged with where the loop was stuck: its innermost
# LOOP_STACK_FRAMES frames, each file's path from its package on (after one of CODE_ROOTS).
LOOP_BEAT_SECONDS = 0.1
LOOP_BLOCK_SECONDS = 1.0
LOOP_STACK_FRAMES = 8
CODE_ROOTS = ("/site-packages/", "/src/")
# Where the loop's thread waits for its next event: there, it isn't blocked.
IDLE_FILE = "selectors.py"
