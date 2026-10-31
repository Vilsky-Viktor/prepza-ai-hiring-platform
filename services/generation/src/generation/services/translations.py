# What a translation of testee's own texts (news posts, campaign emails) must be to be saved:
# every field within its limits (services/batch_steps.py checks each reply with it).
from pydantic import BaseModel


def checked[T: BaseModel](result: T, limits: dict[str, int], language: str) -> T:
    """The translation trimmed; raises when a field in `limits` is empty or longer than its
    limit."""
    values = {
        name: value.strip() if isinstance(value, str) else value
        for name, value in result.model_dump().items()
    }

    for name, longest in limits.items():
        if not values[name]:
            raise ValueError(f"Empty {language} translation")

        if len(values[name]) > longest:
            raise ValueError(f"The {language} translation is too long")

    return type(result)(**values)
