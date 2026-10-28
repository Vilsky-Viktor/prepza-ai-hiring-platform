# prepza's suppression list (services/suppression.py). A permanent bounce suppresses an address at
# once; temporary ones (a full mailbox, a server down) only once SOFT_BOUNCES of them come within
# SOFT_BOUNCE_DAYS, kept that long and then forgotten.
PERMANENT_BOUNCE = "Permanent"
SOFT_BOUNCES = 3
SOFT_BOUNCE_DAYS = 14
