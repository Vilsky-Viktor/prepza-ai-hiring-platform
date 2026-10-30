# rounds

Candidates' interview sessions and their answers, and free practice rounds. It keeps sessions, answers and integrity signals in its own database, and reads a finished candidate's answer patterns from them when asked (`/internal/invites/{id}/answer-patterns`, never stored); questions come from library, and scores go out as
events; a deleted interview's or company's sessions go when its `interview.deleted` or
`company.deleted` arrives. An interview taken by voice is read aloud and answered by voice here too
(voice mode, below). It also keeps who is open to offers (`/open-to-offers`: a practice user's
opt-in with their name, LinkedIn profile and consent log, which lapses after `OPEN_DAYS`) and gives
companies the open people with practice results on an interview's matching topics
(`/internal/open-to-offers/...`). What it does and its settings:
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

A section started with `voice` (the interview's setting in companies) is read aloud: the step
that opens its next question (`POST /sessions/{id}/step`) first makes sure the question's
reading is kept (read ahead, or made now under the clip's lock), then starts its clock, so the
clock and the voice start together and the reading counts in its time; a reading that fails
leaves the question unread, its clock started. The question and its options are read by
OpenAI's realtime voice model (`SPEECH_MODEL`, voice `SPEECH_VOICE`; `prompts/voice_speech.py`
tells it to say the text exactly; a reading whose own transcript strays from the text, such as
an answer added, is made again once, then the question stays unread; kept as Ogg Opus, its eval
`evals/scripts/voice_reading_test.py`) once per text and voice and kept in
`voice_clips` for every candidate who gets it (one reading a text: a Redis lock per clip, and a
request needing a clip being read waits for it); a reading that fails leaves the question
unread, never stopped. As a question opens, the browser asks for the question after it to be
read ahead, the next section's first after a section's last (`POST
.../voice/next-question/prepare`, 204: only the clip cache gets it, nothing is sent), so moving on
finds it kept. The step's question says whether it's the interview's `last`: the browser plays
"Moving on…" or "Time's up…" before asking for the next step, never after the last. Code blocks and long options aren't read: the interviewer
points to the screen (`helpers/voice_speech.py`). The browser plays the clip
(`GET .../voice/question`), the interviewer's phrases (`.../voice/phrases/{phrase}`,
`.../voice/confirmations?picks=`, `.../voice/saved/{pick}`: "B, saved.", made ahead with the next
question for each option of a single-answer question), and streams each spoken answer while
it's said (`.../voice/stream`, a WebSocket, `services/voice_stream.py`): opened as listening
starts, signed in by its first message (the Firebase token, checked as a write's: a browser can't
give a WebSocket headers, and an address would be logged), the same guards as the upload, then
`start` once the browser hears the candidate (counted as a spoken answer; audio only after it),
16-bit PCM at 16 kHz as it comes (resampled to OpenAI's 24 kHz, `helpers/voice_pcm.py`) into a
realtime transcription session (`integrations/live_hearing.py`, `TRANSCRIBE_MODEL` with the same
keywords, no turn detection of its own), and `end` with the choice waiting: the final text comes
within a second, is matched as below and sent back, and the connection closes. One answer per
connection, at most `STREAM_SECONDS` (55, under Cloud Run's 60-second timeout; the browser
renews a quiet one after 25) and 30 seconds of audio, and at most `MAX_OPEN_STREAMS` (20) open
per instance, so short requests keep the rest of its 40 slots. A refusal or failure closes it
with 4000 plus the status the upload would get (4401, 4404, 4409, 4429, 4502, 4503, 4504; 4400
for anything out of turn), and the browser sends the recording instead (`POST .../voice/answers`,
at most 2 MB), which is turned into text (`TRANSCRIBE_MODEL`, told the options' letters and texts
as keywords) and matched the same way: the candidate gets the same answer or the same refusal.
The audio sent to OpenAI is billed in seconds whether or not its text came back. Each spoken
answer is matched to options, or to a yes or no for the choice waiting; a transcript without words (empty, or only a sound such as "[cough]") is
`noise`, which the browser ignores (`helpers/voice_match.py` `is_noise`); a plain yes while a choice waits (`constants/voice_confirmations.py`) or
a reply of only options' letters ("B", "option B", "B and D": `helpers/voice_letters.py`,
`constants/voice_letters.py`) is read by code, without the model (`helpers/voice_match.py` `obvious`);
anything else by the model (`VOICE_MATCH_MODEL`, `prompts/voice_match.py`, never the answer
key; its eval is `evals/scripts/voice_answers_test.py`). The answer says whether the choice is
`clear` (one option on a single-answer question): the browser saves it at once; any other is
confirmed first. Nothing of it is saved here: the choice is sent to `.../answers` as a tapped one
is, and the audio and the words are never stored, logged or traced. Each answer's stages
(transcribe, match, total; from the speech's end when streamed) come back in a `Server-Timing`
header or the stream's answer and are logged with the session's id only (`Voice answer <id>:
<intent> by code|model[, heard live], transcribe;dur=…`; a stream's opening `Voice stream <id>:
open;dur=…`); the browser reports its own (speech end to answer, to Mira's reaction, whether it
was heard live) to Sentry.
A spoken answer received (its stream's end, or its upload) by its question's deadline plus
`VOICE_UPLOAD_SECONDS` is noted in
Redis (`services/voice_deadline.py`, the service's own time), and the answers route then takes
its result until `VOICE_ANSWER_GRACE_SECONDS` past the deadline instead of the usual
`TIME_GRACE_SECONDS`; one answer per question still wins (the section's lock and the unique
constraint), so a time-out racing it saves nothing twice.
Limits: `VOICE_ANSWERS_PER_USER_HOUR`, `VOICE_ANSWERS_PER_COMPANY_DAY`,
`VOICE_STREAMS_PER_USER_HOUR` (live listening's connections, against floods: it fails open),
`VOICE_CLIPS_PER_COMPANY_DAY`, `VOICE_CLIPS_PER_DAY`, and a preview also the unpaid AI cap.
A voice interview's whole time is the same as in click mode. Clips go with their
company (`company.deleted`) and after 30 days unplayed (`/internal/schedules/voice-clips`, daily).

## Commands

```bash
docker compose up -d --build rounds              # the service and its migrations
cd services/rounds && uv run pytest              # unit tests
scripts/integration.sh rounds                    # integration tests (real Postgres and Redis)
scripts/assistant-openapi.sh                     # refresh the assistant's snapshot of these routes
```
