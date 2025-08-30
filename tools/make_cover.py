from __future__ import annotations

import colorsys, hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# -------------------- font helpers --------------------
def _pick_font(paths: list[str], size: int):
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

def _font_sans(size: int):
    mac = ["/System/Library/Fonts/Helvetica.ttc",
           "/System/Library/Fonts/Supplemental/Arial.ttf",
           "/Library/Fonts/Arial.ttf"]
    win = ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"]
    lin = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
           "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]
    return _pick_font(mac + win + lin, size)

def _font_script(size: int):
    # broad set to increase chances on mac/win/linux
    mac = ["/System/Library/Fonts/Supplemental/SnellRoundhand.ttc",
           "/System/Library/Fonts/Supplemental/Zapfino.ttf",
           "/System/Library/Fonts/Supplemental/Brush Script.ttf",
           "/Library/Fonts/Apple Chancery.ttf"]
    win = ["C:/Windows/Fonts/brushs.ttf", "C:/Windows/Fonts/segoesc.ttf"]
    lin = ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"]  # fallback
    return _pick_font(mac + win + lin, size)

# -------------------- color + layout helpers --------------------
def _hsl(h: float, s: float, l: float) -> tuple[int, int, int]:
    r, g, b = colorsys.hls_to_rgb(h/360.0, l, s)
    return (int(r*255), int(g*255), int(b*255))

def _hash_hue(text: str) -> float:
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()
    return (int(h[:2], 16) / 255.0) * 360.0

def _build_gradient(size: tuple[int,int], top: tuple[int,int,int], bottom: tuple[int,int,int]) -> Image.Image:
    W, H = size
    im = Image.new("RGB", (W, H), bottom)
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / max(1, H-1)
        col = (int(top[0]*(1-t) + bottom[0]*t),
               int(top[1]*(1-t) + bottom[1]*t),
               int(top[2]*(1-t) + bottom[2]*t))
        d.line([(0,y),(W,y)], fill=col)
    return im

def _vignette(im: Image.Image, strength: float=0.18) -> Image.Image:
    if strength <= 0: 
        return im
    W,H = im.size
    mask = Image.new("L", (W,H), 255)
    d = ImageDraw.Draw(mask)
    cw, ch = int(W*0.78), int(H*0.78)
    x0, y0 = (W-cw)//2, (H-ch)//2
    d.ellipse([x0,y0,x0+cw,y0+ch], fill=0)
    mask = mask.filter(ImageFilter.GaussianBlur(220)).point(lambda p: int(p*strength))
    overlay = Image.new("RGBA", (W,H), (0,0,0,255)); overlay.putalpha(mask)
    return Image.alpha_composite(im.convert("RGBA"), overlay)

def _wrap_center(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> str:
    words, lines, row = text.split(), [], []
    for w in words:
        t = (" ".join(row+[w])) if row else w
        wbox = draw.textbbox((0,0), t, font=font)
        if wbox[2]-wbox[0] <= max_w: 
            row.append(w)
        else: 
            if row: lines.append(" ".join(row))
            row=[w]
    if row: lines.append(" ".join(row))
    return "\n".join(lines)

def _auto_fit(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_h: int, font_fn, start: int, min_size: int=44):
    size = start
    while size >= min_size:
        f = font_fn(size)
        wrapped = _wrap_center(draw, text, f, max_w)
        bbox = draw.multiline_textbbox((0,0), wrapped, font=f, spacing=6, align="center")
        w,h = bbox[2]-bbox[0], bbox[3]-bbox[1]
        if w<=max_w and h<=max_h: 
            return f, wrapped
        size -= 4
    f = font_fn(min_size)
    return f, _wrap_center(draw, text, f, max_w)

# -------------------- mandala motif --------------------
def _mandala_layer(size: tuple[int,int], color: tuple[int,int,int], alpha: int=40, scale: float=0.9) -> Image.Image:
    """Tone-on-tone mandala behind the title (minimal)."""
    W,H = size
    R = int(min(W,H)*0.38*scale)
    cx, cy = W//2, int(H*0.33)
    layer = Image.new("RGBA", (W,H), (0,0,0,0))
    d = ImageDraw.Draw(layer)

    # concentric circles
    for k in range(6):
        r = int(R*(0.35 + 0.1*k))
        d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(color[0],color[1],color[2], alpha-8), width=2)

    # petals
    petals = 16
    pet_w, pet_h = int(R*0.22), int(R*0.55)
    pet = Image.new("RGBA", (pet_w*2, pet_h*2), (0,0,0,0))
    pd = ImageDraw.Draw(pet)
    pd.ellipse([int(pet_w*0.2), int(pet_h*0.2), int(pet_w*1.8), int(pet_h*1.8)],
               outline=(color[0],color[1],color[2], alpha), width=3)
    for i in range(petals):
        ang = (360/petals)*i
        rot = pet.rotate(ang, resample=Image.BICUBIC, center=(pet_w, pet_h))
        layer.alpha_composite(rot, (cx-pet_w, cy-int(R*0.1)-pet_h))
    return layer.filter(ImageFilter.GaussianBlur(0.6))

