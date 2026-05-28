---
name: md-to-pdf
description: Render a Markdown file in this project to a styled PDF (with embedded images). Use when the user asks to "render/convert/export a .md to PDF", "rebuild/regenerate the PDF", or mentions creating the Berufsvorstellung / Diplom Konzept PDF.
---

# Markdown → PDF

Renders a Markdown file in this project to a child-friendly, styled A4 PDF with
all images embedded. There is no pandoc / wkhtmltopdf / node here — this uses
Python's `markdown` library plus Chrome (or Edge) headless.

## How to run

```powershell
python ".claude\skills\md-to-pdf\md_to_pdf.py" "Berufsvorstellung Systems Engineer.md"
```

- One argument: the `.md` file. The PDF lands next to it (same name, `.pdf`).
- Optional second argument: a custom output path.
- `python -m pip install markdown` is auto-run if the library is missing.

The script is self-contained: it builds styled HTML, inlines every local image
as a base64 data URI, renders with a headless browser into a temp folder, then
copies the finished PDF into place.

## Environment quirks the script already handles

1. **Local images don't show up** unless inlined — Chrome headless blocks
   `file://` images. The script base64-embeds them into the HTML.
2. **Chrome can't write into the SynologyDrive folder** ("Zugriff verweigert").
   The script renders to a temp dir and copies the PDF in afterwards.
3. **A running/stale Chrome instance hijacks the render** and produces an
   image-less PDF. The script forces a throwaway `--user-data-dir`.

## Sanity checks

- The full document (with all images) is several hundred KB. An image-less
  render is only ~40 KB — if you get that, something regressed.
- Count pages: `python -c "import re; d=open('FILE.pdf','rb').read(); print(len(re.findall(rb'/Type\s*/Page[^s]', d)))"`

## Styling

Defined in the `CSS` constant in `md_to_pdf.py`: blue headings, yellow
highlighted `> **Frage:**` blockquote boxes, bordered tables, centered images.
Adjust there if the look needs to change.
