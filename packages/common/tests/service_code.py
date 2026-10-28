"""The services' code (`services/<svc>/src/<svc>/`), for the checks that read it by path, so
none passes on finding nothing."""

from pathlib import Path


def service_code(root: Path, pattern: str = "**/*.py", service: str = "*") -> list[Path]:
    """The files matching `pattern` in every service's package (or in `service`'s). Fails when
    there are none."""
    found = sorted(root.glob(f"services/{service}/src/*/{pattern}"))

    assert found, f"no service code matches services/{service}/src/*/{pattern}"

    return found
