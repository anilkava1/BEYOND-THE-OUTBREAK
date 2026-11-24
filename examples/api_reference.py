"""
API USAGE EXAMPLE ONLY (not part of any video). Copy the pattern, not the visuals.
A scene is a file scenes/<id>.py with a render(ctx) function.

Pattern:
  1. Build the STATIC base image + STATIC glow once, outside the frame loop.
  2. In the frame loop draw only moving things on a transparent layer, tone() them, composite,
     add fog, then finish with post() which applies glow, camera, vignette, grain and caption.
  3. ctx.save(out, f)
"""
from studio.engine import *


def render(ctx):
    # ---- static part (once) ----
    base = vgrad(H, *SKY["night"]).convert("RGBA")
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    stars(ImageDraw.Draw(base), 400)
    moon(base, glow, 900, 160, 80, (190, 70, 60), (200, 60, 50))
    far = new_layer(); skyline(far, 470, 1, 120, 300, 70, 150, (32, 32, 62), win_prob=0.12)
    base.alpha_composite(blur_layer(far, 3))                      # far layer = blurred
    ImageDraw.Draw(base).rectangle([0, 470, W, H], fill=(26, 26, 32))
    base = base.convert("RGB")
    fog = make_fog(1)

    # ---- per-frame part ----
    for f in ctx.frames():
        t = ctx.t(f)
        img = base.copy().convert("RGBA")
        lay = new_layer(); d = ImageDraw.Draw(lay); glows = []
        person(d, lerp(300, 700, t), 540, 1.4, False, f, 0, "march", shirt=SHIRTS[1], pants=PANTS_[1])
        img.alpha_composite(tone(lay, (170, 175, 225)))             # darken figures to match the night
        img = img.convert("RGB"); apply_fog(img, fog, f)
        g = dyn_glow(glow, glows)                                   # per-frame lights go here
        out = post(img, g, f, z=lerp(1.0, 1.1, ease(t)), caption=ctx.text, calpha=fade(f, ctx.total))
        ctx.save(out, f)
