"""What every offline test shares: where the datasets live, model prices, the judge prompts, and
one format for a question wherever it comes from."""

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from langchain_openai import ChatOpenAI
from prepza_common.llm import call_cost

EVALS = Path(__file__).resolve().parents[1]
DATASETS = EVALS / "datasets"
RESULTS = EVALS / "results"
JUDGES = EVALS / "judges"

# The judge: stronger than what it judges, and thinking hard, so its verdicts are the reference.
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gpt-6.1-sol")
JUDGE_EFFORT = os.environ.get("JUDGE_EFFORT", "high")


def load(path: Path):
    return json.loads(path.read_text())


def save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")


def prompts_version() -> str:
    """A short hash of the service's prompts, its constants (tool descriptions, limits) and the
    judge prompts, so a result names the exact wording it was made with, committed or not. Run
    from the service's folder, as run.sh does: its code is in `app/` or `src/<service>/`."""
    package = Path("app") if Path("app").is_dir() else Path("src") / Path.cwd().name
    files = sorted((package / "prompts").glob("*.py"))
    files += sorted((package / "constants").glob("*.py"))

    if not files:
        raise FileNotFoundError(f"no prompts or constants in {Path.cwd() / package}")

    files += sorted(JUDGES.glob("*.md"))
    digest = hashlib.sha256()

    for path in files:
        digest.update(path.name.encode() + path.read_bytes())

    return digest.hexdigest()[:10]


def run_record(**fields) -> dict:
    """What every result records (CLAUDE.md rule 20): when, the commit and the prompts it ran
    with, the judge, and the caller's model, effort, scores and cost in `fields`."""
    return {
        "date": datetime.now(UTC).date().isoformat(),
        "commit": os.environ.get("EVAL_COMMIT", "unknown"),
        "prompts": prompts_version(),
        "judge": f"{JUDGE_MODEL} ({JUDGE_EFFORT})",
        **fields,
    }


def tokens_of(usage_metadata: dict) -> int:
    """The tokens of a run's calls, from LangChain's usage callback (all models together)."""
    return sum(used.get("total_tokens", 0) for used in usage_metadata.values())


def reviews_of(path: Path) -> list[dict]:
    """A review file's verdicts: a list, or {"run", "reviews"} as review_questions.py saves."""
    data = load(path)

    return data["reviews"] if isinstance(data, dict) else data


def prompt(name: str) -> str:
    """A judge or writer prompt from judges/, filled in with str.format."""
    return (JUDGES / f"{name}.md").read_text()


def model(name: str, effort: str, timeout: int = 300) -> ChatOpenAI:
    """A reasoning model takes no temperature; one with reasoning off gets a little."""
    if effort == "none":
        return ChatOpenAI(
            model=name, reasoning_effort="none", temperature=0.3, max_retries=3, timeout=timeout
        )

    return ChatOpenAI(model=name, reasoning_effort=effort, max_retries=3, timeout=timeout)


def generation_models(settings, names: tuple[str, ...] = ("interview",)) -> str:
    """With MODEL and EFFORT set, the model under test does the task (each setting in `names`,
    e.g. "interview" for interview_model); without them the service's own setting is tested.
    Returns what does it, for the results."""

    for name in names:
        if "MODEL" in os.environ:
            setattr(settings, f"{name}_model", os.environ["MODEL"])

        if "EFFORT" in os.environ:
            setattr(settings, f"{name}_reasoning_effort", os.environ["EFFORT"])

    return ", ".join(
        f"{name} {getattr(settings, f'{name}_model')} ({getattr(settings, f'{name}_reasoning_effort')})"
        for name in names
    )


def judge() -> ChatOpenAI:
    return model(JUDGE_MODEL, JUDGE_EFFORT)


def cost(model_name: str, usage: dict) -> float:
    """USD for one call's usage metadata; a model without a price fails the run."""
    spent = call_cost(model_name, usage)

    if spent is None:
        raise KeyError(model_name)

    return spent


def correct_option(item: dict) -> str:
    return next(option["answer"] for option in item["options"] if option["correct"])


def correct_options(item: dict) -> set[str]:
    return {option["answer"] for option in item["options"] if option["correct"]}


def is_multi(item: dict) -> bool:
    """A select-all-that-apply question: more than one option marked correct."""
    return len(correct_options(item)) > 1


def options_text(item: dict) -> str:
    return "\n".join(
        f"- {option['answer']}{' [correct]' if option['correct'] else ''}"
        for option in item["options"]
    )


def question_items(path: Path) -> list[dict]:
    """Questions as a list of {id, domain, level, topic, question, options, ...}, from a dataset
    or from a results file of generate_tests.py, which use the same format."""
    data = load(path)

    return data["items"] if isinstance(data, dict) else data
