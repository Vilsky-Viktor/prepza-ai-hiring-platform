"""OpenAI chat models, built one way by every service that talks to one. Needs the package's `llm`
extra (langchain-openai); the key comes from OPENAI_API_KEY."""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from prepza_common.ai.ai_constants import AUDIO_PRICES, BATCH_SHARE, MODEL_PRICES
from prepza_common.config.constants import CHARS_PER_TOKEN


def chat_model(
    model: str, reasoning_effort: str, temperature: float | None = None, **options
) -> ChatOpenAI:
    """A chat model thinking at `reasoning_effort` ("none", "minimal", "low", "medium", "high").

    Reasoning models accept a temperature only at effort "none", so at any other effort
    `temperature` is left out. `options` go to ChatOpenAI as they are (timeout, max_retries, ...).
    Nothing is stored at OpenAI: its Responses API, which a model with tools may use, would keep
    each call (and the people's data in it) by default.
    """
    return ChatOpenAI(
        model=model,
        reasoning_effort=reasoning_effort,
        temperature=temperature if reasoning_effort == "none" else None,
        store=False,
        **options,
    )


def price_of(prices: dict, model_name: str):
    """A model's price; a dated version ("gpt-6-luna-2026-08-01") has its model's. None for a
    model without one."""
    if model_name in prices:
        return prices[model_name]

    found = [name for name in prices if model_name.startswith(f"{name}-")]

    return prices[max(found, key=len)] if found else None


def call_cost(model_name: str, usage: dict, batch: bool = False) -> float | None:
    """USD for a model's usage metadata, as LangChain reports it: cached input at its own price,
    and a Batch API call at BATCH_SHARE of the price. None for a model without a price in
    MODEL_PRICES."""
    price = price_of(MODEL_PRICES, model_name)

    if price is None:
        return None

    cached = (usage.get("input_token_details") or {}).get("cache_read", 0) or 0
    fresh = usage.get("input_tokens", 0) - cached
    cost = (fresh * price[0] + cached * price[1] + usage.get("output_tokens", 0) * price[2]) / 1e6

    return cost * BATCH_SHARE if batch else cost


def audio_cost(model_name: str, seconds: float) -> float | None:
    """USD for `seconds` of audio turned into text or made from it; None for a model without a
    price."""
    price = price_of(AUDIO_PRICES, model_name)

    return None if price is None else price * seconds / 60


def latest_messages(messages: list[tuple[bool, str]], room: int) -> list[BaseMessage]:
    """What a model reads of a conversation: its latest messages (oldest first) within `room`
    characters. `messages` are (from the user, text), oldest first; one without text is left
    out."""
    kept: list[BaseMessage] = []

    for from_user, text in reversed(messages):
        if not text:
            continue

        room -= len(text)

        if room < 0:
            break

        kind = HumanMessage if from_user else AIMessage
        kept.insert(0, kind(content=text))

    return kept


def estimated_tokens(text: str) -> int:
    """The tokens of `text`, for a model call cut short that reported none: about
    CHARS_PER_TOKEN characters each, rounded up."""
    return -(-len(text) // CHARS_PER_TOKEN)


def estimated_input(messages: list[BaseMessage]) -> int:
    """The tokens a model call read, estimated from its messages (see estimated_tokens)."""
    return estimated_tokens("".join(str(message.content) for message in messages))