def _choose_theme(cfg: dict, outline: dict) -> str:
    theme = (cfg.get("cover", {}) or {}).get("theme", "auto")
    topic = ((outline.get("title") or cfg.get("topic") or "") + " " + (cfg.get("audience") or "")).lower()
    if theme and theme != "auto": 
        return theme
    keys = {"ayurveda":["ayurveda","yoga","wellness","herb","dosha"],
            "tariff":["tariff","duty","customs","import","export","trade"],
            "ai":["ai","ml","automation","data","genai","llm"]}
    for k, arr in keys.items():
        if any(w in topic for w in arr): 
            return k
    return "minimal"

# -------------------- title condense (optional) --------------------
def _condense_title(title: str, cfg: dict) -> str:
    cover_cfg = (cfg.get("cover", {}) or {})
    if not cover_cfg.get("condense_title", False): 
        return title
    max_words = int(cover_cfg.get("max_title_words", 6))
    # Try LLM condense if available
    try:
        from .ollama_client import generate
        res = generate(cfg.get("refiner_model", cfg.get("writer_model")),
                       f"Condense the title to maximum {max_words} words. Keep meaning. Return only the title: {title}",
                       options={"temperature":0.3}).strip().strip('"')
        if 1 <= len(res.split()) <= max_words:
            return res
    except Exception:
        pass
    # Heuristic fallback
    words = [w for w in title.split() if len(w) > 2]
    return " ".join(words[:max_words]) or title

# -------------------- main --------------------
def make_cover(cfg: dict, outline: dict, out_path: Path) -> None:
    size = cfg.get("cover_size", [1600, 2560])
    if isinstance(size, (list, tuple)) and len(size) == 2:
        W, H = size
    else:
        W, H = 1600, 2560

    # palette
    title = (outline.get("title") or cfg.get("topic") or "Untitled").strip()
    subtitle = (outline.get("subtitle") or cfg.get("subtitle") or "").strip()
    cover_cfg = (cfg.get("cover", {}) or {})
    show_sub = bool(cover_cfg.get("show_subtitle", False))  # default OFF
    title = _condense_title(title, cfg)

    hue = _hash_hue(title)
    top, bottom = _hsl(hue, 0.52, 0.58), _hsl((hue+28)%360, 0.50, 0.42)
    accent = _hsl((hue+298)%360, 0.55, 0.60)

    # optional forced palettes
    if cover_cfg.get("force_palette") == "ayurveda":
        top, bottom, accent = (128,169,132), (82,122,92), (196,220,198)
    elif cover_cfg.get("force_palette") == "tariff":
        top, bottom, accent = (44,110,168), (24,63,108), (158,210,255)

    im = _build_gradient((W,H), top, bottom).convert("RGBA")

    # Mandala motif for Ayurveda
    theme = _choose_theme(cfg, outline)
    if theme == "ayurveda":
        mandala_alpha = int(cover_cfg.get("mandala_strength", 46))
        mandala_scale = float(cover_cfg.get("mandala_scale", 0.9))
        im = Image.alpha_composite(im, _mandala_layer((W,H), accent, mandala_alpha, mandala_scale))

    # gentle vignette
    vign = float(cover_cfg.get("vignette_strength", 0.15))
    im = _vignette(im, strength=vign)

    # typesetting (minimal)
    draw = ImageDraw.Draw(im)
    margin_x = int(W * 0.10)
    max_title_w, max_title_h = (W - margin_x * 2), int(H * 0.24)
    title_font, wrapped_title = _auto_fit(draw, title, max_title_w, max_title_h, _font_script, start=190, min_size=64)

    # position ~ upper third
    tw, th = draw.multiline_textbbox((0,0), wrapped_title, font=title_font, spacing=6, align="center")[2:]
    tw -= 0; th -= 0
    tx, ty = (W - tw) // 2, int(H * 0.30) - th // 2

    # soft **light** halo for readability
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.ellipse([tx - 70, ty - 50, tx + tw + 70, ty + th + 70], fill=(255, 255, 255, 80))
    halo = halo.filter(ImageFilter.GaussianBlur(14))
    im = Image.alpha_composite(im, halo)

    # title
    td = ImageDraw.Draw(im)
    td.multiline_text((tx, ty), wrapped_title, font=title_font, fill=(255,255,255,245), align="center", spacing=6)

    # optional short subtitle (sans)
    if show_sub and subtitle:
        sub_font = _font_sans(max(34, int(title_font.size * 0.40)))
        sub_wrapped = _wrap_center(draw, subtitle, sub_font, W - margin_x * 2)
        sb = td.multiline_textbbox((0,0), sub_wrapped, font=sub_font, spacing=6, align="center")
        sw, sh = sb[2]-sb[0], sb[3]-sb[1]
        sx, sy = (W - sw)//2, ty + th + 24
        td.multiline_text((sx, sy), sub_wrapped, font=sub_font, fill=(238,240,248,235), align="center", spacing=6)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(out_path, quality=95)
