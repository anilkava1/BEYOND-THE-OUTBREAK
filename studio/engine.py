import math, random
import numpy as np
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1280, 720, 30
INK = (18, 12, 14)
ZSKIN = (138, 168, 112)
SKIN = (236, 222, 200)
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "assets", "fonts", "DejaVuSerif-Bold.ttf")

def load_font(size, path=None):
    """Bundled serif font. For Hindi/Devanagari captions drop a Devanagari .ttf into assets/fonts and pass its path."""
    try:
        return ImageFont.truetype(path or FONT, size)
    except Exception:
        return ImageFont.load_default()

f_cap = load_font(44)
f_day = load_font(64)
f_lab = load_font(22)

def lerp(a, b, t): return a + (b - a) * t
def clamp(t, a=0.0, b=1.0): return max(a, min(b, t))
def ease(t):
    t = clamp(t); return t * t * (3 - 2 * t)

# ---------- post-processing assets
_yy, _xx = np.mgrid[0:H, 0:W]
_r = np.sqrt(((_xx / W - 0.5) * 2) ** 2 * 0.9 + ((_yy / H - 0.5) * 2) ** 2 * 1.1)
VIG = (1 - 0.68 * np.clip((_r - 0.4) / 0.95, 0, 1) ** 1.5)[..., None].astype(np.float32)
GRAIN = np.random.RandomState(7).normal(0, 4.2, (6, H, W, 1)).astype(np.float32)

def vgrad(h, top, bot, w=W):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top)[None, None, :] * (1 - t) + np.array(bot)[None, None, :] * t
    return Image.fromarray(np.repeat(a, w, axis=1).astype("uint8"))

@lru_cache(maxsize=None)
def radial(r):
    r = max(2, int(r))
    y, x = np.ogrid[-r:r, -r:r]
    d = np.sqrt(x * x + y * y) / r
    a = np.clip(1 - d, 0, 1) ** 2
    return Image.fromarray((a * 255).astype("uint8"), "L")

def add_glow(glow, x, y, r, color, k=1.0):
    r = int(r)
    if r < 2: return
    spr = radial(r)
    mask = spr if k >= 0.999 else spr.point(lambda v: int(v * k))
    box = (int(x - r), int(y - r), int(x + r), int(y + r))
    region = glow.crop(box)
    lit = Image.composite(Image.new("RGB", mask.size, color), Image.new("RGB", mask.size, (0, 0, 0)), mask)
    glow.paste(ImageChops.add(region, lit), box[:2])

def add_mask_glow(glow, mask, color, k=1.0):
    if k != 1.0: mask = mask.point(lambda v: int(v * k))
    lit = Image.composite(Image.new("RGB", (W, H), color), Image.new("RGB", (W, H), (0, 0, 0)), mask)
    return ImageChops.add(glow, lit)

