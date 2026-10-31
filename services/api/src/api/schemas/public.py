from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from api.constants import examples


class Interview(BaseModel):
    """One of your company's interviews."""

    model_config = ConfigDict(json_schema_extra={"examples": [examples.INTERVIEW]})

    id: UUID = Field(description="The interview's id")
    title: str | None = Field(
        description="Null while the interview's questions are being generated"
    )
    status: Literal["new", "in_process", "hired"] = Field(
        description="`new` before any candidate is invited, then `in_process`; `hired` once "
        "your company marks it so"
    )
    ready: bool = Field(description="Whether the questions are ready and candidates can be invited")
    pass_mark: int = Field(description="The minimum grade, in percent, a candidate needs to pass")
    candidate_count: int = Field(description="How many candidates were invited to it")
    created_at: datetime = Field(description="When it was made")
    updated_at: datetime | None = Field(
        default=None,
        description=(
            "When it last changed; to sync, pass the last one you got as `updated_since`, with "
            "its `id` as `after`"
        ),
    )


class Signals(BaseModel):
    """Integrity signals recorded while the candidate answered.

    They can have innocent causes; never reject a candidate automatically on them.
    """

    tab_leaves: int = Field(description="How many times the candidate left the page")
    copies: int = Field(description="How many times the candidate tried to copy text")
    fast_answers: int = Field(description="Answers given too quickly to have read the question")
    answer_patterns: list[Literal["timing", "person_fit"]] | None = Field(
        default=None,
        description=(
            "Patterns in the finished candidate's answers: `timing`, answer times that didn't "
            "follow the questions' length and difficulty; `person_fit`, hard questions right "
            "while easy ones were wrong. Only when one candidate is read (null in lists and web "
            "hook events); empty when none showed"
        ),
    )


class Section(BaseModel):
    """One section of a candidate's interview."""

    title: str = Field(description="The section's title")
    grade: int | None = Field(
        default=None, description="The section's grade in percent; null until it's finished"
    )


class Candidate(BaseModel):
    """A candidate invited to one of your interviews, with their progress and results."""

    model_config = ConfigDict(json_schema_extra={"examples": [examples.CANDIDATE]})

    id: UUID = Field(description="The candidate's id, within the interview")
    interview_id: UUID = Field(description="The interview the candidate was invited to")
    email: str = Field(description="The email the candidate was invited with")
    name: str | None = Field(
        default=None,
        description=(
            "The candidate's name: as given when they were invited, edited by an owner or admin, "
            "or else from their sign-in when they start; null while unknown"
        ),
    )
    status: Literal["invited", "undelivered", "in_process", "finished", "expired", "deleted"] = (
        Field(
            description=(
                "`invited`; `undelivered` when the invite email bounced; `in_process` once they "
                "start; `finished`; `expired` when the invite went unused for 30 days; `deleted` "
                "when the candidate deleted their account"
            )
        )
    )
    progress: int = Field(description="Percentage of the interview answered")
    grade: int | None = Field(
        description="Final grade in percent; null until the candidate finishes"
    )
    passed: bool | None = Field(
        description=(
            "Whether the grade reached the pass mark; null until the candidate finishes. It "
            "supports a person's decision: don't reject a candidate automatically on it"
        )
    )
    signals: Signals = Field(description="Integrity signals recorded while they answered")
    flagged: bool = Field(
        default=False,
        description=(
            "Whether the candidate has any integrity signal (a page leave, a copy attempt or a "
            "fast answer): worth a person's look at the full results, not a reason to reject"
        ),
    )
    extra_time: int = Field(
        default=0,
        description="Extra time per question the company gave the candidate, in percent",
    )
    mode: Literal["click", "voice"] = Field(
        default="click",
        description=(
            "How the candidate takes the interview: `voice` (the questions are read aloud and "
            "may be answered by voice) or `click`; the mode the company chose for them, else "
            "the interview's"
        ),
    )
    sections: list[Section] | None = Field(
        default=None,
        description=(
            "Each section's grade, in order; only when one candidate is read, and in web hook "
            "events (null in lists)"
        ),
    )
    results_url: str = Field(
        description="Link to the candidate's full results and report in testee"
    )
    invite_url: str | None = Field(
        default=None,
        description=(
            "The candidate's invite link, to send them yourself if the invite email didn't "
            "arrive; null once they've finished or the invite has expired"
        ),
    )
    created_at: datetime = Field(description="When the invitation was first sent")
    updated_at: datetime | None = Field(
        default=None,
        description=(
            "When the candidate last changed (status, name, extra time or result; not the "
            "progress while they answer); to sync, pass the last one you got as `updated_since`, "
            "with its `id` as `after`"
        ),
    )
    started_at: datetime | None = Field(
        default=None, description="When the candidate started; null before"
    )
    finished_at: datetime | None = Field(
        default=None, description="When the candidate finished; null before"
    )


