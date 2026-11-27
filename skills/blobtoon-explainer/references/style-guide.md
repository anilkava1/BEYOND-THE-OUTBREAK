# Visual style (extracted from the reference video)
Look at `ref-frames/*.jpg` once. The engine already reproduces it; this is for writing good shots.

- **Characters:** glossy jet-black spherical head, big white oval eyes with black pupils + tiny highlight, pink blush when happy, tiny pink mouth. Small hoodie torso, thin black stick legs, white sneakers, black ball hands. Head is HUGE vs body.
- **Hero Pico:** yellow hoodie, no hair. Friends differ ONLY by hoodie color + hair/hat. Adults = navy suit, red tie.
- **World:** soft pastel flat illustration, gentle blur + vignette, warm lighting, small background crowd of mini blob people in classroom/cafe/bus/stage.
- **Captions:** white fluffy "cloud" speech bubble with dark bold text, pops in from 80% scale. Big yellow outlined `title` for hook and moral.
- **Camera:** slow push-in (zoom 1.0 -> 1.1) every shot, soft 0.2 s cross-fade between shots, pop/whoosh/ding sfx, light plucky background music.
- **Story tone:** relatable school/daily-life situation, comic panic, simple lesson at the end. Emotion changes through `expr`, not through new art.

# Consistency contract
Cast and places live in `characters.json` + `scripts/blobtoon.py` only. A story file can pick names but cannot override colors, so Pico is pixel-identical in shot 1 and shot 60.

# Zombie variant
Same blob world, darker mood: desaturated backgrounds, orange fire glow on horizon, red emergency light, fog at the feet, camera shake on impact. Zombies = green-gray glossy head, yellow eyes + red pupils, jagged mouth, stitched torn hoodie, arms forward. Titles turn toxic green. Music switches to slow minor plucks + heartbeat. Still kid-safe cartoon: no blood. See `zombie-outbreak-guide.md` and `sheets/`.
