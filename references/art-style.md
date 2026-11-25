# Art Style (fixed look, tuned for dread)

## Core look (same family as the reference style)
- **Flat 2D vector / paper-cutout puppet animation**: jointed cut-out pieces, thin dark-brown/near-black outlines, soft drop-shadow giving papercraft depth.
- **3–4 depth layers** per scene (far silhouettes → mid structures → ground → foreground frame pieces: fence wire, broken glass edge, curtains, tree branches, door crack).
- Characters in front of simple, richly coloured, **layered backgrounds**. No photo-realism, no 3D, no gloss.
- Accent system: where the original style used **gold**, zombie videos use **hazard amber/yellow** (caution tape, emergency lights, torch beams) and **signal red** for danger. Gold is allowed for warm, safe, "home" light (candle, lamp).

## Light = the main storytelling tool
- Light sources are **practical and visible**: torch cone, candle, phone screen, car headlights, fire barrel, emergency strip lights, moon, lightning, window glow.
- Everything outside the light falls into **two-tone shadow** (flat dark shape, not blur). Add soft light cones as semi-transparent flat polygons.
- Safe = warm amber, small, enclosed. Danger = cold blue/green/grey, large, open. Peak danger = red flash/pulsing.
- Flicker: light intensity loops irregularly (not sine) when power is failing.

## Palettes (start points; adapt per mood)
| Mood | Colours | Particles / atmosphere |
|---|---|---|
| Calm before / normal world | warm daylight peach, sky blue, green | dust, pollen, birds |
| Outbreak / panic | washed yellow, siren red/blue flashes, smoke grey | sirens glow, papers, smoke |
| Night survival | indigo, teal-black, amber pools | rain, breath fog, moths, ash |
| Abandoned city | concrete grey, rust, moss green, faded signage | drifting papers, dust, crows |
| Safehouse | amber, brown, candle gold | dust motes, steam |
| Hospital / lab | sickly green-white, cold cyan, red alarm | flicker, steam vents |
| Rain / storm | slate blue, silver, black | streaks, lightning flash frame |
| Dawn / hope | rose-orange gradient, pale gold | mist, light rays |
| Horde reveal | bruise purple, black, sick-green eyes glow | fog, embers |

## Colour rules
- 3–4 dominant colours per scene + one accent (amber default, red for danger).
- Zombies read by **silhouette + sickly desaturated skin (grey-green/ashen) + pale eyes**; survivors read by **warmer skin tones + saturated clothing**. Keep that value/saturation contrast constant so viewers parse the frame instantly.
- Palette shifts follow story shifts (warm → cold when a place stops being safe).

## Graphic system (always available)
- **Chapter card:** dark charcoal panel, **hazard-stripe border** (amber/black), corner bolts, small label ("CHAPTER 7"), huge English word (e.g., "DAY 7"), tiny sub-label (e.g., "SURVIVAL THRILLER"), motif icons (crowbar, can, radio, key, bite-mark-free bandage, biohazard-free generic warning triangle).
- **Name ribbon:** small banner at first appearance (survivor = amber, zombie type = rust/red, place = grey).
- **Day/time stamp:** day counter + clock (e.g., "DAY 3 · 02:14").
- **Subtitles:** bottom centre, white bold with black outline, **spoken word highlighted yellow**. Keep clear of overlays.
- **HUD/meter set** (see `realism-layer.md`): water, food, ammo/stamina, noise, health, battery, distance-to-goal.
- **Warning elements:** caution tape strips, red "!" pop, rule cards ("RULE #3"), stamp ("INFECTED"/"CLEAR"), tick/cross marks.

## Typography
- English display: bold, slightly rough/stencil feel, off-white or amber with dark outline; red for danger words.
- Sub-labels in condensed sans/stencil caps, spaced.
- Typewriter/handwriting font for diary and notes.
- ≤ 7 words for headline text. Safe margins 5%, bottom 15% for subtitles.

## Motion language (cut-out)
- Humans: joint rotation, breathing bob, blink, walk-cycle leg swing; **fear = smaller, tighter posture, shaky hands, quick head turns**.
- Zombies: **jerky stutter** (hold-and-snap poses at 8–12 fps feel), head tilt, arm drag, shamble; runners = faster stride with lunge; crawlers = drag; keep each type's motion distinct and consistent.
- Camera: handheld drift (1–3 px random), slow push-in on dread, snap-zoom on reveal, whip-pan for threat, rack-focus by blurring layers, dolly along corridors.
- Light/FX loops: flicker, rain, fog drift, ember rise, dust in beams, red alarm pulse.
- Transitions: hard cut on sound, dip-to-black, flash-frame (lightning/alarm), iris wipe through a keyhole/binocular circle, match-cut on a prop, glitch only for CCTV/radio scenes.
- Beat length 2–8 s; **faster cuts as danger rises**, longer holds in silence.

## Variation rule
Each new video gets its own **colour story, locations, motif icons, camera rhythm and ending hook**. Only the cut-out look, character construction and hazard system persist.

## Aspect ratios
16:9 (1920×1080) default; 9:16 (1080×1920) for Shorts/Reels – keep threats in the **top-middle**, survivors lower, subtitles lower-middle.
