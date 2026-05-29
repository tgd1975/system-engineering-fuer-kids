---
name: edit-image-text
description: Edit baked-in text labels on the project's PNG illustrations (the stick-figure role cards in Bilder/, diagrams, etc.) while keeping the artwork untouched. Use when asked to rename a figure ("replace Walter with Kerstin"), fix a typo in a label, or change any text rendered into a raster image.
---

# Editing text baked into PNG images

The illustrations in `Bilder/` are raster PNGs with their labels (names like
`Walter`, captions like `Steuergerät`) drawn into the pixels. There is no source
SVG. To change a label you must paint over the old text and re-draw the new text
in a matching font — the rest of the drawing stays as-is.

Tooling here: Python 3 + Pillow (PIL). **No numpy** — use pure PIL `Image.load()`
pixel access. System fonts live in `C:/Windows/Fonts/`.

## The workflow (proven on Walter → Kerstin)

1. **Look at the image** (Read tool) to see the text and where it sits.

2. **Find the text's bounding box and color.** Scan rows for dark, opaque pixels
   in the region where the text is. A blank-row gap separates the artwork from a
   bottom label, which gives you a clean y-range. Record the bbox, the dominant
   text color (e.g. `(43,43,43)`), and the horizontal center.

3. **Identify the font.** Render candidate bold fonts at a size whose cap-height
   matches the text height, then overlay the candidate in red over the original
   and Read the crop to compare letterforms. For this project's role cards the
   match is **Calibri Bold (`calibrib.ttf`) at size 54**, color `(43,43,43)`,
   on a white background. Reuse that unless the image clearly differs.

4. **Replace.** Paint a white rectangle over the old-text bbox (a few px margin),
   then draw the new text centered on the same horizontal center and baseline.

5. **Verify** by reading the output PNG. The artwork must be unchanged; only the
   label differs.

6. **Update references & rebuild PDFs.** If you renamed the file, grep for the
   old name across `*.md`, update `<img src=...>` paths and prose, delete the old
   PNG, then regenerate any affected PDFs with the `md-to-pdf` skill
   (`Berufsvorstellung Systems Engineer.pdf`, `Diplom.pdf`).

## Helper script

`replace_label.py` does steps 2–5 for a bottom-centered label and prints the
detected bbox so you can sanity-check it:

```powershell
python ".claude\skills\edit-image-text\replace_label.py" "Bilder\Walter.png" "Kerstin" "Bilder\Kerstin.png"
```

Arguments: `<source.png> <new-text> <output.png>`. It auto-detects the label
bbox (the lowest contiguous block of dark text below a blank-row gap), erases it,
and redraws with Calibri Bold matched to the original height/center/color.
Always **Read the output** afterwards — auto-detection can misfire on images
whose layout differs from the role cards (e.g. inline diagram labels). For those,
fall back to the manual steps above with explicit coordinates.

## Gotchas

- `numpy` is not installed — don't import it.
- Pillow's `getbbox()` returns `(l,t,r,b)`; subtract the top offset when
  positioning so the baseline lands where you want.
- Match the existing color exactly (`(43,43,43)`, not pure black) or the new
  label will look slightly off next to the artwork.
