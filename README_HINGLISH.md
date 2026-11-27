# BlobToon Skill for Opencode (ref-video style)

## Install (1 minute)
1. Zip extract karo apne project ke root me. Folder banega: `.opencode/skills/blobtoon-explainer/`
   (Global chahiye to is folder ko `~/.config/opencode/skills/` me copy karo.)
2. Dependencies: `pip install pillow numpy` aur `ffmpeg` installed hona chahiye.
3. Opencode me bolo:  "blobtoon-explainer skill use karke 'Why we procrastinate' ka shorts video bana"
   Long ke liye:       "... ka 4 minute ka long video bana"

## Manual test (bina AI ke)
    python .opencode/skills/blobtoon-explainer/scripts/blobtoon.py demo/demo_story.json -o demo/out.mp4
    (jaldi check: --check  |  draft speed: --scale 0.5)

## Kya locked hai (consistency 100%)
- Cast: pico (hero, yellow), remy, mia, zed, ollie, sam  -> `characters.json`
- 8 locations: bedroom_night, classroom, living_room, street_sunset, cafe, stage, bus, park
- Limits: short max 60s (1080x1920), long max 300s (1920x1080). Engine us se zyada accept hi nahi karta.

## Free tier tips
- Video local CPU par render hota hai: koi image/video API ya paid model nahi chahiye.
- Model ko sirf ek chhota story.json likhna hota hai (short ~1.5k tokens, long ~6k tokens).
- Voice optional hai: `python scripts/tts.py story.json` (edge-tts, internet chahiye). Bina voice ke captions + music wala video banta hai.

## Naya character / location jodna
- Character: `characters.json` me ek entry (color, hair: none/bob/curly/beanie/cap). Baaki sab auto.
- Location: `scripts/blobtoon.py` me `L_xxx` function copy karke LOCS me add karo.

## ZOMBIE OUTBREAK support (v2)
- Story JSON me `"meta":{"genre":"zombie"}` likho. Auto: horror colors, green title, tense music + heartbeat.
- Naye characters: doc (scientist) + zombies: zombie, zombie_girl, zombie_boss, zombie_remy, zombie_ollie.
- Naye locations: ruined_street, abandoned_school, supermarket, rooftop, lab (kul 13).
- Naye poses: run, zwalk, cower, defend. Props: bat, flashlight. Expressions: scared, terrified, determined, zombie, groan.
- Effects: `horde` (background zombies), `fx` = fog / shake / red_alert / flicker. Sfx: growl, alarm, boom, heartbeat.
- References: `references/zombie-outbreak-guide.md` (story beats, caption bank) + `references/sheets/` (cast, poses, expressions, locations images).
- Templates: `story_zombie_short.json` (41s) aur `story_zombie_long.json`.
- Demo: `demo/demo_zombie_short.mp4`
- Content cartoon-safe rakha hai: koi blood/gore nahi.
Sheets dobara banane ke liye: `python scripts/make_sheets.py`
