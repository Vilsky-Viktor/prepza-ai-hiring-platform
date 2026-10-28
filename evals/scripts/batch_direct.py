"""Batch work run at once, for the evals: each step's request body exactly as the Batch API gets
it (generation's batch_steps.body_for), sent straight to chat completions, and its reply moved on
by the service's own `advance`, until the work is done or given up. Measures what a batch would
write without waiting a day for one; the price is the direct one (a batch costs half)."""

from generation.integrations import openai_batch
from generation.services.batch_steps import advance, body_for


async def run_direct(kind: str, step: str, payload: dict) -> tuple[object, list[tuple[str, dict]]]:
    """The work's result (None when it gave up) and each call's model and usage."""
    used = []
    attempt = 0

    while True:
        body = body_for(kind, step, payload)
        response = await openai_batch.get_client().chat.completions.create(**body)
        reply = response.choices[0].message.content if response.choices else None
        used.append((response.model, openai_batch.usage_of(response.model_dump())))
        found = await advance(kind, step, attempt, payload, reply)

        if found.give_up or found.result is not None:
            return found.result, used

        step, payload, attempt = found.step, found.payload, attempt + 1
