"""The services' code wherever it lives while the services move to the new layout:
`services/<svc>/app/` (the old one) and `services/<svc>/src/<svc>/` (the new one). Checks that
read the code by path use it, so none passes on finding nothing."""

from pathlib import Path


def service_code(root: Path, pattern: str = "**/*.py", service: str = "*") -> list[Path]:
    """The files matching `pattern` in every service's package (or in `service`'s), under
    either layout. Fails when there are none."""
    found = sorted(root.glob(f"services/{service}/app/{pattern}"))
    found += sorted(root.glob(f"services/{service}/src/*/{pattern}"))

    assert found, f"no service code matches services/{service}/(app|src/*)/{pattern}"

    return found
