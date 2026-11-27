#!/usr/bin/env python3
"""BlobToon engine: story.json -> mp4 (shorts 9:16 up to 60s / long 16:9 up to 300s).
Deps: pillow, numpy, ffmpeg (CLI). No internet, no GPU, no API needed.
Characters are drawn from locked specs (characters.json) so they are IDENTICAL in every frame/shot."""
import argparse, json, math, os, subprocess, sys, wave, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
FONT = os.path.join(SKILL, "fonts", "Poppins-Bold.ttf")
CHARS = json.load(open(os.path.join(SKILL, "characters.json")))
ZOMBIES = [k for k, v in CHARS.items() if v.get("zombie")]
LIMITS = {"short": 60.0, "long": 300.0}

def hx(c): c = c.lstrip("#"); return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
def shade(c, f): return tuple(max(0, min(255, int(v * f))) for v in c)
def lerp(a, b, t): return a + (b - a) * t
def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def pop(x): x = max(0.0, min(1.0, x)); c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def font(sz):
    try: return ImageFont.truetype(os.environ.get("BLOBTOON_FONT", FONT), int(sz))
    except Exception: return ImageFont.load_default()

# ------------------------------------------------------------------ CHARACTER
_head = {}
def head_sprite(d, zom=False):
    if (d, zom) in _head: return _head[(d, zom)]
    yy, xx = np.mgrid[0:d, 0:d].astype(np.float32); c = (d - 1) / 2
    r = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / c
    dist = np.sqrt((xx - c + 0.35 * c) ** 2 + (yy - c + 0.4 * c) ** 2) / c
    base = np.clip(1 - dist / 1.25, 0, 1) ** 1.8
    rim = np.clip((r - 0.84) / 0.16, 0, 1) * np.clip(((xx - c) + (yy - c)) / c * 0.55, 0, 1) * 34
    a = np.clip((1 - r) * c, 0, 1) * 255
    if zom:
        v = np.clip(34 + base * 120 + rim, 0, 255); chans = [v * 0.62, v * 0.86, v * 0.55, a]
    else:
        v = np.clip(13 + base * 60 + rim, 0, 255); chans = [v, v, v * 1.1, a]
    im = Image.fromarray(np.dstack(chans).clip(0, 255).astype(np.uint8), "RGBA")
    sp = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    ImageDraw.Draw(sp).ellipse([c * 0.42, c * 0.2, c * 0.95, c * 0.62], fill=(255, 255, 255, 62))
    sp = sp.filter(ImageFilter.GaussianBlur(d * 0.035))
    im = Image.alpha_composite(im, sp)
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    _head[(d, zom)] = im
    return im

EXPR = {
    "neutral":   dict(es=1.0,  lid=(0, 0),       mouth="smile_small", blush=0, pr=1.0),
    "happy":     dict(es=0.92, lid=(0, 0),       mouth="smile_open",  blush=1, pr=1.0),
    "sad":       dict(es=1.0,  lid=(0.5, 0.05),  mouth="frown",       blush=0, pr=1.0),
    "angry":     dict(es=0.95, lid=(0.05, 0.5),  mouth="frown_flat",  blush=0, pr=1.0),
    "surprised": dict(es=1.25, lid=(0, 0),       mouth="o",           blush=0, pr=0.7),
    "worried":   dict(es=1.05, lid=(0.35, 0.0),  mouth="wavy",        blush=0, pr=0.9),
    "smug":      dict(es=1.0,  lid=(0.5, 0.5),   mouth="smirk",       blush=1, pr=1.0),
    "sleepy":    dict(es=0.9,  lid=(0.6, 0.6),   mouth="flat",        blush=0, pr=1.0),
    "scared":    dict(es=1.2,  lid=(0.3, 0.0),   mouth="wavy",        blush=0, pr=0.6),
    "terrified": dict(es=1.4,  lid=(0, 0),       mouth="o",           blush=0, pr=0.45),
    "determined": dict(es=0.95, lid=(0.0, 0.35), mouth="frown_flat",  blush=0, pr=1.0),
    "zombie":    dict(es=1.0,  lid=(0.25, 0.0),  mouth="jagged",      blush=0, pr=0.8),
    "groan":     dict(es=1.0,  lid=(0.25, 0.0),  mouth="groan",       blush=0, pr=0.8),
}
LOOK = {"center": (0, 0), "camera": (0, 0), "left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1),
        "up_left": (-1, -1), "up_right": (1, -1)}
# hand targets relative to shoulder in head-diameter units: (outward, down). front = arms drawn over the head
POSES = {
    "idle":   dict(L=(0.16, 0.62), R=(0.16, 0.62)),
    "wave":   dict(L=(0.16, 0.62), R=(0.36, -0.40), front="R"),
    "think":  dict(L=(0.16, 0.62), R=(-0.12, 0.02), front="R"),
    "point":  dict(L=(0.16, 0.62), R=(0.64, 0.05)),
    "shrug":  dict(L=(0.42, 0.22), R=(0.42, 0.22)),
    "cheer":  dict(L=(0.38, -0.52), R=(0.38, -0.52), front="LR"),
    "stress": dict(L=(0.30, -0.20), R=(0.30, -0.20), front="LR"),
    "sit":    dict(L=(0.10, 0.50), R=(0.10, 0.50), legf=0.5),
    "walk":   dict(L=(0.16, 0.62), R=(0.16, 0.62)),
    "talk":   dict(L=(0.16, 0.62), R=(0.30, 0.30)),
    "run":    dict(L=(0.12, 0.50), R=(0.12, 0.50)),
    "zwalk":  dict(L=(0.42, -0.12), R=(0.42, -0.12)),
    "cower":  dict(L=(-0.18, -0.43), R=(-0.18, -0.43), front="LR"),
    "defend": dict(L=(0.05, 0.35), R=(0.30, -0.50), front="R"),
}
FX = ("shake", "flicker", "red_alert", "fog")
PROPS = ("none", "bat", "flashlight")

def ik(S, H, l1, l2, side):
    dx, dy = H[0] - S[0], H[1] - S[1]; d = math.hypot(dx, dy); mx = (l1 + l2) * 0.985
    if d > mx: dx, dy = dx * mx / d, dy * mx / d; d = mx
    d = max(d, 1e-4); ux, uy = dx / d, dy / d
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d); h = math.sqrt(max(0, l1 * l1 - a * a))
    bx, by = S[0] + ux * a, S[1] + uy * a
    c1 = (bx - uy * h, by + ux * h); c2 = (bx + uy * h, by - ux * h)
    return (c1 if c1[0] * side > c2[0] * side else c2), (S[0] + dx, S[1] + dy)

