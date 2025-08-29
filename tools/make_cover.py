from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        # Common macOS font; fallback to default
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", size)
    except Exception:
        return ImageFont.load_default()


def make_cover(cfg: dict, outline: dict, out_path: Path) -> None:
    W, H = 1600, 2560
    top = (46, 56, 120)
    bottom = (74, 108, 250)

    im = Image.new("RGB", (W, H), top)
    draw = ImageDraw.Draw(im)

    # Vertical gradient
    for y in range(H):
        ratio = y / H
        r = int(top[0] * (1 - ratio) + bottom[0] * ratio)
        g = int(top[1] * (1 - ratio) + bottom[1] * ratio)
        b = int(top[2] * (1 - ratio) + bottom[2] * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    title = (outline.get("title") or cfg.get("topic", "Untitled"))[:80]
    subtitle = (outline.get("subtitle") or "")[:120]

    f_title = _font(120)
    f_sub = _font(64)

    # Centered title
    tw, th = draw.textlength(title, font=f_title), f_title.size
    # textlength returns width; approximate height via font size
    x_title = (W - draw.textlength(title, font=f_title)) / 2
    y_title = H / 2 - f_title.size
    draw.text((x_title, y_title), title, fill=(255, 255, 255), font=f_title)

    if subtitle:
        x_sub = (W - draw.textlength(subtitle, font=f_sub)) / 2
        y_sub = y_title + f_title.size + 40
        draw.text((x_sub, y_sub), subtitle, fill=(235, 235, 245), font=f_sub)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(out_path)