# ---------- characters
def person(d, x, y, s=1.0, flip=False, frame=0, phase=0.0, mood="calm", zombie=False,
           shirt=(150, 120, 90), pants=(50, 45, 60), arm_up=False, lean=0.0, glows=None,
           weapon=None, skin=None, hair=(70, 50, 40)):
    moving = mood != "calm"
    sw = math.sin(frame * 0.35 + phase) * (4 if zombie else 6) if moving else 0
    bob = math.sin(frame * 0.35 + phase) * 3 if moving else 0
    if zombie and not lean: lean = 0.14
    dr = -1 if flip else 1
    def P(px, py): return (x + dr * (px + lean * (40 - py)) * s, y + bob + py * s)
    def B(a, b):
        (x0, y0), (x1, y1) = a, b
        return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]
    lw = max(2, int(4 * s))
    sk = skin or (ZSKIN if zombie else SKIN)
    d.line([P(-8, 40), P(-8 - sw, 70)], fill=pants, width=int(9 * s))
    d.line([P(8, 40), P(8 + sw, 70)], fill=pants, width=int(9 * s))
    d.rounded_rectangle(B(P(-24, 5), P(24, 49)), radius=int(10 * s), fill=shirt, outline=INK, width=lw)
    if zombie:
        for (bx, by, br) in ((-8, 20, 6), (10, 34, 5), (2, 42, 4)):
            c = P(bx, by); d.ellipse([c[0] - br * s, c[1] - br * s, c[0] + br * s, c[1] + br * s], fill=(96, 18, 18))
        d.line([P(-24, 44), P(-18, 52), P(-10, 46), P(-2, 53), P(8, 47), P(16, 52), P(24, 46)], fill=INK, width=max(1, int(2 * s)))
        for a, b in (((22, 14), (64, 0)), ((18, 22), (58, 14))):
            d.line([P(*a), P(*b)], fill=INK, width=int(8 * s))
            d.line([P(*a), P(*b)], fill=sk, width=max(2, int(4 * s)))
    elif arm_up or weapon:
        tip = P(46, -34)
        d.line([P(22, 14), tip], fill=INK, width=int(7 * s))
        d.line([P(22, 14), tip], fill=sk, width=max(2, int(3 * s)))
        if weapon == "torch":
            top = P(50, -78)
            d.line([tip, top], fill=(90, 60, 40), width=max(2, int(5 * s)))
            fh = (16 + 5 * math.sin(frame * 0.8 + phase)) * s
            d.polygon([(top[0] - 9 * s, top[1]), (top[0], top[1] - fh * 1.6), (top[0] + 9 * s, top[1])], fill=(255, 150, 40))
            d.polygon([(top[0] - 4 * s, top[1]), (top[0], top[1] - fh), (top[0] + 4 * s, top[1])], fill=(255, 225, 120))
            if glows is not None: glows.append((top[0], top[1] - 10 * s, 170 * s, (255, 150, 60), 0.8))
        elif weapon == "bat":
            top = P(56, -80)
            d.line([tip, top], fill=(140, 100, 60), width=max(3, int(7 * s)))
    else:
        d.line([P(22, 14), P(34, 36)], fill=INK, width=int(6 * s))
    r = 24 * s; cx, cy = P(0, -10)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=sk, outline=INK, width=lw)
    d.chord([cx - r - 2, cy - r * 1.4, cx + r + 2, cy + r * 0.05], 180, 360, fill=hair, outline=INK, width=lw)
    for ex in (-8, 8):
        ecx, ecy = P(ex, -8)
        if zombie:
            d.ellipse([ecx - 6 * s, ecy - 6 * s, ecx + 6 * s, ecy + 6 * s], fill=(30, 10, 10))
            d.ellipse([ecx - 2.8 * s, ecy - 2.8 * s, ecx + 2.8 * s, ecy + 2.8 * s], fill=(255, 60, 45))
            if glows is not None: glows.append((ecx, ecy, max(10, 22 * s), (255, 40, 30), 0.95))
        else:
            rr = 2.6 * s; d.ellipse([ecx - rr, ecy - rr, ecx + rr, ecy + rr], fill=INK)
    mx, my = P(0, 7)
    if zombie:
        d.ellipse([mx - 8 * s, my - 5 * s, mx + 8 * s, my + 8 * s], fill=(35, 8, 8))
        d.polygon([(mx - 5 * s, my + 7 * s), (mx + 5 * s, my + 7 * s), (mx + 3 * s, my + 18 * s), (mx - 3 * s, my + 15 * s)], fill=(110, 14, 14))
        d.line([(mx - 6 * s, my - 2 * s), (mx + 6 * s, my - 2 * s)], fill=(225, 222, 200), width=max(1, int(2 * s)))
    elif mood == "shout":
        d.ellipse([mx - 6 * s, my - 5 * s, mx + 6 * s, my + 5 * s], fill=INK)
    else:
        d.arc(B(P(-6, 0), P(6, 10)), 0, 180, fill=INK, width=max(2, int(3 * s)))

def tone(lay, amb):
    r, g, b, a = lay.split()
    rgb = ImageChops.multiply(Image.merge("RGB", (r, g, b)), Image.new("RGB", lay.size, amb))
    return Image.merge("RGBA", (*rgb.split(), a))

def blur_layer(lay, rad): return lay.filter(ImageFilter.GaussianBlur(rad))

def new_layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))

# ---------- environment pieces
def stars(d, hy, n=130, seed=3):
    rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.randint(0, W), rnd.randint(0, int(hy * 0.8))
        c = rnd.randint(150, 230); r = rnd.choice((1, 1, 2))
        d.ellipse([x, y, x + r, y + r], fill=(c, c, min(255, c + 20)))

