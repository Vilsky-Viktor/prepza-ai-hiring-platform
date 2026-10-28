from generation.constants.events import GENERATION_FAILED
from generation.constants.kinds import GenerationKind
from generation.models.generation import Generation


def failed_event(generation: Generation) -> tuple[str, dict] | None:
    """Companies hears of a failed interview generation; a template has no interview to tell."""
    if generation.kind != GenerationKind.INTERVIEW:
        return None

    return GENERATION_FAILED, {"generation_id": str(generation.id)}
