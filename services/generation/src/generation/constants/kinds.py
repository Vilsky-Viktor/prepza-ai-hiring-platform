from enum import StrEnum


class GenerationKind(StrEnum):
    INTERVIEW = "interview"
    # A superadmin's template (docs/features/admin-zone.md, Templates), saved to library without a company.
    TEMPLATE = "template"
    # Questions added to an existing template's topics: a top-up or a superadmin's addition
    # (services/additions.py).
    TEMPLATE_QUESTIONS = "template_questions"