def moon(base, glow, x, y, r, col, gcol):
    d = ImageDraw.Draw(base)
    d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    for dx, dy, rr in ((-0.3, -0.2, 0.22), (0.25, 0.1, 0.16), (-0.1, 0.35, 0.12), (0.3, -0.35, 0.1)):
        d.ellipse([x + dx * r - rr * r, y + dy * r - rr * r, x + dx * r + rr * r, y + dy * r + rr * r],
                  fill=tuple(int(c * 0.82) for c in col))
    add_glow(glow, x, y, r * 3.4, gcol, 0.85)

def skyline(base_rgba, base_y, seed, hmin, hmax, wmin, wmax, color, win_prob=0.25, outline=False,
            win_col=(255, 200, 110), lit_out=None, ruin=0.0):
    d = ImageDraw.Draw(base_rgba)
    rnd = random.Random(seed)
    x = -30
    while x < W + 30:
        w = rnd.randint(wmin, wmax); h = rnd.randint(hmin, hmax)
        top = base_y - h
        pts = [(x, base_y), (x, top), (x + w, top), (x + w, base_y)]
        if ruin and rnd.random() < ruin:
            pts = [(x, base_y), (x, top), (x + w * 0.4, top + 25), (x + w * 0.6, top - 8), (x + w, top + 40), (x + w, base_y)]
        d.polygon(pts, fill=color, outline=INK if outline else None)
        if outline: d.line(pts + [pts[0]], fill=INK, width=3)
        if rnd.random() < 0.35:
            d.line([(x + w * 0.5, top), (x + w * 0.5, top - rnd.randint(20, 50))], fill=color, width=3)
        for wy in range(top + 16, base_y - 14, 28):
            for wx in range(x + 12, x + w - 16, 24):
                if rnd.random() < win_prob:
                    d.rectangle([wx, wy, wx + 11, wy + 15], fill=win_col)
                    if lit_out is not None and rnd.random() < 0.18: lit_out.append((wx + 5, wy + 8))
                elif rnd.random() < 0.5:
                    d.rectangle([wx, wy, wx + 11, wy + 15], fill=tuple(max(0, c - 18) for c in color))
        x += w + rnd.randint(-4, 14)

def make_fog(seed=5):
    rnd = random.Random(seed)
    m = Image.new("L", (W * 2, H), 0); d = ImageDraw.Draw(m)
    for _ in range(16):
        cx = rnd.randint(0, W * 2); cy = rnd.randint(int(H * 0.55), int(H * 0.97))
        rx = rnd.randint(220, 460); ry = rnd.randint(30, 85)
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=rnd.randint(90, 170))
    return m.filter(ImageFilter.GaussianBlur(42))

def apply_fog(img, fog, frame, color=(120, 132, 160), alpha=0.35, speed=0.8):
    off = int(frame * speed) % W
    m = fog.crop((off, 0, off + W, H)).point(lambda v: int(v * alpha))
    img.paste(Image.new("RGB", (W, H), color), (0, 0), m)

def street(d, y0, road=(26, 26, 32), walk=(44, 44, 54), seed=1, blood=6):
    rnd = random.Random(seed)
    d.rectangle([0, y0, W, y0 + 36], fill=walk)
    d.line([(0, y0 + 36), (W, y0 + 36)], fill=INK, width=3)
    d.rectangle([0, y0 + 36, W, H], fill=road)
    for x in range(40, W, 180):
        d.rectangle([x, y0 + 36 + (H - y0) * 0.62, x + 90, y0 + 36 + (H - y0) * 0.62 + 7], fill=(110, 100, 66))
    for _ in range(blood):
        bx = rnd.randint(40, W - 40); by = rnd.randint(y0 + 50, H - 30); br = rnd.randint(14, 44)
        d.ellipse([bx - br, by - br * 0.35, bx + br, by + br * 0.35], fill=(70, 12, 14))
    for _ in range(10):
        x1 = rnd.randint(0, W); y1 = rnd.randint(y0 + 50, H - 10)
        d.line([(x1, y1), (x1 + rnd.randint(-60, 60), y1 + rnd.randint(-8, 8)), (x1 + rnd.randint(-90, 90), y1 + rnd.randint(-10, 10))], fill=(14, 14, 18), width=2)