def draw_char(spec, st, D):
    """Draw one character. D = head diameter in px. Returns (RGBA image, (anchor_x, anchor_y)=ground point)."""
    SS = 2; d = max(8, int(D * SS)); U = d
    Wc, Hc = int(3.4 * d), int(3.0 * d); ox, oy = Wc // 2, int(2.65 * d)
    im = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    P = lambda x, y: (ox + x * U, oy + y * U)
    def ell(cx, cy, rx, ry, fill): g.ellipse([*P(cx - rx, cy - ry), *P(cx + rx, cy + ry)], fill=fill)
    def tube(pts, w, fill):
        for a, b in zip(pts, pts[1:]): g.line([P(*a), P(*b)], fill=fill, width=max(1, int(w * U)))
        for p in pts: ell(p[0], p[1], w / 2, w / 2, fill)
    col = hx(spec["color"]); suit = spec["outfit"] == "suit"; lab = spec["outfit"] == "labcoat"; zb = bool(spec.get("zombie"))
    ex = EXPR.get(st.get("expr", "neutral"), EXPR["neutral"])
    pose = POSES.get(st.get("pose", "idle"), POSES["idle"]); t = st.get("t", 0.0)
    legf = pose.get("legf", 1.0); legs_len = 0.95 * legf
    bob = st.get("bob", 0.0); hipy = -legs_len + bob * 0.5; top = hipy - 0.55
    hcx, hcy = st.get("tilt", 0.0) * 0.03, top - 0.30 + bob * 0.6; R = 0.5
    hair = spec.get("hair", "none"); hc = hx(spec["hair_color"]) if spec.get("hair_color") else None
    ph = st.get("walk", None)
    # back hair
    if hair == "bob": ell(hcx, hcy + 0.07, 0.57, 0.56, hc)
    # legs
    legc = hx(spec["legs"]); shoe = hx(spec["shoes"])
    for side in (-1, 1):
        lift = 0.0
        if ph is not None: lift = max(0, math.sin(ph) * -side) * (0.24 if st.get("run") else 0.14)
        sw = (math.sin(t * 3 + side) * 0.03) if legf < 1 else 0
        fx, fy = side * 0.17 + sw, -lift
        tube([(side * 0.14, hipy), (fx, fy - 0.03)], 0.085, legc)
        ell(fx + side * 0.015, fy - 0.035, 0.13, 0.06, shoe); ell(fx + side * 0.015, fy - 0.01, 0.13, 0.03, shade(shoe, 0.72))
    # torso
    g.rounded_rectangle([*P(-0.30, top), *P(0.30, hipy + 0.03)], radius=int(0.14 * U), fill=col)
    if lab:
        g.polygon([P(-0.12, top + 0.02), P(0.12, top + 0.02), P(0, top + 0.30)], fill=(90, 150, 200))
        g.line([P(0, top + 0.1), P(0, hipy)], fill=(190, 200, 210), width=max(1, int(0.02 * U)))
        g.rounded_rectangle([*P(-0.2, hipy - 0.2), *P(-0.06, hipy - 0.08)], radius=int(0.03 * U), fill=shade(col, 0.92))
    elif suit:
        g.polygon([P(-0.11, top + 0.02), P(0.11, top + 0.02), P(0, top + 0.26)], fill=(240, 240, 244))
        g.polygon([P(-0.035, top + 0.07), P(0.035, top + 0.07), P(0.045, top + 0.3), P(0, top + 0.36), P(-0.045, top + 0.3)], fill=(200, 45, 50))
    else:
        ell(0, top + 0.05, 0.30, 0.12, shade(col, 0.82))
        for sx in (-0.08, 0.08): g.line([P(sx, top + 0.12), P(sx, top + 0.30)], fill=(250, 250, 250), width=max(1, int(0.022 * U)))
        g.rounded_rectangle([*P(-0.19, hipy - 0.19), *P(0.19, hipy - 0.06)], radius=int(0.06 * U), fill=shade(col, 0.9))
    if zb:
        dk = shade(col, 0.5); wc = max(1, int(0.015 * U))
        g.polygon([P(-0.28, hipy - 0.02), P(-0.20, hipy - 0.12), P(-0.14, hipy - 0.02), P(-0.08, hipy - 0.13), P(-0.02, hipy - 0.02)], fill=dk)
        g.polygon([P(0.08, top + 0.20), P(0.28, top + 0.16), P(0.20, top + 0.28), P(0.26, top + 0.38), P(0.10, top + 0.30)], fill=dk)
        for sx_, sy_ in ((-0.12, top + 0.28), (0.05, top + 0.42)):
            g.line([P(sx_ - 0.04, sy_ - 0.04), P(sx_ + 0.04, sy_ + 0.04)], fill=(210, 205, 190), width=wc); g.line([P(sx_ + 0.04, sy_ - 0.04), P(sx_ - 0.04, sy_ + 0.04)], fill=(210, 205, 190), width=wc)
    # arms (behind head unless raised)
    hands = {}; hand_c = (96, 130, 84) if zb else (14, 14, 18)
    def arm(key, side):
        sh = (side * 0.30, top + 0.10); o, dn = pose[key]
        if pose is POSES["walk"] or ph is not None: o += 0.05; dn += math.sin(ph + (0 if side < 0 else math.pi)) * (0.22 if st.get("run") else 0.1) if ph is not None else 0
        if pose.get("wave") == key[0] or (key == "R" and pose is POSES["talk"]): o += 0.1 * math.sin(t * 9) if pose.get("wave") else 0.06 * math.sin(t * 5); dn += 0.0 if pose.get("wave") else 0.05 * math.cos(t * 4)
        E, Hd = ik(sh, (sh[0] + side * o, sh[1] + dn), 0.34, 0.34, side)
        hands[key] = Hd
        return lambda: (tube([sh, E, Hd], 0.105, col), ell(Hd[0], Hd[1], 0.078, 0.078, hand_c))
    arms = {"L": arm("L", -1), "R": arm("R", 1)}
    front = pose.get("front", "")
    for k in "LR":
        if k not in front: arms[k]()
    # head
    hs = head_sprite(d, zb)
    im.alpha_composite(hs, dest=(int(ox + hcx * U - d / 2), int(oy + hcy * U - d / 2)))
    # face
    bl = 0.1 if ((t + st.get("phase", 0.0)) % 3.3) < 0.13 else 1.0
    es = ex["es"] * bl; ers = (0.125, 0.15 * es); look = LOOK.get(st.get("look", "center"), (0, 0))
    for side in (-1, 1):
        cx, cy = hcx + side * 0.185, hcy - 0.03
        zs = (1.15 if side == -1 else 0.85) if zb else 1.0
        ell(cx, cy, ers[0] * zs, ers[1] * zs, (232, 236, 130) if zb else (250, 250, 250))
        if bl > 0.5:
            pr = (0.045 if zb else 0.062) * ex["pr"]; px, py = cx + look[0] * 0.045, cy + look[1] * 0.05
            if zb: px, py = cx + side * 0.03, cy + 0.02
            ell(px, py, pr, pr * 1.1, (150, 20, 22) if zb else (14, 14, 18)); ell(px - 0.02, py - 0.025, 0.02, 0.02, (255, 255, 255))
        oc, ic = ex["lid"]
        if side == 1: oc, ic = oc, ic
        if oc or ic:
            tp = cy - ers[1]; hh = 2 * ers[1]; x0, x1 = cx - ers[0] - 0.02, cx + ers[0] + 0.02
            yl, yr = (tp + oc * hh, tp + ic * hh) if side == -1 else (tp + ic * hh, tp + oc * hh)
            g.polygon([P(x0, tp - 0.04), P(x1, tp - 0.04), P(x1, yr), P(x0, yl)], fill=(24, 24, 30))
    pink = (210, 214, 190) if zb else (244, 146, 160); mx, my = hcx, hcy + 0.21; m = ex["mouth"]
    if st.get("talk"):
        o = abs(math.sin(t * 11.0)) * 0.7 + 0.15
        ell(mx, my + 0.02, 0.06, 0.018 + 0.05 * o, pink)
    elif m == "smile_small": g.arc([*P(mx - 0.07, my - 0.07), *P(mx + 0.07, my + 0.04)], 20, 160, fill=pink, width=max(2, int(0.025 * U)))
    elif m == "smile_open": g.chord([*P(mx - 0.09, my - 0.07), *P(mx + 0.09, my + 0.07)], 0, 180, fill=pink)
    elif m == "o": ell(mx, my + 0.02, 0.04, 0.055, pink)
    elif m == "frown": g.arc([*P(mx - 0.07, my), *P(mx + 0.07, my + 0.1)], 200, 340, fill=pink, width=max(2, int(0.025 * U)))
    elif m == "frown_flat": g.line([P(mx - 0.06, my + 0.03), P(mx + 0.06, my + 0.03)], fill=pink, width=max(2, int(0.028 * U)))
    elif m == "wavy": g.line([P(mx - 0.08, my + 0.03), P(mx - 0.04, my), P(mx, my + 0.04), P(mx + 0.04, my), P(mx + 0.08, my + 0.03)], fill=pink, width=max(2, int(0.022 * U)))
    elif m == "smirk": g.arc([*P(mx - 0.02, my - 0.07), *P(mx + 0.12, my + 0.04)], 10, 150, fill=pink, width=max(2, int(0.025 * U)))
    elif m == "jagged": g.line([P(mx - 0.1, my + 0.02), P(mx - 0.06, my + 0.06), P(mx - 0.02, my), P(mx + 0.02, my + 0.06), P(mx + 0.06, my), P(mx + 0.1, my + 0.05)], fill=pink, width=max(2, int(0.024 * U)))
    elif m == "groan":
        ell(mx, my + 0.04, 0.09, 0.08, (58, 18, 20))
        for tx_ in (-0.05, -0.0, 0.05): g.polygon([P(tx_ - 0.02, my - 0.03), P(tx_ + 0.02, my - 0.03), P(tx_, my + 0.02)], fill=(235, 235, 215))
    else: g.line([P(mx - 0.05, my + 0.03), P(mx + 0.05, my + 0.03)], fill=pink, width=max(2, int(0.022 * U)))
    if spec.get("glasses"):
        for side in (-1, 1): g.ellipse([*P(hcx + side * 0.185 - 0.16, hcy - 0.03 - 0.18), *P(hcx + side * 0.185 + 0.16, hcy - 0.03 + 0.18)], outline=(222, 232, 246), width=max(2, int(0.025 * U)))
        g.line([P(hcx - 0.03, hcy - 0.05), P(hcx + 0.03, hcy - 0.05)], fill=(222, 232, 246), width=max(2, int(0.025 * U)))
    if ex["blush"]:
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for s in (-1, 1): od.ellipse([*P(hcx + s * 0.29 - 0.075, hcy + 0.13), *P(hcx + s * 0.29 + 0.075, hcy + 0.2)], fill=(255, 110, 140, 95))
        im.alpha_composite(ov.filter(ImageFilter.GaussianBlur(U * 0.012)))
    # hair / hats (front)
    def chord_cap(a0, a1, rr, fill):
        g.chord([*P(hcx - rr, hcy - rr), *P(hcx + rr, hcy + rr)], a0, a1, fill=fill)
    if hair == "bob": chord_cap(200, 340, 0.53, hc)
    elif hair == "curly":
        chord_cap(205, 335, 0.5, hc)
        for a in range(190, 351, 16):
            ell(hcx + 0.48 * math.cos(math.radians(a)), hcy + 0.48 * math.sin(math.radians(a)), 0.15, 0.15, hc)
    elif hair == "beanie":
        chord_cap(197, 343, 0.54, hc); g.line([P(hcx - 0.50, hcy - 0.155), P(hcx + 0.50, hcy - 0.155)], fill=shade(hc, 0.78), width=int(0.075 * U))
        ell(hcx, hcy - 0.56, 0.08, 0.08, shade(hc, 1.15))
    elif hair == "cap":
        chord_cap(197, 343, 0.53, hc); ell(hcx, hcy - 0.17, 0.46, 0.05, shade(hc, 0.75))
    for k in "LR":
        if k in front: arms[k]()
    prop = st.get("prop")
    if prop and "R" in hands:
        hx_, hy_ = hands["R"]
        if prop == "bat":
            tube([(hx_ - 0.05, hy_ + 0.12), (hx_ + 0.14, hy_ - 0.62)], 0.085, (156, 108, 62)); tube([(hx_ + 0.12, hy_ - 0.52), (hx_ + 0.14, hy_ - 0.62)], 0.11, (130, 88, 50))
            ell(hx_, hy_, 0.078, 0.078, hand_c)
        elif prop == "flashlight":
            tube([(hx_ - 0.02, hy_), (hx_ + 0.22, hy_ - 0.06)], 0.09, (70, 74, 84)); ell(hx_ + 0.24, hy_ - 0.065, 0.06, 0.06, (255, 250, 200))
            cone = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(cone).polygon([P(hx_ + 0.26, hy_ - 0.07), P(hx_ + 0.7, hy_ - 0.32), P(hx_ + 0.7, hy_ + 0.2)], fill=(255, 245, 170, 70))
            im.alpha_composite(cone.filter(ImageFilter.GaussianBlur(U * 0.03))); ell(hx_, hy_, 0.078, 0.078, hand_c)
    im = im.reduce(SS)
    if st.get("flip"): im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im, (ox / SS, oy / SS)

