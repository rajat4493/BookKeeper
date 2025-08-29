from __future__ import annotations

import colorsys
import hashlib
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter


# ---------- helpers ----------
def _pick_font(candidates: list[str], size: int):
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

def _font(size: int):
    mac_sans = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    win_sans = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    linux_sans = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    return _pick_font(mac_sans + win_sans + linux_sans, size)

def _hsl(h: float, s: float, l: float) -> tuple[int, int, int]:
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l, s)
    return (int(r * 255), int(g * 255), int(b * 255))

def _lerp(a: tuple[int, int, int], b: tuple[int, int, int], t: float):
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))

def _hash_hue(text: str) -> float:
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()
    return (int(h[:2], 16) / 255.0) * 360.0

def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> str:
    if not text:
        return ""
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = (" ".join(cur + [w])) if cur else w
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return "\n".join(lines)

def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    if not text:
        return (0, 0)
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=6, align="center")
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])

def _auto_fit(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_h: int, start: int, min_size: int = 42):
    size = start
    while size >= min_size:
        f = _font(size)
        wrapped = _wrap_text(draw, text, f, max_w)
        w, h = _text_size(draw, wrapped, f)
        if w <= max_w and h <= max_h:
            return f, wrapped
        size -= 4
    f = _font(min_size)
    return f, _wrap_text(draw, text, f, max_w)

def _vignette(base: Image.Image, strength: float = 0.45):
    W, H = base.size
    mask = Image.new("L", (W, H), 0)
    grad = Image.radial_gradient("L").resize((W, H))
    grad = Image.eval(grad, lambda p: 255 - p)          # bright center
    grad = Image.eval(grad, lambda p: int(p * strength))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    return Image.composite(base.convert("RGBA"), dark, grad).convert("RGBA")


# ---------- motifs (minimal, tone-on-tone) ----------
def _leaf_layer(size: tuple[int, int], color: tuple[int, int, int], alpha: int = 42) -> Image.Image:
    """Draw 3 minimalist leaves in bottom-right corner."""
    W, H = size
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    def leaf(cx, cy, w, h, angle_deg):
        # draw ellipse on temp then rotate
        temp = Image.new("RGBA", (int(w*1.4), int(h*1.4)), (0, 0, 0, 0))
        td = ImageDraw.Draw(temp)
        bbox = [int(0.2*w), int(0.2*h), int(1.2*w), int(1.2*h)]
        td.ellipse(bbox, fill=(color[0], color[1], color[2], alpha))
        # vein
        td.line([(w*0.7, h*0.2),(w*0.7, h*1.2)], fill=(255,255,255, int(alpha*0.5)), width=max(1, int(w*0.04)))
        imr = temp.rotate(angle_deg, resample=Image.BICUBIC, expand=True)
        layer.alpha_composite(imr, (int(cx - imr.width/2), int(cy - imr.height/2)))
    # positions near bottom-right
    leaf(W*0.80, H*0.82, W*0.18, H*0.10, -25)
    leaf(W*0.88, H*0.86, W*0.16, H*0.09, 10)
    leaf(W*0.83, H*0.92, W*0.14, H*0.08, -5)
    return layer

def _currency_rain(size: tuple[int, int], color: tuple[int, int, int], alpha: int = 36) -> Image.Image:
    """Falling currency glyphs (€, $, zł) subtle, diagonal drift."""
    W, H = size
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    font = _font(max(36, int(W * 0.04)))
    glyphs = ["$", "€", "zł"]
    cols = 6
    for c in range(cols):
        x = int((c + 0.5) * W / cols)
        for r in range(6):
            y = int((r * H / 6) + ((c % 2) * 18))
            g = glyphs[(c + r) % len(glyphs)]
            d.text((x + r*6, y + r*8), g, font=font, fill=(color[0], color[1], color[2], alpha))
    # slight blur to keep it minimal
    return layer.filter(ImageFilter.GaussianBlur(0.6))