def lamp(base, glow, x, y, h=250, col=(255, 205, 120), power=0.6, r=230):
    d = ImageDraw.Draw(base)
    d.rectangle([x - 5, y - h, x + 5, y], fill=(18, 18, 22), outline=INK)
    d.line([(x, y - h), (x + 36, y - h)], fill=(18, 18, 22), width=8)
    d.rounded_rectangle([x + 22, y - h - 6, x + 52, y - h + 6], radius=4, fill=(255, 235, 170), outline=INK, width=3)
    add_glow(glow, x + 37, y - h, r, col, power)
    cone = Image.new("L", (W, H), 0)
    ImageDraw.Draw(cone).polygon([(x + 30, y - h + 6), (x + 44, y - h + 6), (x + 150, y), (x - 80, y)], fill=95)
    return cone.filter(ImageFilter.GaussianBlur(14))

def flame(d, x, y, s, frame, seed=0):
    w = 18 * s; h = (34 + 9 * math.sin(frame * 0.7 + seed) + 4 * math.sin(frame * 1.9 + seed * 2)) * s
    d.polygon([(x - w, y), (x - w * 0.5, y - h * 0.5), (x - w * 0.1, y - h), (x + w * 0.35, y - h * 0.58), (x + w, y)], fill=(255, 130, 30))
    d.polygon([(x - w * 0.55, y), (x - w * 0.1, y - h * 0.62), (x + w * 0.5, y)], fill=(255, 220, 100))

def barrel_fire(d, glow, x, y, s, frame, seed=0):
    d.rectangle([x - 22 * s, y - 40 * s, x + 22 * s, y], fill=(70, 50, 44), outline=INK, width=3)
    d.line([(x - 22 * s, y - 24 * s), (x + 22 * s, y - 24 * s)], fill=INK, width=2)
    flame(d, x, y - 40 * s, s * 1.3, frame, seed)
    fl = 0.8 + 0.2 * math.sin(frame * 0.9 + seed)
    add_glow(glow, x, y - 50 * s, 260 * s, (255, 140, 50), 0.85 * fl)

def wreck_car(d, x, y, s=1.0, col=(86, 70, 78)):
    d.rounded_rectangle([x, y - 60 * s, x + 230 * s, y - 15 * s], radius=int(14 * s), fill=col, outline=INK, width=4)
    d.polygon([(x + 50 * s, y - 60 * s), (x + 80 * s, y - 100 * s), (x + 160 * s, y - 100 * s), (x + 190 * s, y - 60 * s)], fill=col, outline=INK)
    d.polygon([(x + 62 * s, y - 62 * s), (x + 86 * s, y - 94 * s), (x + 118 * s, y - 94 * s), (x + 118 * s, y - 62 * s)], fill=(24, 28, 40))
    d.polygon([(x + 126 * s, y - 62 * s), (x + 126 * s, y - 94 * s), (x + 156 * s, y - 94 * s), (x + 178 * s, y - 62 * s)], fill=(24, 28, 40))
    for wx in (x + 40 * s, x + 185 * s):
        d.ellipse([wx - 22 * s, y - 36 * s, wx + 22 * s, y + 8 * s], fill=(14, 14, 16), outline=INK, width=3)

def crow(d, x, y, frame, s=1.0, phase=0.0):
    up = math.sin(frame * 0.5 + phase) * 14 * s
    d.polygon([(x, y), (x - 26 * s, y - 10 * s - up), (x - 10 * s, y + 3 * s)], fill=(10, 10, 14))
    d.polygon([(x, y), (x + 26 * s, y - 10 * s - up), (x + 10 * s, y + 3 * s)], fill=(10, 10, 14))
    d.ellipse([x - 7 * s, y - 3 * s, x + 7 * s, y + 6 * s], fill=(10, 10, 14))

# ---------- final pass
def screen(img_rgb, glow):
    a = np.asarray(img_rgb, dtype=np.float32); g = np.asarray(glow, dtype=np.float32)
    return 255 - (255 - a) * (255 - g) / 255.0

