from enum import StrEnum


class SetKind(StrEnum):
    INTERVIEW = "interview"
    # Made by a superadmin (docs/features/admin-zone.md, Templates); the question bank reuses theirs.
    TEMPLATE = "template"


class OwnerType(StrEnum):
    COMPANY = "company"
    # A template belongs to prepza itself.
    PLATFORM = "platform"


PLATFORM_OWNER = "prepza"


class Pool(StrEnum):
    """Which readers a template question is for: fixed when it's created and never changed.
    A company interview's own questions have none."""

    # Free practice and the role pages' sample questions: public, shown with answers.
    PRACTICE = "practice"
    # Company interviews copied from the template, and the bank new generations reuse from;
    # never shown publicly.
    COMPANY = "company"


# What each topic of a template is meant to hold. A new template's questions reused from the
# bank are company questions; of its fresh ones, the first PRACTICE_QUESTIONS (spread across its
# subtopics, as generation lists them round-robin) go to practice and the rest to companies.
PRACTICE_QUESTIONS = 30
COMPANY_QUESTIONS = 60

# A deleted company's sets go this many at a time, each batch its own transaction: a set takes
# its topics and questions with it (cascade), so a batch stays small.
SET_DELETE_BATCH = 20
