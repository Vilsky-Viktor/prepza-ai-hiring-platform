#!/usr/bin/env bash
# Builds the downloadable documents on the /documents page from their Markdown sources in
# frontend/content/documents into frontend/public/documents: DOCX with pandoc, and PDF with
# pandoc (HTML with print.css) and then Chromium's print to PDF in Playwright's Docker image.
# Needs uv and Docker. Usage: scripts/documents/build.sh
set -euo pipefail

cd "$(dirname "$0")/../.."

src=frontend/content/documents
out=frontend/public/documents

# pandoc from the pypandoc_binary wheel, so it needn't be installed.
pandoc="$(uvx --from pypandoc_binary python -c 'import pypandoc; print(pypandoc.get_pandoc_path())')"

# Editable templates: Word files.
for name in candidate-notice-templates dpia-template; do
  "$pandoc" "$src/$name.md" -o "$out/prepza-$name.docx"
done

# Documents to read and keep: PDFs. The HTML goes into the container on stdin and the PDF comes
# back on stdout, so nothing needs mounting.
for name in instructions-for-companies data-processing-agreement; do
  title="$(head -n 1 "$src/$name.md" | sed 's/^# //')"
  "$pandoc" "$src/$name.md" -s --embed-resources --css scripts/documents/print.css \
    --metadata pagetitle="$title" |
    docker run --rm -i mcr.microsoft.com/playwright:v1.64.1-noble@sha256:47b510dd9230bf0b9bfc9b20102241e577ea7a99334ab4c3ca19f19770e9b8ea sh -c '
      cat > /tmp/page.html
      chrome="$(ls /ms-playwright/chromium-*/chrome-linux*/chrome | head -n 1)"
      "$chrome" --headless --no-sandbox --disable-gpu --no-pdf-header-footer \
        --print-to-pdf=/tmp/page.pdf file:///tmp/page.html 2>/dev/null
      cat /tmp/page.pdf' >"$out/prepza-$name.pdf"
done

ls -l "$out"