def post(img_rgb, glow, fidx, z=1.0, cx=W / 2, cy=H / 2, shake=0.0, flash=0.0, caption=None, calpha=1.0):
    comp = Image.fromarray(np.clip(screen(img_rgb, glow), 0, 255).astype("uint8"))
    if z != 1.0 or shake:
        bw, bh = W / z, H / z
        sx = (random.Random(fidx * 7).random() - 0.5) * shake; sy = (random.Random(fidx * 13).random() - 0.5) * shake
        x0 = clamp(cx - bw / 2 + sx, 0, W - bw); y0 = clamp(cy - bh / 2 + sy, 0, H - bh)
        comp = comp.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + bw, y0 + bh))
    arr = np.asarray(comp, dtype=np.float32) * VIG + GRAIN[fidx % 6]
    if flash: arr = arr * (1 - flash) + 255 * flash
    out = Image.fromarray(np.clip(arr, 0, 255).astype("uint8")).convert("RGBA")
    if caption and calpha > 0: draw_caption(out, caption, calpha)
    return out.convert("RGB")

def draw_caption(img, text, alpha, y0=56):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    bb = ld.textbbox((0, 0), text, font=f_cap); tw, th = bb[2] - bb[0], bb[3] - bb[1]
    bx = W // 2 - tw // 2 - 42
    ld.rounded_rectangle([bx, y0, bx + tw + 84, y0 + th + 40], radius=10, fill=(14, 8, 10, int(205 * alpha)),
                         outline=(205, 44, 40, int(255 * alpha)), width=3)
    ld.text((W // 2 - tw // 2, y0 + 16), text, font=f_cap, fill=(244, 230, 214, int(255 * alpha)))
    img.alpha_composite(layer)

def fade(local, dur, fi=14, fo=14):
    a = min(1, local / fi) if fi else 1
    b = min(1, (dur - local) / fo) if fo else 1
    return max(0.0, min(a, b))


# ---------- shared palettes / helpers the scenes can reuse
SHIRTS = [(150, 112, 82), (74, 100, 128), (136, 80, 70), (96, 124, 92), (120, 110, 130)]
PANTS_ = [(52, 46, 60), (44, 70, 90), (86, 64, 50)]

SKY = {  # (top, bottom) gradient presets; pick or invent your own per scene
    "night": ((6, 8, 24), (78, 44, 76)),
    "blood_dusk": ((12, 6, 16), (170, 66, 40)),
    "deep_night": ((4, 4, 14), (34, 24, 52)),
    "overcast": ((40, 44, 56), (120, 120, 130)),
    "day": ((120, 170, 220), (240, 225, 190)),
}

def crowd(d, cols, rows, x, y, gx, gy, s, seed, frame, flip=False, zombie=True, glows=None, mood="march"):
    """Grid of people with jitter. zombie=True gives green skin + glowing red eyes (appended to `glows`)."""
    rnd = random.Random(seed)
    for r in range(rows):
        for c in range(cols):
            dx = (rnd.random() - 0.5) * 18; dy = (rnd.random() - 0.5) * 10
            person(d, x + c * gx + dx, y + r * gy + dy, s * (0.9 + r * 0.07), flip, frame, phase=c * 0.8 + r * 1.4,
                   mood=mood, zombie=zombie, shirt=rnd.choice(SHIRTS), pants=rnd.choice(PANTS_), glows=glows,
                   lean=rnd.uniform(0.08, 0.3))

def dyn_glow(static_glow, glows):
    """Copy of the static glow layer plus per-frame lights [(x, y, r, color, k), ...]. Never draw per-frame lights on the static layer."""
    g = static_glow.copy()
    for (x, y, r, c, k) in glows: add_glow(g, x, y, r, c, k)
    return g

def plank(d, cx, cy, w, h, ang, col=(110, 80, 54)):
    c, s = math.cos(ang), math.sin(ang)
    pts = [(cx + (-w / 2) * c - (-h / 2) * s, cy + (-w / 2) * s + (-h / 2) * c), (cx + (w / 2) * c - (-h / 2) * s, cy + (w / 2) * s + (-h / 2) * c),
           (cx + (w / 2) * c - (h / 2) * s, cy + (w / 2) * s + (h / 2) * c), (cx + (-w / 2) * c - (h / 2) * s, cy + (-w / 2) * s + (h / 2) * c)]
    d.polygon(pts, fill=col, outline=INK)
