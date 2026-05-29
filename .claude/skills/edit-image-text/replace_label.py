#!/usr/bin/env python
"""Replace a bottom-centered text label baked into a PNG, keeping the artwork.

Usage:
    python replace_label.py <source.png> <new-text> <output.png>

Detects the label as the lowest contiguous block of dark, opaque pixels that
sits below a blank-row gap (the artwork). Erases it and redraws <new-text> in
Calibri Bold, matched to the original label's height, horizontal center and
color. Pure Pillow — no numpy. Tuned for this project's stick-figure role cards.

Always visually check the output afterwards; auto-detection assumes a single
bottom label on a white background.
"""
import sys
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "C:/Windows/Fonts/calibrib.ttf"
TEXT_COLOR = (43, 43, 43)
DARK_SUM = 300        # r+g+b below this counts as "dark text"
ALPHA_MIN = 100       # opaque enough to be ink


def is_ink(px):
    r, g, b, a = px
    return a > ALPHA_MIN and (r + g + b) < DARK_SUM


def row_has_ink(px, w, y):
    return any(is_ink(px[x, y]) for x in range(w))


def detect_label_bbox(im):
    """Return (minx, miny, maxx, maxy) of the lowest ink block after a gap."""
    w, h = im.size
    px = im.load()
    # Walk up from the bottom: skip trailing blank rows, collect the block,
    # stop at the blank-row gap above it.
    y = h - 1
    while y >= 0 and not row_has_ink(px, w, y):
        y -= 1
    bottom = y
    while y >= 0 and row_has_ink(px, w, y):
        y -= 1
    top = y + 1
    if bottom < 0:
        raise SystemExit("No text found in image.")
    minx, maxx = w, -1
    for yy in range(top, bottom + 1):
        for x in range(w):
            if is_ink(px[x, yy]):
                if x < minx:
                    minx = x
                if x > maxx:
                    maxx = x
    return minx, top, maxx, bottom


def fit_font_size(text, target_h):
    for size in range(20, 120):
        f = ImageFont.truetype(FONT_PATH, size)
        bb = f.getbbox(text)
        if (bb[3] - bb[1]) >= target_h:
            return size, f
    return size, f


def main():
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    src, new_text, out = sys.argv[1], sys.argv[2], sys.argv[3]
    im = Image.open(src).convert("RGBA")
    minx, miny, maxx, maxy = detect_label_bbox(im)
    print(f"Detected label bbox: x {minx}-{maxx}  y {miny}-{maxy}")
    cx = (minx + maxx) // 2
    target_h = maxy - miny
    size, f = fit_font_size(new_text, target_h)
    bb = f.getbbox(new_text)
    tw = bb[2] - bb[0]
    d = ImageDraw.Draw(im)
    # Erase old label with a small margin.
    d.rectangle([minx - 6, miny - 6, maxx + 6, maxy + 6], fill=(255, 255, 255, 255))
    x = cx - tw // 2 - bb[0]
    d.text((x, miny - bb[1]), new_text, font=f, fill=TEXT_COLOR + (255,))
    im.save(out)
    print(f"Wrote {out}  (font Calibri Bold size {size}, new width {tw}px)")


if __name__ == "__main__":
    main()
