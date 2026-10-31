# Made-up examples the API reference shows beside its schemas.
INTERVIEW = {
    "id": "6b1f0c3e-2a7d-4c58-9e41-3f8a2d5b7c90",
    "title": "Backend developer",
    "status": "in_process",
    "ready": True,
    "pass_mark": 70,
    "candidate_count": 12,
    "created_at": "2026-10-01T09:00:00Z",
    "updated_at": "2026-10-14T16:20:00Z",
}
CANDIDATE = {
    "id": "0e7a4d2c-91b3-4f6e-8a5d-2c1b9f3e7a60",
    "interview_id": INTERVIEW["id"],
    "email": "anna@example.com",
    "name": "Anna Nowak",
    "status": "finished",
    "progress": 100,
    "grade": 86,
    "passed": True,
    "signals": {"tab_leaves": 0, "copies": 1, "fast_answers": 0, "answer_patterns": None},
    "flagged": False,
    "extra_time": 0,
    "mode": "click",
    "sections": None,
    "results_url": "https://testee.ai/companies/…/candidates/0e7a4d2c-91b3-4f6e-8a5d-2c1b9f3e7a60",
    "invite_url": None,
    "created_at": "2026-10-02T10:30:00Z",
    "updated_at": "2026-10-03T11:05:00Z",
    "started_at": "2026-10-03T10:40:00Z",
    "finished_at": "2026-10-03T11:05:00Z",
}
CANDIDATE_IN = {"email": "anna@example.com", "name": "Anna Nowak"}
NOTE = {
    "id": "3c9e1a7b-5d24-4f80-b6e2-8a1d0c4f9e35",
    "text": "For Acme: Backend Developer, contact Lena.",
    "author": "Maria Schmidt",
    "pinned": True,
    "created_at": "2026-10-02T09:15:00Z",
    "edited_at": None,
}
NOTE_IN = {"text": "Shortlist the top five for a call."}
