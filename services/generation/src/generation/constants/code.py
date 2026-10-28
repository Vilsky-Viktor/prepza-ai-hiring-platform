from typing import Literal

# The languages a question's example can be in, by the names the site's code colors know them
# (shiki's); "text" for anything else, such as a table's rows or a spreadsheet formula, shown
# without colors.
CodeLanguage = Literal[
    "python",
    "javascript",
    "typescript",
    "java",
    "csharp",
    "cpp",
    "c",
    "go",
    "rust",
    "ruby",
    "php",
    "kotlin",
    "swift",
    "scala",
    "dart",
    "r",
    "sql",
    "bash",
    "powershell",
    "json",
    "yaml",
    "xml",
    "html",
    "css",
    "graphql",
    "dockerfile",
    "text",
]

# Examples tagged in one model call by the tag_code_languages job.
TAG_BATCH_SIZE = 20
# The first untagged fence in a question's text, and one tagged "text", which the job checks
# again with --text.
UNTAGGED_FENCE = "```\n"
TEXT_FENCE = "```text\n"
