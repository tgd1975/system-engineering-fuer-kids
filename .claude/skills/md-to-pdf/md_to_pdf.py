# -*- coding: utf-8 -*-
"""Render a Markdown file to a nicely styled PDF.

Usage:
    python md_to_pdf.py "Berufsvorstellung Systems Engineer.md" [output.pdf]

Handles the quirks of this environment:
  * Images are inlined as base64 data URIs, so they always appear in the PDF
    (Chrome headless otherwise blocks local file:// images).
  * The PDF is written to a temp folder first and then copied into place,
    because Chrome cannot write directly into the SynologyDrive folder
    ("Zugriff verweigert").
  * Chrome is launched with a throwaway --user-data-dir so a stale/running
    Chrome instance can't hijack the render (which produced image-less PDFs).
"""
import base64
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

# --- markdown library (auto-install if missing) ------------------------------
try:
    import markdown
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "markdown"],
                   check=False)
    import markdown

CSS = """
  @page { size: A4; margin: 18mm 16mm; }
  * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  html { font-size: 12pt; }
  body { font-family: "Segoe UI", "Verdana", sans-serif; line-height: 1.55;
         color: #1f2933; max-width: 100%; }
  h1 { font-size: 2em; color: #1d4ed8; border-bottom: 3px solid #1d4ed8;
       padding-bottom: .2em; margin-bottom: .1em; }
  h2 { font-size: 1.4em; color: #1e40af; margin-top: 1.4em;
       border-bottom: 1px solid #c7d2fe; padding-bottom: .15em; page-break-after: avoid; }
  h3 { font-size: 1.1em; color: #334155; }
  p { margin: .55em 0; }
  em { color: #475569; }
  ul, ol { margin: .4em 0 .8em 1.3em; }
  li { margin: .2em 0; }
  strong { color: #b91c1c; }
  blockquote { margin: .8em 0; padding: .6em 1em; background: #fef9c3;
               border-left: 6px solid #f59e0b; border-radius: 6px; page-break-inside: avoid; }
  blockquote p { margin: .2em 0; }
  blockquote strong { color: #92400e; }
  img { display: block; margin: .8em auto; max-width: 100%; height: auto; page-break-inside: avoid; }
  table { border-collapse: collapse; width: 100%; margin: 1em 0; page-break-inside: avoid; }
  th, td { border: 1px solid #94a3b8; padding: 8px 10px; vertical-align: top; text-align: left; }
  th { background: #dbeafe; color: #1e3a8a; }
  td img { margin: .3em auto; }
  td ul, td ol { margin: .3em 0 .3em 1.1em; }
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>
"""


def find_browser():
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in candidates:
        if pathlib.Path(c).exists():
            return c
    raise SystemExit("No Chrome or Edge found for PDF rendering.")


def build_html(md_path: pathlib.Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    body = markdown.markdown(
        text,
        extensions=["tables", "attr_list", "sane_lists", "md_in_html", "smarty"],
        output_format="html5",
    )

    base_dir = md_path.parent

    def embed(match):
        quote, src = match.group(1), match.group(2)
        p = (base_dir / src)
        if not p.exists():
            return match.group(0)
        data = base64.b64encode(p.read_bytes()).decode("ascii")
        ext = p.suffix.lower().lstrip(".")
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        return f'src={quote}data:{mime};base64,{data}{quote}'

    body = re.sub(r'src=(["\'])((?!https?:|data:)[^"\']+)\1', embed, body)
    return TEMPLATE.format(title=md_path.stem, css=CSS, body=body)


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python md_to_pdf.py "<file.md>" [output.pdf]')

    md_path = pathlib.Path(sys.argv[1]).resolve()
    if not md_path.exists():
        raise SystemExit(f"Not found: {md_path}")

    out_pdf = pathlib.Path(sys.argv[2]).resolve() if len(sys.argv) > 2 \
        else md_path.with_suffix(".pdf")

    browser = find_browser()
    html = build_html(md_path)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        html_file = tmp / "doc.html"
        pdf_file = tmp / "doc.pdf"
        profile = tmp / "profile"
        html_file.write_text(html, encoding="utf-8")

        subprocess.run([
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--user-data-dir={profile}",
            "--no-pdf-header-footer",
            "--virtual-time-budget=10000",
            f"--print-to-pdf={pdf_file}",
            html_file.as_uri(),
        ], check=True)

        if not pdf_file.exists():
            raise SystemExit("Browser did not produce a PDF.")
        shutil.copyfile(pdf_file, out_pdf)

    print(f"Wrote {out_pdf} ({out_pdf.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
