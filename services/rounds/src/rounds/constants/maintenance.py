from datetime import timedelta

# A candidate interview counts as running while it has a question on screen shown this recently;
# a question's time runs out well before.
RUNNING_WINDOW = timedelta(minutes=15)