class CandidateIn(BaseModel):
    """Who to invite, and how."""

    model_config = ConfigDict(json_schema_extra={"examples": [examples.CANDIDATE_IN]})

    email: EmailStr = Field(description="The candidate's email address")
    name: str | None = Field(
        default=None,
        max_length=200,
        description=(
            "The candidate's name, optional (at most 200 characters). It fills a name not known "
            "yet; inviting the same address again doesn't change a known one"
        ),
    )
    return_url: str | None = Field(
        default=None,
        max_length=2048,
        description=(
            "Where to take the candidate once they've finished, optional: any https address "
            "(http only on `localhost` or `127.0.0.1`, while you test). The finished page shows "
            "a button to it, with `testee_invite=<candidate id>` added to its query"
        ),
    )
    theme: Literal["light", "dark", "default"] = Field(
        default="default",
        description=(
            "The theme the candidate's pages show, in your company's colors for it: `light` or "
            "`dark` always shows that theme, `default` the candidate's own. A `theme` added to "
            "the `invite_url` (`?theme=dark`) or given to the SDK wins over it"
        ),
    )
    sign_in: bool = Field(
        default=True,
        description=(
            "Whether the candidate signs in to testee with this email, which testee sends the "
            "invitation and its reminder to. Set it to false when your platform already knows "
            "who the candidate is and sends them to the response's `invite_url` itself: the "
            "link then opens the interview without signing in, and testee sends no emails. "
            "Anyone with that link can take the interview, so give it only to the candidate"
        ),
    )
    mode: Literal["click", "voice"] | None = Field(
        default=None,
        description=(
            "How this candidate takes the interview, optional: `voice` (the questions are read "
            "aloud and may be answered by voice) or `click`; left out, the interview's mode. "
            "Voice only in the languages voice mode supports (English, Spanish, German, French, "
            "Portuguese and Italian). Inviting an address whose invite is still open returns it "
            "as it is, mode included"
        ),
    )


class Note(BaseModel):
    """A note your company's team wrote on an interview, never shown to candidates."""

    model_config = ConfigDict(json_schema_extra={"examples": [examples.NOTE]})

    id: UUID = Field(description="The note's id")
    text: str = Field(description="The note, as plain text with its line breaks")
    author: str | None = Field(
        description=(
            "Who wrote it: their name, or their email without one; null once they're no longer "
            "a member of your company"
        )
    )
    pinned: bool = Field(
        description="Whether it's the interview's pinned note (at most one is), listed first"
    )
    created_at: datetime = Field(description="When it was written")
    edited_at: datetime | None = Field(description="When its text last changed; null if never")


class CandidateEvent(BaseModel):
    """The `data` object of a candidate's event (`candidate.finished`, `candidate.started`,
    `candidate.undelivered`, `candidate.expired`): the interview and the candidate as they are
    when it's sent."""

    interview: Interview = Field(description="The interview, as it is now")
    candidate: Candidate = Field(description="The candidate, as they are now")


class RemovedEvent(BaseModel):
    """The `data` object of a `candidate.removed` event: who was removed, as the candidate is
    gone."""

    interview_id: UUID = Field(description="The interview the candidate was removed from")
    candidate_id: UUID = Field(description="The candidate's id")
    email: str = Field(description="The email the candidate was invited with")


class InterviewEvent(BaseModel):
    """The `data` object of an `interview.ready` event."""

    interview: Interview = Field(description="The interview, now ready")


class TestEvent(BaseModel):
    """The `data` object of a `test` event: empty."""
