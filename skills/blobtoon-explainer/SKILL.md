---
name: blobtoon-explainer
description: Make 2D cartoon story/explainer videos in the "black round-head blob" style (shorts up to 60s 9:16, long up to 5 min 16:9) with a locked cast (hero Pico in yellow hoodie, friends, doctor, ZOMBIES) and 13 locked locations incl. ruined street, rooftop, lab. Use for ANY topic/title: daily-life stories, explainers, and ZOMBIE OUTBREAK / apocalypse / survival videos. Characters are code-locked so consistency is 100%.
license: MIT (font Poppins is OFL)
compatibility: opencode, claude-code. Needs python3, pillow, numpy, ffmpeg. Optional edge-tts for voice.
metadata:
  style: blob-cartoon
  genres: general, zombie
  outputs: mp4
---

# BlobToon Explainer

You turn ANY title into a finished mp4 by writing ONE `story.json` and running ONE command.
Never draw or describe pixels yourself: the engine draws the cast and places, so characters cannot drift.

## Hard rules (do not break)
1. Characters ONLY from `characters.json`: pico, remy, mia, zed, ollie, sam, doc + zombies (zombie, zombie_girl, zombie_boss, zombie_remy, zombie_ollie). Never invent colors/outfits/characters. Hero = `pico`, in EVERY shot (except pure zombie close-ups).
2. Locations ONLY: bedroom_night, classroom, living_room, street_sunset, cafe, stage, bus, park, ruined_street, abandoned_school, supermarket, rooftop, lab, hospital, hospital_hall.
3. pose/expr/look/prop/fx/sfx values ONLY from `references/vocabulary.md` (engine prints valid values on error).
4. Limits: **short <= 60 s** (1080x1920), **long <= 300 s** (1920x1080). Engine refuses longer.
5. Max 5 characters per shot. One idea per shot. Caption = 1 short sentence (max ~12 words).
6. Keep it kid-safe: no blood/gore/killing on screen. Fear comes from fog, red_alert, shake, growl.

## Workflow (follow in order)
1. Read `references/style-guide.md` and `references/vocabulary.md`. **If the topic is zombie/outbreak/apocalypse/infection/survival: ALSO read `references/zombie-outbreak-guide.md` and set `"genre":"zombie"`.** Look at `references/sheets/*.png` once.
2. Do not ask questions unless the title is missing. short/reel/shorts -> `short`; otherwise `long`.
3. Write shots using the pacing below. Start from `templates/story_short.json`, `story_long.json`, `story_zombie_short.json` or `story_zombie_long.json`. Save as `story.json`.
4. (Optional voice) `python <skill>/scripts/tts.py story.json --voice en-IN-NeerjaNeural`. Skip if offline.
5. QA fast: `python <skill>/scripts/blobtoon.py story.json --check -o out/video.mp4 --scale 0.5` -> inspect `out/check/shot_XX.png`.
6. Final: `python <skill>/scripts/blobtoon.py story.json -o out/video.mp4` (`--mode short|long` if meta.mode missing; `--scale 0.5` for draft).
7. Reply with the mp4 path + 2-line summary. Do not paste the JSON.
`<skill>` = folder containing this SKILL.md (`.opencode/skills/blobtoon-explainer`).

## Pacing
- **Short (45-55 s):** 12-14 shots x 3.5-4.5 s. Shot 1 = hook with `title`. Last shot = moral/cliffhanger + `title`.
- **Long (4-5 min):** 45-60 shots x 4-6 s: hook -> problem -> turning point -> explanation/climax -> recap + CTA. Change location every 3-5 shots; vary camera zoom.
- Hinglish/Hindi/English fine. Devanagari: set env `BLOBTOON_FONT=/path/NotoSansDevanagari-Bold.ttf`.

## story.json cheat sheet
```
{"meta":{"title":"...","mode":"short","genre":"zombie|general","music":true},
 "shots":[{"location":"ruined_street","dur":4,"caption":"text","title":"optional BIG text","speaker":"pico",
   "sfx":"pop|whoosh|ding|growl|alarm|boom|heartbeat|none","fx":["fog","shake","red_alert","flicker"],"horde":6,"grade":"none|horror",
   "camera":{"zoom":[1.0,1.12],"focus":[0.5,0.6]},
   "characters":[{"name":"pico","x":0.5,"to_x":0.7,"run":true,"pose":"point","expr":"scared","look":"right","size":0.9,"prop":"bat"}]}]}
```
`x`/`to_x` = position 0..1 (to_x makes them walk; `run:true` runs). `speaker` moves the mouth. `size` 0.6-1.2. `horde` = background zombies (zombie genre).
Layout: 1 char x=0.5; 2 chars x=0.3/0.7 size 0.85; 3 chars x=0.2/0.5/0.8 size 0.75-0.8.

## If something fails
- `STORY ERRORS` -> fix the JSON using the printed valid values. `ffmpeg not found` -> ask user to install ffmpeg. `ModuleNotFoundError` -> `pip install pillow numpy`.
- Slow machine -> `--scale 0.5 --fps 20`.
