"""Run after giving a changed legal document its new version: `python -m site_content.legal_archive`."""

from site_content.helpers.legal import archive

if __name__ == "__main__":
    archive()
