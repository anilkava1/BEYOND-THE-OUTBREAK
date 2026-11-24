# Engine primitives (`from studio.engine import *`)

Canvas: `W, H, FPS = 1280, 720, 30`. Colors are RGB tuples.

## Math / timing
- `lerp(a, b, t)`, `clamp(t, a=0, b=1)`, `ease(t)` (smoothstep 0..1)
- `fade(local_frame, duration, fi=14, fo=14)` -> alpha 0..1 for caption in/out
- Scene ctx (`ctx`): `ctx.frames()`, `ctx.total`, `ctx.fps`, `ctx.t(f)` (0..1), `ctx.sec(f)`, `ctx.text` (caption), `ctx.scene` (dict), `ctx.save(img, f)`

## Layers and images
- `vgrad(h, top, bottom)` -> RGB gradient image (width W). Presets: `SKY["night"|"blood_dusk"|"deep_night"|"overcast"|"day"]` (tuples of top, bottom)
- `new_layer()` -> transparent RGBA layer; draw figures/props on it with `ImageDraw.Draw`
- `blur_layer(layer, radius)` -> blurred copy (depth of field)
- `tone(layer, (r,g,b))` -> multiply layer by ambient color (darkens figures to match scene)
- `make_fog(seed)` + `apply_fog(img_rgb, fog, frame, color, alpha, speed)` -> drifting fog (in place)

## Lighting (glow layer = black RGB image, screen-blended in `post`)
- `add_glow(glow, x, y, r, color, k=1.0)`: soft radial light
- `add_mask_glow(glow, L_mask, color, k)` -> returns new glow: light through any L mask (cones, pools)
- `dyn_glow(static_glow, glows)`: copy + per-frame lights `[(x, y, r, color, k), ...]`
- `lamp(base_rgb, glow, x, y, h, col, power, r)` -> draws street lamp, returns light-cone mask for `add_mask_glow`
- `moon(base_rgba, glow, x, y, r, color, glow_color)`, `stars(draw, horizon_y, n, seed)`
- `flame(draw, x, y, s, frame, seed)`, `barrel_fire(draw, glow, x, y, s, frame, seed)`

## Environment
- `skyline(rgba_layer, base_y, seed, hmin, hmax, wmin, wmax, color, win_prob, outline, win_col, lit_out, ruin)` -> buildings with windows. `lit_out=list` collects lit window positions for glows. `ruin` is 0..1 chance of broken rooftops.
- `street(draw, y0, road, walk, seed, blood)` -> sidewalk + road + cracks + stains
- `wreck_car(draw, x, y, s, color)`, `plank(draw, cx, cy, w, h, angle)`, `crow(draw, x, y, frame, s, phase)`

## Characters
- `person(draw, x, y, s, flip, frame, phase, mood, zombie, shirt, pants, arm_up, lean, glows, weapon, skin, hair)`
  - origin x,y ~ chest; height ~ 130*s; `mood`: "calm" | "march" | "shout"; `weapon`: None | "torch" | "bat"
  - `zombie=True` -> green skin, arms forward, blood, glowing red eyes (pass `glows=[]` to collect eye lights for `dyn_glow`)
  - `lean` tilts forward (0..0.6); `skin`/`hair` override colors (silhouettes)
- `crowd(draw, cols, rows, x, y, gx, gy, s, seed, frame, flip, zombie, glows, mood)` -> grid of people
- Palettes: `SHIRTS`, `PANTS_`

## Final pass
- `post(img_rgb, glow, f, z=1.0, cx, cy, shake=0, flash=0, caption=None, calpha=1.0)` -> applies glow, camera zoom/pan/shake, vignette, film grain, caption. Returns RGB image to `ctx.save`.
- `draw_caption(img_rgba, text, alpha, y0)`, `load_font(size, path=None)`

## Typical per-frame recipe
```python
img = base.copy().convert("RGBA")
lay = new_layer(); d = ImageDraw.Draw(lay); glows = []
# ... draw moving things on d ...
img.alpha_composite(tone(lay, (170, 175, 225)))
img = img.convert("RGB"); apply_fog(img, fog, f)
g = dyn_glow(static_glow, glows)
out = post(img, g, f, z=1.1, caption=ctx.text, calpha=fade(f, ctx.total))
ctx.save(out, f)
```
