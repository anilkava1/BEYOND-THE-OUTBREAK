# AGENTS.md: Script-driven video studio (dark cartoon style)

Ye project `script/script.json` se video banata hai. **Koi bhi visual pehle se fixed nahi hai.** `scenes/` folder khaali hai. Har scene ka visual tumhe script ke `visual`, `narration`, `caption` aur global `style` se decide karke code mein design karna hai.

## Golden rules
1. Koi bana-banaya scene/template reuse mat karo. Har scene `script.json` ki scene entry se design hoga. Agar script badli hai to visuals bhi badlenge.
2. `examples/api_reference.py` sirf API dikhane ke liye hai. Uska visual copy mat karo.
3. Engine primitives (`studio/engine.py`) reuse karo. Jo cheez nahi hai, naya helper `studio/extras.py` mein banao (engine.py mein sirf bug fix karo).
4. Sirf procedural drawing (Pillow + numpy). Koi external image/asset download mat karo. Kisi existing film/show/game ke characters ya artwork copy mat karo.
5. Output size fixed hai: 1280x720, 30 fps. Scene ki length `seconds` se aati hai.

## Workflow
1. `script/script.json` padho. Agar user ne plain text/markdown script di hai to pehle use is JSON format mein convert karo (`id`, `seconds`, `narration`, `visual`, `caption`).
2. Har scene ke liye chhota plan (thinking mein): location/environment, kaun/kya hai, lighting (kaunsa light source, kya glow), depth layers, camera move, caption timing.
3. `scenes/<id>.py` likho jisme `render(ctx)` ho (pattern: `examples/api_reference.py`, primitives: `docs/PRIMITIVES.md`).
4. Check: `python3 studio/build.py --preview` -> `out/preview.jpg` kholo/dekho, jo khali, flat ya galat lage use fix karo.
5. Final: `python3 studio/build.py` -> `out/video.mp4`. Kisi ek scene ko dobara: `python3 studio/build.py --scenes s02`.

## Style kaise lagana hai (script ke `style` block se mood lo)
Default look: flat 2D cartoon, round-headed chibi characters, bold dark outline, dark moody atmosphere. Visual ko "khali" nahi lagna chahiye. Har scene mein ye layers socho:
- **Depth**: far layer blurred (`blur_layer(...,3)`), mid layer sharp outline ke saath, foreground blurred ya partially cropped objects.
- **Environment detail**: skyline/buildings, props (cars, barrels, planks, lamps), ground details (street, blood, cracks), sky (stars, moon, smoke), aur kuch moving (crows, embers, crowd sway).
- **Lighting**: scene ka base dark rakho. Roshni `glow` layer se do (`add_glow`, `lamp`, `barrel_fire`, window glows). Characters ko `tone(layer, (r,g,b))` se scene ke rang mein darken karo.
- **Atmosphere**: `apply_fog(...)` dhuan/kohra ke liye. `post(...)` vignette aur film grain khud lagata hai.
- **Camera**: `post(..., z=zoom, cx, cy, shake)` se slow push-in/pull-out. Close-up ke liye zoom 2+ karo kisi face par.
- **Caption**: `post(..., caption=ctx.text, calpha=fade(f, ctx.total))`. Script mein caption khali ho to na dikhao.
- Palette script ke style/mood se aaye (night, blood-dusk, overcast, day ya apna). Zaroori nahi ki har video zombie/night ho.

## Technical gotchas (pehle bhi bugs aaye hain, dhyan do)
- **Static vs per-frame**: base image aur static glow loop ke bahar ek baar banao. Loop ke andar sirf moving cheezein.
- **Static glow ko loop mein modify mat karo.** Per-frame lights `glows` list mein daalo `(x, y, r, color, k)` aur `g = dyn_glow(glow, glows)` use karo. `add_glow(glow, ...)` seedha static par loop mein kiya to har frame par roshni jama hoti jayegi.
- `lamp(base, glow, ...)` aur `moon(...)` mein `base` ka mode matter karta hai: `lamp` ko RGB base chahiye, `moon` aur `skyline` ko RGBA. Examples dekho.
- `barrel_fire(d, glow, ...)` apne aap glow add karta hai. Loop mein use karo to `glow` ki jagah throwaway `Image.new("RGB",(1,1))` do aur flicker wali roshni `glows` list se do.
- Flipped drawing mein rectangles ke coordinates ulte ho sakte hain. Engine mein handle hai, naya primitive banao to `min/max` use karo.
- Performance: ek frame ~0.1 to 0.3s. Bahut zyada blur/figures per-frame mat karo. `--preview` se pehle check karo, full render baad mein.
- ffmpeg PATH mein hona chahiye. Hindi/Devanagari caption ke liye `assets/fonts/` mein ek Devanagari .ttf daalo aur `load_font(size, path)` se caption font set karo.

## Don'ts
- `out/` ya `frames/` ki purani files user ke bina mat hatao (build khud apne scene folders overwrite karta hai).
- Graphic gore ya sexual content mat banao. Zombie/horror ho to cartoon-style aur non-graphic rakho.