# ------------------------------------------------------------------ LOCATIONS
class Cv:
    def __init__(s, W, H): s.W, s.H, s.m = W, H, min(W, H); s.im = Image.new("RGB", (W, H)); s.d = ImageDraw.Draw(s.im, "RGBA")
    def grad(s, y0, y1, c0, c1):
        a, b = int(y0 * s.H), int(y1 * s.H); h = max(1, b - a); t = np.linspace(0, 1, h)[:, None, None]
        arr = (np.array(c0)[None, None, :] * (1 - t) + np.array(c1)[None, None, :] * t) * np.ones((1, s.W, 1))
        s.im.paste(Image.fromarray(arr.astype(np.uint8)), (0, a))
    def r(s, x0, y0, x1, y1, f, rad=0):
        b = [x0 * s.W, y0 * s.H, x1 * s.W, y1 * s.H]
        (s.d.rounded_rectangle(b, radius=rad * s.m, fill=f) if rad else s.d.rectangle(b, fill=f))
    def c(s, x, y, rr, f): s.d.ellipse([x * s.W - rr * s.m, y * s.H - rr * s.m, x * s.W + rr * s.m, y * s.H + rr * s.m], fill=f)
    def e(s, x0, y0, x1, y1, f): s.d.ellipse([x0 * s.W, y0 * s.H, x1 * s.W, y1 * s.H], fill=f)
    def p(s, pts, f): s.d.polygon([(x * s.W, y * s.H) for x, y in pts], fill=f)
    def glow(s, x, y, rr, col, a=110):
        ov = Image.new("RGBA", (s.W, s.H), (0, 0, 0, 0)); ImageDraw.Draw(ov).ellipse([x * s.W - rr * s.m, y * s.H - rr * s.m, x * s.W + rr * s.m, y * s.H + rr * s.m], fill=(*col, a))
        ov = ov.filter(ImageFilter.GaussianBlur(rr * s.m * 0.45)); s.im.paste(ov, (0, 0), ov); s.d = ImageDraw.Draw(s.im, "RGBA")
    def bust(s, x, y, rr, col):
        cx, cy, r_ = x * s.W, y * s.H, rr * s.m
        s.d.rounded_rectangle([cx - r_, cy + r_ * .7, cx + r_, cy + r_ * 2.5], radius=r_ * .5, fill=col)
        s.d.ellipse([cx - r_, cy - r_, cx + r_, cy + r_], fill=(24, 24, 30))
        for sd in (-1, 1):
            ex_ = cx + sd * r_ * .36; s.d.ellipse([ex_ - r_ * .2, cy - r_ * .35, ex_ + r_ * .2, cy + r_ * .12], fill=(246, 246, 246)); s.d.ellipse([ex_ - r_ * .09, cy - r_ * .2, ex_ + r_ * .09, cy + r_ * .06], fill=(16, 16, 20))

HOOD = [(63, 111, 184), (232, 116, 154), (47, 163, 154), (238, 138, 46), (150, 110, 200), (120, 170, 80), (242, 184, 28)]
def crowd(c, y0, y1, rows, n, rr, seed=3, dark=False):
    rnd = random.Random(seed)
    for i in range(rows):
        y = lerp(y0, y1, i / max(1, rows - 1)); 
        for k in range(n + i):
            x = (k + 0.5 + rnd.uniform(-.2, .2)) / (n + i)
            col = HOOD[rnd.randrange(len(HOOD))]; col = shade(col, 0.55 if dark else 0.95)
            c.bust(x, y + rnd.uniform(-.004, .004), rr * (1 + 0.25 * i / max(1, rows)), col)

def L_bedroom_night(W, H):
    c = Cv(W, H); c.grad(0, .7, (52, 48, 100), (92, 72, 124)); c.grad(.7, 1, (96, 64, 54), (70, 46, 42))
    c.r(.07, .10, .44, .40, (210, 200, 222)); c.r(.09, .12, .42, .38, (20, 28, 72)); c.c(.34, .19, .032, (250, 244, 200))
    rnd = random.Random(5)
    for _ in range(14): c.c(rnd.uniform(.1, .4), rnd.uniform(.13, .36), .004, (255, 255, 255, 200))
    c.r(.25, .12, .26, .38, (210, 200, 222)); c.r(.09, .24, .42, .25, (210, 200, 222))
    c.r(.60, .14, .88, .34, (245, 225, 200)); c.c(.74, .24, .06, (240, 140, 120)); c.r(.64, .17, .68, .21, (90, 170, 200))
    c.r(.50, .50, 1.0, .72, (84, 112, 170), .02); c.r(.50, .46, .66, .53, (240, 240, 248), .02); c.r(.50, .72, 1.0, .75, (60, 80, 130))
    c.r(.0, .55, .42, .575, (150, 100, 70)); c.r(.03, .575, .045, .74, (120, 80, 56)); c.r(.37, .575, .385, .74, (120, 80, 56))
    c.glow(.28, .50, .22, (255, 214, 130), 120); c.r(.14, .47, .30, .55, (60, 62, 80), .01); c.r(.15, .48, .29, .54, (150, 210, 255)); c.r(.075, .40, .085, .55, (200, 170, 100)); c.p([(.04, .40), (.12, .40), (.10, .35), (.06, .35)], (255, 220, 130))
    return c, .86
