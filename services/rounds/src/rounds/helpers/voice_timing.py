def server_timing(stages: dict[str, float]) -> str:
    """Stages' seconds as a Server-Timing header, in milliseconds: "transcribe;dur=812, ..."."""
    return ", ".join(f"{name};dur={round(seconds * 1000)}" for name, seconds in stages.items())
