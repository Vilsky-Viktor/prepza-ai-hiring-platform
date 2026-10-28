"""Every OpenAI client generation builds has a timeout and retries from its constants; the
Batch API's isn't retried by the client, as creating a batch twice would bill it twice."""

from generation.constants.generation import BATCH_MAX_RETRIES, LLM_MAX_RETRIES, LLM_TIMEOUT_SECONDS
from generation.integrations import llm, openai_batch


def test_the_batch_apis_client_never_retries_on_its_own(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    openai_batch.get_client.cache_clear()
    client = openai_batch.get_client()

    assert (client.max_retries, client.timeout) == (BATCH_MAX_RETRIES, LLM_TIMEOUT_SECONDS)
    assert BATCH_MAX_RETRIES == 0
    openai_batch.get_client.cache_clear()


def test_embeddings_have_the_calls_timeout_and_retries(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    llm.get_embeddings.cache_clear()
    embeddings = llm.get_embeddings()

    assert (embeddings.max_retries, embeddings.request_timeout) == (
        LLM_MAX_RETRIES,
        LLM_TIMEOUT_SECONDS,
    )
    llm.get_embeddings.cache_clear()