def _network_dots(size: tuple[int, int], color: tuple[int, int, int], alpha: int = 34) -> Image.Image:
    """Minimal AI/data motif: small dots + lines in top-right."""
    W, H = size
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    nodes = []
    # cluster in a quadrant
    for i in range(10):
        nx = int(W * 0.68 + (W * 0.24) * (i % 5) / 5)
        ny = int(H * 0.14 + (H * 0.22) * (i // 5) / 2)
        nodes.append((nx, ny))
    for i, (x1, y1) in enumerate(nodes):
        for j, (x2, y2) in enumerate(nodes):
            if j > i and (i + j) % 3 == 0:
                d.line([(x1, y1), (x2, y2)], fill=(color[0], color[1], color[2], alpha), width=1)
    for (x, y) in nodes:
        d.ellipse([x-3, y-3, x+3, y+3], fill=(color[0], color[1], color[2], min(alpha+10, 60)))
    return layer

def _choose_theme(cfg: dict, outline: dict) -> str:
    # explicit override
    theme = (cfg.get("cover", {}) or {}).get("theme", "auto")
    topic = ((outline.get("title") or cfg.get("topic") or "") + " " + (cfg.get("audience") or "")).lower()
    if theme and theme != "auto":
        return theme
    # keyword heuristics
    keys = {
        "ayurveda": ["ayurveda", "yoga", "herb", "wellness", "holistic", "dosha"],
        "tariff": ["tariff", "duty", "customs", "import", "export", "trade", "pricing"],
        "ai": ["ai", "ml", "machine learning", "automation", "data", "genai", "llm"],
    }
    for k, arr in keys.items():
        if any(w in topic for w in arr):
            return k
    return "minimal"  # default motif-free

def _motif_layer(theme: str, size: tuple[int, int], color: tuple[int, int, int], strength: int):
    if theme == "ayurveda":
        return _leaf_layer(size, color, alpha=strength)
    if theme == "tariff":
        return _currency_rain(size, color, alpha=strength)
    if theme == "ai":
        return _network_dots(size, color, alpha=strength)
    return Image.new("RGBA", size, (0, 0, 0, 0))


# ---------- main ----------
def make_cover(cfg: dict, outline: dict, out_path: Path) -> None:
    # Canvas
    W, H = cfg.get("cover_size", [1600, 2560])
    if isinstance(W, list):  # if config accidentally provides list
        W, H = 1600, 2560

    title = (outline.get("title") or cfg.get("topic") or "Untitled").strip()
    subtitle = (outline.get("subtitle") or cfg.get("subtitle") or "").strip()
    author = (cfg.get("author") or "").strip()

    # Palette from title hash
    hue = _hash_hue(title)
    base = _hsl(hue, 0.42, 0.46)
    grad_to = _hsl((hue + 32) % 360, 0.44, 0.34)
    accent = _hsl((hue + 302) % 360, 0.55, 0.58)

    # Smooth vertical gradient
    grad = Image.new("RGB", (W, H), 0)
    gd = ImageDraw.Draw(grad)
    for y in range(H):
        t = y / max(1, H - 1)
        gd.line([(0, y), (W, y)], fill=_lerp(base, grad_to, t))
    im = grad

    # Minimal motif layer (tone-on-tone)
    theme = _choose_theme(cfg, outline)
    motif_strength = int((cfg.get("cover", {}) or {}).get("motif_strength", 36))  # 0-255
    motif = _motif_layer(theme, (W, H), accent, strength=motif_strength)
    im = Image.alpha_composite(im.convert("RGBA"), motif)

    # Subtle vignette for focus
    im = _vignette(im, strength=0.35)

    # Text layout
    draw = ImageDraw.Draw(im)
    margin_x = int(W * 0.12)
    max_title_w = W - margin_x * 2
    max_title_h = int(H * 0.30)
    max_sub_w = W - margin_x * 2
    max_sub_h = int(H * 0.12)

    title_font, wrapped_title = _auto_fit(draw, title, max_title_w, max_title_h, start=164, min_size=56)
    sub_font_size = max(38, int(title_font.size * 0.46))
    sub_font = _font(sub_font_size)
    wrapped_sub = _wrap_text(draw, subtitle, sub_font, max_sub_w) if subtitle else ""

    # Title position (slightly above center)
    tw, th = _text_size(draw, wrapped_title, title_font)
    tx = (W - tw) // 2
    ty = int(H * 0.30) - th // 2

    # Draw text with soft readability halo
    text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(text_layer)
    # halo
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.ellipse([tx - 60, ty - 40, tx + tw + 60, ty + th + 60], fill=(0, 0, 0, 40))
    halo = halo.filter(ImageFilter.GaussianBlur(16))
    text_layer = Image.alpha_composite(text_layer, halo)
    # title
    td.multiline_text((tx, ty), wrapped_title, font=title_font, fill=(255, 255, 255, 245), align="center", spacing=6)

    # subtitle
    if wrapped_sub:
        sw, sh = _text_size(td, wrapped_sub, sub_font)
        sx = (W - sw) // 2
        sy = ty + th + 28
        td.multiline_text((sx, sy), wrapped_sub, font=sub_font, fill=(238, 240, 248, 235), align="center", spacing=6)

    # author (optional footer)
    if author:
        f_small = _font(34)
        aw = ImageDraw.Draw(text_layer).textlength(author, font=f_small)
        ax = (W - int(aw)) // 2
        ay = int(H * 0.88)
        ImageDraw.Draw(text_layer).text((ax, ay), author, font=f_small, fill=(240, 242, 250, 220))

    # Compose
    out = Image.alpha_composite(im, text_layer).convert("RGB")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path, quality=95)
