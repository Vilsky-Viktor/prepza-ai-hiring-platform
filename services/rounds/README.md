# rounds

Candidates' interview sessions and their answers, and free practice rounds. It keeps sessions, answers and integrity signals in its own database, and reads a finished candidate's answer patterns from them when asked (`/internal/invites/{id}/answer-patterns`, never stored); questions come from library, and scores go out as
events; a deleted interview's or company's sessions go when its `interview.deleted` or
`company.deleted` arrives. An interview taken by voice is read aloud and answered by voice here too
(voice mode, below). What it does and its settings:
[candidates](../../docs/features/candidates.md) and
[templates and practice](../../docs/features/templates-and-practice.md).

## Layout

```
src/rounds/
├── main.py, config.py      # App wiring; settings
├── api/v1/                 # Routes (the folder name only: URLs have no extra /v1)
├── api/dependencies.py     # Calls from other services
├── core/                   # db.py (engine, Session), security.py (service tokens)
├── handlers/               # Pub/Sub events (deleted interviews, companies and accounts);
│                           # dispatch.py picks one
├── services/               # Interview steps, answers, timed sessions, practice, signals,
│                           # deletions; each opens its
│                           # transaction
├── repositories/           # Database queries (sessions, answers, signals, ...);
│                           # take the session, never commit
├── models/, schemas/       # SQLAlchemy tables; request and response models
├── helpers/, constants/    # Pure functions (scores, exports, answer patterns); fixed values
├── prompts/                # Voice mode's matching and reading instructions
└── integrations/           # library, Redis, OpenAI
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

The FAQ, page guides, guide articles, legal texts and the contact form are the site service's
(`/api/site/help/...`); the help chat is the assistant's.

Routes call services; services open the transaction (`async with Session.begin() as
session:`) and pass it to the repositories, so an action's steps are saved together (an
answer with the finish it brings, a step's finished sections with the next question's clock),
and read limits from Redis or call library outside it. A plain read may open
`async with Session() as session:` in the route. `tests/unit/test_layers.py` checks the imports
and that no repository commits; batched deletions take the session factory, each batch its own
transaction.

`src/` is on the path (`PYTHONPATH` in the Dockerfile, `pythonpath` for pytest,
`prepend_sys_path` for Alembic, `evals/run.sh`), so the package imports as `rounds`
(`rounds.api.v1.sessions`).

## Voice mode

A section started with `voice` (the interview's setting in companies) is read aloud: when its
next question opens (`POST /sessions/{id}/step`), the question and its options are read by
OpenAI's text-to-speech (`SPEECH_MODEL`, Ogg Opus) once per text and voice and kept in
`voice_clips` for every candidate who gets it, and the question's own time starts after the
reading (`question_reading_seconds`, at most `MAX_READING_SECONDS`); a reading that fails leaves
the question unread, never stopped. Code blocks and long options aren't read: the interviewer
points to the screen (`helpers/voice_speech.py`). The browser plays the clip
(`GET .../voice/question`), the interviewer's phrases (`.../voice/phrases/{phrase}`,
`.../voice/confirmations?picks=`), and sends each spoken answer (`POST .../voice/answers`, at most
2 MB): it's turned into text (`TRANSCRIBE_MODEL`) and matched to options, or to a yes or no for
the choice waiting (`VOICE_MATCH_MODEL`, `prompts/voice_match.py`, never the answer key; its eval
is `evals/scripts/voice_answers_test.py`). Nothing of it is saved: a confirmed choice is sent to
`.../answers` as a tapped one is, and the audio and the words are never stored, logged or traced.
Limits: `VOICE_ANSWERS_PER_USER_HOUR`, `VOICE_ANSWERS_PER_COMPANY_DAY`,
`VOICE_CLIPS_PER_COMPANY_DAY`, `VOICE_CLIPS_PER_DAY`, and a preview also the unpaid AI cap.
A voice interview's whole time adds `VOICE_READING_SECONDS` a question. Clips go with their
company (`company.deleted`) and after 30 days unplayed (`/internal/schedules/voice-clips`, daily).

## Commands

```bash
docker compose up -d --build rounds              # the service and its migrations
cd services/rounds && uv run pytest              # unit tests
scripts/integration.sh rounds                    # integration tests (real Postgres and Redis)
scripts/assistant-openapi.sh                     # refresh the assistant's snapshot of these routes
```
