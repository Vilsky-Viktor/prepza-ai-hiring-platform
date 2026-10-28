# A question's example whose opening fence has no language yet ("```" then a new line), from
# before generation tagged them; generation's tag_code_languages job adds one.
UNTAGGED_FENCE = "```\n"
# One tagged "text", in no notation the site colors: checked again by the same job, since an
# example showing several files used to get it though it is in one ("--text").
TEXT_FENCE = "```text\n"
# A language as the site's code colors name it: lowercase letters, digits, "+", "#" or "-".
CODE_LANGUAGE_PATTERN = r"^[a-z0-9+#-]{1,20}$"
MAX_UNTAGGED_BATCH = 100