def L_classroom(W, H):
    c = Cv(W, H); c.grad(0, .7, (240, 230, 200), (232, 216, 184)); c.grad(.7, 1, (212, 176, 130), (180, 140, 100))
    c.r(.04, .09, .34, .36, (150, 100, 66)); c.r(.055, .105, .325, .345, (176, 214, 242)); c.c(.2, .3, .09, (110, 170, 90)); c.r(.19, .105, .195, .345, (150, 100, 66))
    c.r(.40, .09, .96, .36, (140, 96, 64)); c.r(.415, .105, .945, .345, (52, 100, 80)); 
    for i, w in enumerate((.3, .22, .35)): c.r(.44, .15 + i * .06, .44 + w, .162 + i * .06, (235, 235, 225, 200))
    c.r(.0, .38, .1, .5, (230, 150, 100)); 
    for i in range(5): c.r(.01 + i * .018, .39, .02 + i * .018, .43, [(240, 200, 60), (100, 170, 220), (230, 110, 130), (120, 190, 120), (200, 150, 220)][i])
    crowd(c, .5, .58, 2, 6, .034, 11)
    for i in range(3): c.r(.04 + i * .33, .6, .3 + i * .33, .625, (190, 140, 96)); c.r(.07 + i * .33, .625, .08 + i * .33, .72, (110, 110, 120)); c.r(.26 + i * .33, .625, .27 + i * .33, .72, (110, 110, 120))
    return c, .88
def L_living_room(W, H):
    c = Cv(W, H); c.grad(0, .7, (240, 218, 200), (228, 200, 182)); c.grad(.7, 1, (176, 128, 92), (140, 98, 70))
    for i in range(0, 20): c.r(i * .05, 0, i * .05 + .012, .7, (255, 255, 255, 38))
    c.r(.08, .09, .42, .36, (190, 150, 110)); c.r(.095, .105, .405, .345, (150, 190, 230)); c.r(.095, .24, .405, .345, (112, 142, 190)); c.r(.24, .105, .25, .345, (190, 150, 110))
    c.r(.62, .12, .76, .26, (236, 176, 150)); c.c(.69, .19, .035, (250, 240, 220))
    c.r(.04, .50, .96, .70, (186, 138, 98), .03); c.r(.02, .46, .14, .72, (170, 122, 86), .03); c.r(.86, .46, .98, .72, (170, 122, 86), .03); c.r(.14, .50, .86, .58, (200, 154, 112), .02)
    c.r(.86, .62, .94, .72, (190, 100, 70)); c.e(.80, .38, 1.0, .64, (90, 150, 80)); c.e(.86, .30, 1.04, .56, (70, 130, 70))
    return c, .88
