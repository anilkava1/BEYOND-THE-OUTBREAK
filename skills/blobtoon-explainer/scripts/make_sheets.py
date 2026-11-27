#!/usr/bin/env python3
"""Regenerates the visual reference sheets (cast, poses, expressions, locations) into references/sheets/. Run after editing characters.json."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blobtoon as B
from PIL import Image, ImageDraw
OUT = os.path.join(B.SKILL, "references", "sheets"); os.makedirs(OUT, exist_ok=True)
BG = (240, 233, 222); INK = (40, 34, 52)
def sprite(name, **st):
    d = dict(pose="idle", expr="neutral", t=0.5, phase=1.0, look="center"); d.update(st); spec = B.CHARS[name]
    if spec.get("zombie") and d["expr"] == "neutral": d["expr"] = "zombie"
    im, _ = B.draw_char(spec, d, 200); return im.crop(im.getbbox())
def sheet(items, cols, fname, cw=250, chh=380, title=None):
    rows = (len(items) + cols - 1) // cols; top = 70 if title else 10
    S = Image.new("RGB", (cols * cw, rows * chh + top), BG); d = ImageDraw.Draw(S)
    if title: d.text((20, 18), title, font=B.font(30), fill=INK)
    for i, (img, label) in enumerate(items):
        x, y = (i % cols) * cw, top + (i // cols) * chh; k = min((cw - 30) / img.width, (chh - 70) / img.height); im = img.resize((int(img.width * k), int(img.height * k)), Image.LANCZOS)
        S.paste(im, (x + (cw - im.width) // 2, y + 12 + (chh - 70 - im.height)), im); d.text((x + cw / 2, y + chh - 28), label, font=B.font(20), fill=INK, anchor="mm")
    S.save(os.path.join(OUT, fname)); print("wrote", fname)
survivors = [k for k, v in B.CHARS.items() if not v.get("zombie")]; zombies = B.ZOMBIES
sheet([(sprite(n), n) for n in survivors + zombies], 6, "cast-sheet.png", title="BlobToon cast - LOCKED (survivors + zombies)")
poses = [p for p in B.POSES]; items = []
for p in poses: items.append((sprite("pico", pose=p, walk=1.0 if p in ("walk", "run") else None, run=(p == "run")), p))
items.append((sprite("pico", pose="defend", prop="bat"), "defend + bat")); items.append((sprite("pico", pose="point", prop="flashlight"), "point + flashlight"))
sheet(items, 6, "poses-sheet.png", title="Poses (pico)")
ex = [(sprite("zombie" if e in ("zombie", "groan") else "pico", expr=e), e) for e in B.EXPR]
sheet(ex, 6, "expressions-sheet.png", title="Expressions (zombie / groan shown on a zombie)")
W, H = 270, 480; cells = list(B.LOCS); cols = 7; rows = (len(cells) + cols - 1) // cols
S = Image.new("RGB", (cols * W, rows * (H + 36) + 60), BG); d = ImageDraw.Draw(S); d.text((20, 14), "Locations (use these names in story.json)", font=B.font(30), fill=INK)
for i, n in enumerate(cells):
    bg, gy = B.get_bg(n, 540, 960, "horror" if n in ("ruined_street", "abandoned_school", "supermarket", "rooftop", "lab") else "none")
    x, y = (i % cols) * W, 60 + (i // cols) * (H + 36); S.paste(bg.resize((W, H), Image.LANCZOS), (x, y)); d.text((x + W / 2, y + H + 18), n, font=B.font(20), fill=INK, anchor="mm")
S.save(os.path.join(OUT, "locations-sheet.png")); print("wrote locations-sheet.png")
