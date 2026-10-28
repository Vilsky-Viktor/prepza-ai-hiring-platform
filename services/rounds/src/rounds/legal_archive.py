"""Run after giving a changed legal document its new version: `python -m rounds.legal_archive`."""

from rounds.helpers.legal import archive

if __name__ == "__main__":
    archive()