def L_street_sunset(W, H):
    c = Cv(W, H); c.grad(0, .62, (255, 196, 150), (250, 140, 130)); c.c(.5, .46, .12, (255, 236, 190, 230)); c.glow(.5, .46, .3, (255, 210, 150), 110)
    rnd = random.Random(8)
    for i in range(10):
        x = i * .105; h = rnd.uniform(.14, .34); c.r(x, .62 - h, x + .1, .66, (132, 104, 150))
        for k in range(int(h * 14)): 
            if rnd.random() < .5: c.r(x + .015 + (k % 3) * .03, .62 - h + .02 + (k // 3) * .04, x + .03 + (k % 3) * .03, .62 - h + .045 + (k // 3) * .04, (255, 224, 150))
    c.r(0, .66, 1, .72, (200, 180, 190)); c.grad(.72, 1, (92, 90, 110), (66, 64, 84))
    for i in range(6): c.r(.04 + i * .18, .9, .13 + i * .18, .91, (240, 220, 160))
    c.r(.1, .30, .115, .66, (60, 58, 80)); c.c(.107, .30, .02, (255, 230, 160)); c.glow(.107, .30, .1, (255, 220, 150), 90)
    c.e(.74, .40, 1.04, .67, (98, 150, 100)); c.r(.88, .56, .9, .68, (96, 72, 64))
    return c, .90
def L_cafe(W, H):
    c = Cv(W, H); c.grad(0, .66, (232, 200, 160), (220, 182, 142))
    for i in range(10): c.p([(i * .1, 0), (i * .1 + .1, 0), (i * .1 + .05, .06)], [(34, 150, 140), (220, 70, 60), (250, 240, 220)][i % 3])
    c.r(.52, .12, .94, .36, (110, 78, 56)); c.r(.54, .14, .92, .34, (46, 70, 62)); c.r(.58, .19, .8, .2, (240, 240, 230, 220)); c.r(.58, .25, .72, .26, (240, 240, 230, 220)); c.c(.86, .25, .03, (240, 240, 230, 200))
    c.r(0, .44, 1, .60, (176, 120, 80)); c.r(0, .44, 1, .46, (214, 160, 110)); c.r(.08, .33, .26, .44, (90, 90, 100), .01); c.c(.17, .36, .025, (210, 70, 60))
    for x in (.2, .5, .8): c.r(x - .003, .06, x + .003, .2, (60, 50, 50)); c.p([(x - .07, .26), (x + .07, .26), (x + .04, .2), (x - .04, .2)], (46, 140, 110)); c.glow(x, .26, .07, (255, 230, 150), 80)
    crowd(c, .5, .5, 1, 7, .03, 21)
    n = 8
    for rr in range(9):
        y0 = .64 + .36 * (rr / 9) ** 1.25; y1 = .64 + .36 * ((rr + 1) / 9) ** 1.25
        for k in range(14): 
            if (rr + k) % 2 == 0: c.r(k / 14, y0, (k + 1) / 14, y1, (40, 40, 48))
            else: c.r(k / 14, y0, (k + 1) / 14, y1, (244, 240, 232))
    return c, .90
def L_stage(W, H):
    c = Cv(W, H); c.grad(0, 1, (22, 12, 44), (74, 32, 96)); crowd(c, .42, .64, 5, 7, .028, 31, dark=True)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(ov).polygon([(.5 * W, 0), (.05 * W, .92 * H), (.95 * W, .92 * H)], fill=(255, 235, 255, 70)); ov = ov.filter(ImageFilter.GaussianBlur(W * .02)); c.im.paste(ov, (0, 0), ov); c.d = ImageDraw.Draw(c.im, "RGBA")
    c.r(0, .70, 1, 1, (64, 40, 98)); c.r(0, .70, 1, .715, (206, 150, 255)); c.glow(.5, .84, .3, (255, 220, 255), 90)
    c.r(.46, .0, .54, .03, (200, 200, 220)); c.glow(.1, .1, .12, (120, 200, 255), 60); c.glow(.9, .1, .12, (255, 120, 200), 60)
    return c, .90
def L_bus(W, H):
    c = Cv(W, H); c.grad(0, .75, (226, 232, 236), (206, 214, 222)); c.r(0, .20, 1, .48, (150, 190, 224)); c.e(.7, .26, 1.1, .5, (110, 170, 110))
    for i in range(5): c.r(.05 + i * .2, .36, .17 + i * .2, .48, (232, 190, 160)); c.p([(.04 + i * .2, .36), (.18 + i * .2, .36), (.11 + i * .2, .3)], (200, 90, 80))
    for i in range(6): c.r(i * .2 - .005, .20, i * .2 + .005, .48, (236, 236, 242)); 
    c.r(0, .18, 1, .2, (240, 190, 30)); c.r(0, .48, 1, .5, (236, 236, 242))
    for x in (.22, .78): c.r(x - .008, .18, x + .008, .90, (240, 190, 30))
    crowd(c, .56, .6, 1, 5, .03, 41)
    c.r(0, .62, .42, .84, (70, 92, 138), .02); c.r(.58, .62, 1, .84, (70, 92, 138), .02); c.grad(.75, 1, (150, 156, 166), (110, 116, 128)); c.r(.42, .75, .58, 1, (130, 136, 148))
    c.r(.0, .60, .42, .66, (88, 112, 160), .02); c.r(.58, .60, 1, .66, (88, 112, 160), .02)
    return c, .92
def L_park(W, H):
    c = Cv(W, H); c.grad(0, .6, (150, 206, 244), (222, 240, 250)); c.c(.8, .14, .06, (255, 246, 200)); 
    for x, y, s in ((.2, .15, .05), (.55, .1, .04), (.4, .25, .035)): c.e(x - s * 2, y, x + s * 2, y + s, (255, 255, 255, 230))
    c.e(-.2, .5, .6, .8, (126, 190, 120)); c.e(.3, .52, 1.3, .84, (110, 176, 108)); c.grad(.7, 1, (118, 186, 104), (88, 156, 84))
    c.r(.08, .35, .12, .72, (120, 84, 60)); c.c(.10, .30, .12, (84, 160, 90)); c.c(.2, .35, .08, (96, 172, 100)); c.c(.0, .36, .08, (96, 172, 100))
    c.r(.55, .60, .95, .64, (170, 120, 80)); c.r(.55, .54, .95, .57, (170, 120, 80)); c.r(.58, .64, .6, .72, (90, 70, 60)); c.r(.9, .64, .92, .72, (90, 70, 60))
    for k in range(16): c.c((k * .071 + .03) % 1, .78 + (k * .37 % .2), .008, [(255, 120, 150), (255, 220, 90), (255, 255, 255)][k % 3])
    return c, .90
def L_ruined_street(W, H):
    c = Cv(W, H); c.grad(0, .62, (46, 30, 48), (214, 96, 58)); c.glow(.2, .58, .34, (255, 140, 60), 120); c.c(.78, .2, .07, (250, 210, 170, 200))
    rnd = random.Random(14)
    for i in range(9):
        x = i * .12 - .02; h = rnd.uniform(.16, .40); w = .11
        c.p([(x, .66), (x, .66 - h), (x + w * .35, .66 - h - rnd.uniform(0, .04)), (x + w * .6, .66 - h + rnd.uniform(0, .05)), (x + w, .66 - h - rnd.uniform(0, .03)), (x + w, .66)], (42, 30, 46))
        for k in range(int(h * 10)):
            if rnd.random() < .3: c.r(x + .015 + (k % 3) * .03, .66 - h + .03 + (k // 3) * .045, x + .03 + (k % 3) * .03, .66 - h + .055 + (k // 3) * .045, (255, 190, 90, 220))
    for x, s_ in ((.3, .1), (.62, .13)): c.e(x - s_, .1, x + s_, .5, (70, 60, 70, 90))
    c.r(0, .66, 1, .72, (110, 96, 104)); c.grad(.72, 1, (74, 70, 84), (48, 46, 60))
    c.r(.58, .70, .98, .80, (150, 60, 54), .02); c.r(.64, .65, .90, .72, (130, 50, 46), .02); c.r(.66, .66, .72, .71, (150, 190, 210)); c.c(.66, .80, .04, (24, 24, 30)); c.c(.90, .80, .04, (24, 24, 30))
    c.r(.06, .30, .075, .66, (50, 48, 60)); c.glow(.068, .30, .08, (255, 200, 120), 60)
    return c, .91
def L_abandoned_school(W, H):
    c = Cv(W, H); c.grad(0, .72, (88, 94, 92), (70, 76, 78)); c.grad(.72, 1, (74, 66, 58), (46, 42, 40))
    for i in range(7): c.r(i * .15 + .02, .22, i * .15 + .13, .62, (70, 96, 120)); c.r(i * .15 + .02, .22, i * .15 + .13, .235, (50, 70, 92)); c.r(i * .15 + .07, .32, i * .15 + .075, .40, (30, 40, 50))
    c.r(.08, .06, .44, .20, (40, 44, 52)); c.p([(.1, .08), (.42, .08), (.30, .2), (.12, .2)], (170, 190, 220, 40))
    c.glow(.9, .05, .25, (255, 40, 40), 90); c.glow(.1, .05, .2, (255, 40, 40), 60)
    for k in range(6):
        x = .60 + (k % 3) * .12 - (k // 3) * .05; y = .66 - (k // 3) * .07
        c.r(x, y, x + .11, y + .03, (140, 100, 70)); c.r(x + .01, y + .03, x + .02, y + .08, (80, 80, 90)); c.r(x + .09, y + .03, x + .10, y + .08, (80, 80, 90))
    return c, .88
def L_supermarket(W, H):
    c = Cv(W, H); c.grad(0, .68, (214, 226, 214), (190, 204, 196)); c.grad(.68, 1, (200, 200, 196), (150, 152, 150)); c.r(0, 0, 1, .03, (240, 240, 236))
    for x in (.18, .5, .82): c.r(x - .09, .02, x + .09, .035, (255, 255, 230)); c.glow(x, .04, .1, (255, 255, 220), 80)
    rnd = random.Random(9)
    for row in range(3):
        y = .20 + row * .13; c.r(0, y + .1, 1, y + .12, (130, 130, 140))
        for k in range(18): c.r(k * .056 + .004, y + .02 + rnd.random() * .02, k * .056 + .05, y + .1, [(220, 80, 70), (240, 190, 60), (70, 160, 210), (110, 190, 110), (230, 230, 230)][rnd.randrange(5)])
    c.r(.04, .70, .2, .76, (150, 154, 164), .01); c.r(.05, .76, .19, .78, (90, 94, 104)); c.c(.07, .80, .016, (30, 30, 36)); c.c(.17, .80, .016, (30, 30, 36))
    return c, .90
def L_rooftop(W, H):
    c = Cv(W, H); c.grad(0, .7, (10, 14, 38), (60, 44, 80)); c.c(.78, .16, .09, (240, 236, 214)); c.glow(.78, .16, .3, (200, 210, 255), 70)
    rnd = random.Random(3)
    for i in range(10):
        x = i * .105; h = rnd.uniform(.12, .36); c.r(x, .72 - h, x + .1, .74, (22, 24, 44))
        for k in range(int(h * 12)):
            if rnd.random() < .35: c.r(x + .015 + (k % 3) * .03, .72 - h + .02 + (k // 3) * .045, x + .03 + (k % 3) * .03, .72 - h + .045 + (k // 3) * .045, (250, 190, 90, 200))
    c.glow(.3, .62, .12, (255, 120, 40), 140); c.glow(.8, .66, .1, (255, 120, 40), 120)
    c.grad(.74, 1, (74, 76, 92), (52, 54, 66)); c.r(0, .74, 1, .755, (110, 112, 128))
    c.r(.06, .60, .30, .74, (96, 100, 112), .01); c.r(.09, .62, .27, .64, (70, 74, 84))
    for k in range(10): c.r(k * .1 + .02, .66, k * .1 + .026, .74, (140, 142, 156))
    c.r(0, .66, 1, .672, (140, 142, 156))
    return c, .90
def L_lab(W, H):
    c = Cv(W, H); c.grad(0, .72, (44, 74, 78), (34, 58, 64)); c.grad(.72, 1, (92, 100, 104), (60, 66, 70))
    for i in range(4):
        x = .06 + i * .24; c.r(x, .12, x + .14, .46, (28, 44, 50), .02); c.r(x + .015, .14, x + .125, .44, (80, 230, 140, 190), .015); c.glow(x + .07, .3, .12, (80, 255, 150), 70)
        for k in range(4): c.c(x + .03 + k * .025, .22 + (k * .07) % .2, .008, (200, 255, 220, 200))
    c.r(0, .50, 1, .53, (150, 156, 160)); c.r(0, .53, 1, .68, (84, 92, 98))
    c.r(.1, .40, .22, .50, (20, 30, 34), .01); c.r(.11, .41, .21, .49, (60, 220, 140)); c.r(.7, .38, .88, .50, (20, 30, 34), .01); c.r(.71, .39, .87, .49, (60, 200, 220))
    for i in range(12): c.p([(i * .09, .94), (i * .09 + .045, .94), (i * .09 + .07, 1), (i * .09 + .025, 1)], (240, 200, 30))
    return c, .88

def L_hospital(W, H):
    c = Cv(W, H); c.grad(0, .72, (92, 110, 114), (60, 78, 84)); c.grad(.72, 1, (122, 130, 132), (80, 88, 92))
    for i in range(25): c.r(i * .04, .06, i * .04 + .0025, .62, (255, 255, 255, 14))
    for j in range(1, 6): c.r(0, .06 + j * .105, 1, .062 + j * .105, (255, 255, 255, 10))
    for i in range(4):
        x = .08 + i * .24; c.r(x, .025, x + .13, .05, (220, 238, 228)); c.glow(x + .065, .07, .10, (210, 255, 235), 45)
    c.r(.035, .13, .105, .175, (165, 40, 40)); c.glow(.07, .152, .045, (255, 60, 60), 65)
    c.r(.38, .30, .62, .48, (46, 66, 72)); c.r(.39, .315, .61, .465, (104, 156, 154))
    c.r(.41, .34, .59, .355, (196, 228, 222, 170)); c.glow(.5, .39, .09, (100, 240, 210), 40)
    c.r(.475, .19, .525, .205, (80, 200, 120)); c.r(.493, .165, .507, .23, (80, 200, 120))
    for x in (.02, .74):
        c.r(x, .10, x + .012, .50, (150, 170, 168)); c.r(x + .012, .12, x + .07, .50, (150, 190, 186, 105))
        c.r(x + .04, .54, x + .24, .59, (128, 138, 144)); c.r(x + .04, .59, x + .24, .62, (86, 96, 102))
        c.r(x + .05, .55, x + .23, .58, (222, 232, 232)); c.r(x + .055, .52, x + .10, .555, (236, 242, 242))
        c.r(x + .05, .62, x + .06, .71, (96, 104, 110)); c.r(x + .22, .62, x + .23, .71, (96, 104, 110))
        c.r(x + .27, .34, x + .276, .71, (180, 192, 198)); c.r(x + .255, .34, x + .292, .355, (200, 218, 218))
        c.r(x + .262, .355, x + .284, .41, (140, 230, 190, 180)); c.glow(x + .273, .41, .028, (120, 255, 200), 55)
    c.r(.60, .56, .72, .60, (150, 160, 166)); c.r(.61, .60, .71, .72, (90, 100, 106))
    c.c(.63, .74, .022, (40, 44, 50)); c.c(.69, .74, .022, (40, 44, 50))
    c.c(.30, .78, .035, (54, 62, 68)); c.c(.35, .78, .035, (54, 62, 68))
    c.r(.285, .70, .355, .735, (70, 80, 86)); c.r(.29, .64, .30, .71, (70, 80, 86))
    for k in range(14): c.r(0, .73 + k * .02, 1, .731 + k * .02, (255, 255, 255, 12))
    c.glow(.5, .82, .22, (110, 230, 200), 18)
    return c, .88

def L_hospital_hall(W, H):
    c = Cv(W, H); c.grad(0, .70, (64, 80, 86), (44, 58, 64)); c.grad(.70, 1, (98, 106, 110), (62, 68, 72))
    c.p([(0, 0), (1, 0), (.64, .30), (.36, .30)], (96, 110, 114))
    c.p([(0, 1), (1, 1), (.64, .64), (.36, .64)], (108, 116, 118))
    c.p([(0, 0), (.36, .30), (.36, .64), (0, 1)], (72, 88, 94))
    c.p([(1, 0), (.64, .30), (.64, .64), (1, 1)], (58, 72, 78))
    for i in range(1, 9):
        t = i / 9; y = .64 + .36 * t; x0 = .36 * (1 - t); x1 = 1 - .36 * (1 - t)
        c.r(x0, y, x1, y + .0025, (255, 255, 255, 16))
    for i, (x, y, w) in enumerate(((.44, .035, .12), (.46, .10, .08), (.475, .155, .05), (.487, .195, .026))):
        c.r(x, y, x + w, y + .012, (220, 238, 228)); c.glow(x + w / 2, y + .022, .08 - i * .014, (210, 255, 235), 50)
    for i, t in enumerate((.06, .20, .36, .54)):
        x = .015 + i * .075; y0 = .18 + i * .035; y1 = .58 + i * .012
        c.r(x, y0, x + .05, y1, (52, 66, 72)); c.r(x + .008, y0 + .02, x + .042, y0 + .12, (120, 160, 170, 85))
        x2 = .935 - i * .075
        c.r(x2, y0, x2 + .05, y1, (46, 60, 66)); c.r(x2 + .008, y0 + .02, x2 + .042, y0 + .12, (120, 160, 170, 75))
    c.r(.44, .34, .56, .64, (38, 50, 56)); c.r(.445, .35, .555, .64, (70, 86, 92)); c.r(.497, .35, .503, .64, (30, 40, 46))
    c.r(.46, .27, .54, .30, (170, 40, 40)); c.glow(.5, .285, .05, (255, 50, 50), 85)
    c.r(.72, .70, .94, .74, (150, 160, 166)); c.r(.74, .74, .92, .76, (90, 98, 104))
    c.c(.75, .80, .035, (40, 44, 50)); c.c(.90, .80, .035, (40, 44, 50))
    c.glow(.5, .85, .25, (110, 230, 200), 16)
    return c, .88

LOCS = {"ruined_street": L_ruined_street, "abandoned_school": L_abandoned_school, "supermarket": L_supermarket, "rooftop": L_rooftop, "lab": L_lab,
        "hospital": L_hospital, "hospital_hall": L_hospital_hall,
        "bedroom_night": L_bedroom_night, "classroom": L_classroom, "living_room": L_living_room, "street_sunset": L_street_sunset,
        "cafe": L_cafe, "stage": L_stage, "bus": L_bus, "park": L_park}
_bg = {}
def get_bg(name, W, H, grade="none"):
    k = (name, W, H, grade)
    if k not in _bg:
        c, gy = LOCS[name](W, H); im = c.im.filter(ImageFilter.GaussianBlur(W * 0.0016))
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); v = 1 - 0.22 * (((xx / W - .5) ** 2 + (yy / H - .5) ** 2) * 2.2)
        arr = np.asarray(im).astype(np.float32) * v[..., None]
        if grade == "horror":
            gray = arr.mean(axis=2, keepdims=True); arr = (gray * 0.35 + arr * 0.65) * np.array([0.82, 0.95, 0.86]) * 0.92
        im = Image.fromarray(arr.clip(0, 255).astype(np.uint8)); _bg[k] = (im, gy)
    return _bg[k]

# ------------------------------------------------------------------ OVERLAYS
def wrap(text, f, maxw):
    dm = ImageDraw.Draw(Image.new("L", (1, 1))); lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if dm.textlength(t, font=f) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w
    return lines + [cur]
def make_cloud(text, fs, maxw):
    f = font(fs); lines = wrap(text, f, maxw); dm = ImageDraw.Draw(Image.new("L", (1, 1)))
    lw = max(dm.textlength(l, font=f) for l in lines); lh = int(fs * 1.28); pad = int(fs * .75)
    w, h = int(lw + 2 * pad), int(lh * len(lines) + pad * 1.1); m = int(fs * .6)
    size = (w + 2 * m, h + 2 * m); mask = Image.new("L", size, 0); md = ImageDraw.Draw(mask)
    md.rounded_rectangle([m, m, m + w, m + h], radius=int(h * .28), fill=255); r = fs * .36; step = r * 1.25
    xs = np.arange(m + r, m + w - r / 2, step); ys = np.arange(m + r, m + h - r / 2, step)
    for x in xs:
        for y in (m, m + h): md.ellipse([x - r, y - r, x + r, y + r], fill=255)
    for y in ys:
        for x in (m, m + w): md.ellipse([x - r, y - r, x + r, y + r], fill=255)
    out = Image.new("RGBA", size, (0, 0, 0, 0)); sh = Image.new("RGBA", size, (30, 20, 50, 90)); sm = mask.filter(ImageFilter.GaussianBlur(fs * .12))
    out.paste(sh, (int(fs * .05), int(fs * .12)), sm); out.paste(Image.new("RGBA", size, (255, 255, 255, 255)), (0, 0), mask)
    d = ImageDraw.Draw(out)
    for i, l in enumerate(lines): d.text((m + w / 2, m + pad * .55 + i * lh + lh / 2), l, font=f, fill=(34, 30, 48), anchor="mm")
    return out
def make_title(text, fs, maxw, genre=None):
    f = font(fs); lines = wrap(text.upper(), f, maxw); lh = int(fs * 1.15); sw = max(3, int(fs * .09)); pad = sw * 3
    fillc, strc, shc = ((176, 238, 92, 255), (18, 44, 26, 255), (10, 24, 14, 255)) if genre == "zombie" else ((255, 214, 64, 255), (52, 28, 80, 255), (40, 20, 60, 255))
    dm = ImageDraw.Draw(Image.new("L", (1, 1))); lw = int(max(dm.textlength(l, font=f) for l in lines))
    im = Image.new("RGBA", (lw + 2 * pad, lh * len(lines) + 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        d.text((im.width / 2 + sw * .4, pad + i * lh + lh / 2 + sw * .8), l, font=f, fill=shc, anchor="mm", stroke_width=sw)
        d.text((im.width / 2, pad + i * lh + lh / 2), l, font=f, fill=fillc, anchor="mm", stroke_width=sw, stroke_fill=strc)
    return im
def scaled(im, k):
    if abs(k - 1) < 0.01: return im
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.BILINEAR)

# ------------------------------------------------------------------ AUDIO
SR = 44100
def _env(n, dec): return np.exp(-np.arange(n) / (SR * dec)).astype(np.float32)
def add(out, t0, sig, vol):
    i = int(t0 * SR); j = min(len(out), i + len(sig))
    if i < len(out): out[i:j] += sig[:j - i] * vol
def pluck(f, dur=0.5):
    n = int(SR * dur); t = np.arange(n) / SR
    return ((np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t)) * _env(n, dur * 0.35)).astype(np.float32)
def sfx(kind):
    if kind == "pop":
        n = int(SR * .14); t = np.arange(n) / SR; f = 700 * np.exp(-t * 14) + 180; return (np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, .05)).astype(np.float32)
    if kind == "whoosh":
        n = int(SR * .35); nz = np.random.RandomState(1).randn(n).astype(np.float32); k = np.ones(40) / 40
        s = np.convolve(nz, k, "same") * 6; return (s * np.sin(np.linspace(0, np.pi, n)) ** 2).astype(np.float32)
    if kind == "ding":
        n = int(SR * .6); t = np.arange(n) / SR; return ((np.sin(2 * np.pi * 1318 * t) + .4 * np.sin(2 * np.pi * 2637 * t)) * _env(n, .2)).astype(np.float32)
    if kind == "growl":
        n = int(SR * .9); t = np.arange(n) / SR; f = 70 + 10 * np.sin(2 * np.pi * 6 * t); ph_ = np.cumsum(f) / SR
        s_ = (2 * (ph_ % 1) - 1) * 0.6 + np.random.RandomState(2).randn(n) * 0.15; s_ = np.convolve(s_, np.ones(8) / 8, "same")
        return (s_ * np.sin(np.linspace(0, np.pi, n)) ** 0.7).astype(np.float32)
    if kind == "heartbeat":
        out_ = np.zeros(int(SR * 1.2), np.float32)
        for t0 in (0.0, 0.28):
            n = int(SR * .18); t = np.arange(n) / SR; add(out_, t0, (np.sin(2 * np.pi * 55 * t) * _env(n, .06)).astype(np.float32), 1.0)
        return out_
    if kind == "alarm":
        n = int(SR * 1.0); t = np.arange(n) / SR; f = 700 + 300 * np.sign(np.sin(2 * np.pi * 2 * t))
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 * np.sin(np.linspace(0, np.pi, n)) ** 0.5).astype(np.float32)
    if kind == "boom":
        n = int(SR * .7); t = np.arange(n) / SR; f = 90 * np.exp(-t * 5) + 30; return (np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, .25)).astype(np.float32)
    return None
def load_voice(path):
    tmp = path + ".44k.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", path, "-ar", str(SR), "-ac", "1", tmp], check=True)
    w = wave.open(tmp); raw = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; w.close(); os.remove(tmp); return raw
def build_audio(shots, starts, total, out_wav, has_voice, music_on=True, style="bright"):
    n = int(total * SR) + SR; y = np.zeros(n, np.float32)
    if music_on:
        prog = [[261.63, 329.63, 392.0], [220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [196.0, 246.94, 293.66]]
        if style == "tense": prog = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [146.83, 174.61, 220.0], [164.81, 207.65, 246.94]]
        bpm = 78 if style == "tense" else 96; beat = 60 / bpm; t0 = 0.0; k = 0; mv = 0.05 if has_voice else 0.11; bar = beat * 4
        while t0 < total:
            ch = prog[int(t0 / bar) % 4]; f = ch[k % 3] * (2 if (k // 3) % 2 else 1)
            add(y, t0, pluck(f, .45), mv)
            if k % 8 == 0: add(y, t0, pluck(ch[0] / 2, 1.2), mv * 1.4)
            if style == "tense" and k % 4 == 0: add(y, t0, sfx("heartbeat"), mv * 1.2)
            k += 1; t0 += beat / 2
    for sh, st in zip(shots, starts):
        s = sfx(sh.get("sfx", "pop"))
        if s is not None: add(y, st, s, 0.35)
        v = sh.get("voice")
        if v and os.path.exists(v): add(y, st + 0.1, load_voice(v), 0.95)
    y = np.tanh(y * 1.2); w = wave.open(out_wav, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((y[:int(total * SR)] * 32000).astype(np.int16).tobytes()); w.close()

# ------------------------------------------------------------------ STORY
def validate(story, mode):
    err = []; shots = story.get("shots", [])
    if not shots: err.append("story needs a non-empty 'shots' list")
    for i, s in enumerate(shots, 1):
        if s.get("location") not in LOCS: err.append(f"shot {i}: location '{s.get('location')}' invalid. Use: {sorted(LOCS)}")
        if not isinstance(s.get("dur", s.get("duration")), (int, float)) and not s.get("voice"): err.append(f"shot {i}: needs 'dur' seconds")
        for c in s.get("characters", []):
            if c.get("name") not in CHARS: err.append(f"shot {i}: character '{c.get('name')}' not in bible. Use: {sorted(CHARS)}")
            if c.get("pose", "idle") not in POSES: err.append(f"shot {i}: pose '{c.get('pose')}' invalid. Use: {sorted(POSES)}")
            if c.get("expr", "neutral") not in EXPR: err.append(f"shot {i}: expr '{c.get('expr')}' invalid. Use: {sorted(EXPR)}")
            if c.get("look", "center") not in LOOK: err.append(f"shot {i}: look '{c.get('look')}' invalid. Use: {sorted(LOOK)}")
    for i, s in enumerate(shots, 1):
        for f_ in s.get("fx", []):
            if f_ not in FX: err.append(f"shot {i}: fx '{f_}' invalid. Use: {list(FX)}")
        for c in s.get("characters", []):
            if c.get("prop", "none") not in PROPS: err.append(f"shot {i}: prop '{c.get('prop')}' invalid. Use: {list(PROPS)}")
        if len(s.get("characters", [])) > 5: err.append(f"shot {i}: max 5 characters per shot")
        if s.get("grade", "none") not in ("none", "horror"): err.append(f"shot {i}: grade must be none|horror")
    return err
def shot_dur(s):
    d = float(s.get("dur", s.get("duration", 3.0))); v = s.get("voice")
    if v and os.path.exists(v):
        try: d = max(d, len(load_voice(v)) / SR + 0.45)
        except Exception: pass
    return d

_fxc = {}; _horde = {}
def fog_layer(W, H):
    k = ("fog", W, H)
    if k not in _fxc:
        al = np.clip((np.linspace(0, 1, H) - 0.55) / 0.45, 0, 1) ** 1.3 * 105
        arr = np.zeros((H, W, 4), np.uint8); arr[..., 0], arr[..., 1], arr[..., 2] = 205, 222, 226; arr[..., 3] = al[:, None].astype(np.uint8)
        _fxc[k] = Image.fromarray(arr, "RGBA")
    return _fxc[k]
def red_layer(W, H):
    k = ("red", W, H)
    if k not in _fxc:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); r = np.sqrt(((xx / W - .5) * 2) ** 2 + ((yy / H - .5) * 2) ** 2)
        m = (np.clip((r - 0.55) / 0.75, 0, 1) ** 1.4 * 170).astype(np.uint8)
        _fxc[k] = (Image.new("RGBA", (W, H), (230, 20, 30, 255)), Image.fromarray(m, "L"))
    return _fxc[k]

def render(story, out, mode, scale=1.0, fps=24, check=None):
    errs = validate(story, mode)
    if errs: print("STORY ERRORS:\n - " + "\n - ".join(errs)); sys.exit(2)
    meta = story.get("meta", {}); genre = meta.get("genre", "general")
    shots = story["shots"]; durs = [shot_dur(s) for s in shots]; total = sum(durs)
    if total > LIMITS[mode] + 0.01: print(f"ERROR: total {total:.1f}s exceeds {mode} limit {LIMITS[mode]:.0f}s. Remove/shorten shots."); sys.exit(3)
    W, H = (1080, 1920) if mode == "short" else (1920, 1080)
    W, H = int(W * scale) // 2 * 2, int(H * scale) // 2 * 2; M = min(W, H); BASE = 0.26 * M
    starts = np.cumsum([0] + durs[:-1]).tolist(); print(f"{mode}: {W}x{H} @{fps}fps, {len(shots)} shots, {total:.1f}s, genre={genre}")
    proc = None
    if not check:
        wav = out + ".audio.wav"
        build_audio(shots, starts, total, wav, any(s.get("voice") for s in shots), meta.get("music", True), "tense" if genre == "zombie" else meta.get("music_style", "bright"))
        proc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-i", wav,
                                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    prev = None; fade = int(fps * 0.22)
    for si, (sh, T) in enumerate(zip(shots, durs)):
        grade = sh.get("grade", "horror" if genre == "zombie" else "none"); fx = sh.get("fx", [])
        bg, gy0 = get_bg(sh["location"], W, H, grade); n = max(1, int(round(T * fps))); cam = sh.get("camera", {})
        z0, z1 = cam.get("zoom", [1.0, 1.08]); fxy = cam.get("focus", [0.5, 0.55]); hn = int(sh.get("horde", 0))
        cap = make_cloud(sh["caption"], 0.056 * M, W * (0.8 if mode == "short" else 0.5)) if sh.get("caption") else None
        ttl = make_title(sh["title"], 0.115 * M, W * 0.86, genre) if sh.get("title") else None
        rng = random.Random(si * 7 + 1); phases = {}
        frames = [check] if check else range(n)
        for f in frames:
            if check: f = int(n * 0.55)
            t = f / fps; u = t / T; z = lerp(z0, z1, ease(u))
            cw, ch_ = W / z, H / z; x0 = min(max(fxy[0] * W - cw / 2, 0), W - cw); y0 = min(max(fxy[1] * H - ch_ / 2, 0), H - ch_)
            if "shake" in fx:
                r2 = random.Random(si * 1000 + f); amp = (14 * (1 - u) + 3) * M / 1080
                x0 = min(max(x0 + r2.uniform(-amp, amp), 0), W - cw); y0 = min(max(y0 + r2.uniform(-amp, amp), 0), H - ch_)
            fr = bg.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch_)).convert("RGBA")
            for i in range(hn):   # zombie horde in the background (behind main characters)
                nm = ZOMBIES[i % len(ZOMBIES)]; zs = CHARS[nm]; rr = random.Random(i * 13 + 5); row = i % 3
                wx = (i + 0.5) / hn + rr.uniform(-0.04, 0.04) + 0.015 * math.sin(t * 0.9 + i)
                gy = gy0 - 0.07 + row * 0.035; sz = (0.34 + row * 0.07) * lerp(0.85, 1.2, u) * zs.get("scale", 1.0)
                D = BASE * sz * z; Dq = max(8, int(D / 6) * 6); bk = int(t * 4 + i) % 3
                key = (nm, Dq, bk)
                if key not in _horde:
                    _horde[key] = draw_char(zs, dict(pose="zwalk", expr="zombie", t=bk * 0.37, phase=0.5, tilt=math.sin(bk * 2.1) * 3, bob=0.02 * math.sin(bk * 2.1), walk=bk * 1.3, look="center"), Dq)
                spr, (ax, ay) = _horde[key]; sx, sy = (wx * W - x0) * z, (gy * H - y0) * z
                fr.paste(spr, (int(sx - ax), int(sy - ay)), spr)
            items = []
            for ci, c in enumerate(sh.get("characters", [])):
                spec = CHARS[c["name"]]; zb = bool(spec.get("zombie"))
                x = c.get("x", 0.5); tx = c.get("to_x"); moving = tx is not None and abs(tx - x) > 1e-3
                wx = lerp(x, tx, ease(u)) if moving else x
                pose = c.get("pose", ("run" if c.get("run") else "walk") if moving else "idle")
                if zb and pose in ("idle", "walk"): pose = "zwalk"
                if c.get("prop") == "bat" and pose == "idle": pose = "defend"
                talk = sh.get("speaker") == c["name"]
                if talk and pose == "idle": pose = "talk"
                ph = phases.setdefault(ci, rng.uniform(0, 3)); spd = 13 if pose == "run" else (3.5 if zb else 7)
                walking = moving or pose in ("walk", "run")
                st = dict(pose=pose, expr=c.get("expr", "zombie" if zb else "neutral"), look=c.get("look", "center"), t=t, phase=ph, talk=talk, flip=c.get("flip", False),
                          prop=c.get("prop"), run=(pose == "run"), bob=math.sin(t * 2.2 + ph) * 0.012 + (abs(math.sin(t * spd)) * -0.04 if walking else 0),
                          tilt=math.sin(t * 1.3 + ph) * (3 if zb else 1), walk=(t * spd if walking else None))
                D = BASE * c.get("size", 1.0) * spec.get("scale", 1.0) * z; gy = c.get("y", gy0)
                items.append(((gy * H - y0) * z, ci, c, st, D, (wx * W - x0) * z))
            for sy, ci, c, st, D, sx in sorted(items, key=lambda a: (a[0], a[1])):
                spr, (ax, ay) = draw_char(CHARS[c["name"]], st, D)
                sd = Image.new("RGBA", (int(D * 1.4), int(D * .3)), (0, 0, 0, 0)); ImageDraw.Draw(sd).ellipse([0, 0, sd.width - 1, sd.height - 1], fill=(20, 10, 40, 70))
                sd = sd.filter(ImageFilter.GaussianBlur(D * .02)); fr.paste(sd, (int(sx - sd.width / 2), int(sy - sd.height / 2)), sd)
                fr.paste(spr, (int(sx - ax), int(sy - ay)), spr)
            if "fog" in fx: fr.alpha_composite(fog_layer(W, H))
            if "red_alert" in fx:
                solid, mk = red_layer(W, H); kk = 0.3 + 0.7 * math.sin(t * 6) ** 2; fr.paste(solid, (0, 0), mk.point(lambda v: int(v * kk)))
            if cap is not None and t > 0.12:
                a_ = (t - 0.12) / 0.3; k = 0.8 + 0.2 * pop(a_); al = min(1.0, a_ * 2) * min(1.0, max(0.0, (T - t) / 0.2))
                im = scaled(cap, k)
                if al < 1: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * al)))
                px = (W - im.width) // 2 if mode == "short" else int(0.04 * W)
                cy_ = 0.06 if mode == "short" else (0.74 if sh.get("title") else 0.05)
                fr.paste(im, (px, int(cy_ * H)), im)
            if ttl is not None and t > 0.05:
                a_ = (t - 0.05) / 0.35; im = scaled(ttl, 0.6 + 0.4 * pop(a_))
                if mode == "long": py = int(0.04 * H)
                elif si == 0 or sh.get("title_pos") == "center": py = int(0.30 * H)
                else: py = int(0.24 * H)
                fr.paste(im, ((W - im.width) // 2, py), im)
            fr = fr.convert("RGB")
            if "flicker" in fx:
                r3 = random.Random(si * 977 + f // 2); fr = ImageEnhance.Brightness(fr).enhance(1.0 if r3.random() > 0.35 else 0.55 + 0.25 * r3.random())
            if prev is not None and f < fade and not check: fr = Image.blend(prev, fr, (f + 1) / (fade + 1))
            if check:
                os.makedirs(check_dir, exist_ok=True); fr.save(os.path.join(check_dir, f"shot_{si + 1:02d}.png")); break
            proc.stdin.write(fr.tobytes())
            if f == n - 1: prev = fr
        print(f"  shot {si + 1}/{len(shots)} ok ({sh['location']}, {T:.1f}s)", flush=True)
    if proc:
        proc.stdin.close(); proc.wait(); os.remove(out + ".audio.wav"); print("DONE ->", out)

check_dir = "check"
def main():
    global check_dir
    ap = argparse.ArgumentParser(description="BlobToon: story.json -> mp4")
    ap.add_argument("story"); ap.add_argument("-o", "--out", default="out.mp4"); ap.add_argument("--mode", choices=["short", "long"])
    ap.add_argument("--scale", type=float, default=1.0, help="0.5 = fast draft"); ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--check", action="store_true", help="render 1 PNG per shot into ./check (fast visual QA, no video)")
    a = ap.parse_args(); story = json.load(open(a.story)); mode = a.mode or story.get("meta", {}).get("mode", "short")
    if a.check: check_dir = os.path.join(os.path.dirname(os.path.abspath(a.out)), "check")
    render(story, a.out, mode, a.scale, a.fps, check=1 if a.check else None)
if __name__ == "__main__": main()
