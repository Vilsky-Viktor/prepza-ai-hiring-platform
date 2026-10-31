class KeyRejected(Exception):
    """The ATS refused the company's key (wrong, revoked, expired or missing a permission): the
    connection needs a new one."""


class WriteRefused(Exception):
    """The ATS refused what testee writes (a candidate's results) while it still takes the key
    for reading: the key lacks write access. The connection keeps working."""
