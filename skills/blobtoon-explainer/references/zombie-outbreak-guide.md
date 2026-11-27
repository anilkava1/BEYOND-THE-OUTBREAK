# Zombie Outbreak guide (genre = "zombie")
Set `"genre":"zombie"` in `meta`. This auto-enables: toxic-green titles, desaturated horror grade on backgrounds, tense music with heartbeat.
Look at `references/sheets/cast-sheet.png`, `poses-sheet.png`, `locations-sheet.png` before writing.

## Style rules (keep it cartoon, NOT gore)
- Kid-safe "TV-Y7" horror: scary mood through color, fog, red alert, shake and growl sfx. **No blood, no gore, no weapons beyond bat/flashlight, no killing shown.**
- Zombies = green-gray head, yellow eyes with red pupils (uneven), jagged mouth, torn hoodie with stitches, stiff arms forward (`zwalk` is automatic for zombie names).
- Survivors stay normal blobs (pico yellow hero). Emotion via `expr`: scared, terrified, determined, worried, sad.
- A friend turning into a zombie = swap `remy` -> `zombie_remy` (also zombie_girl, zombie_boss, zombie_ollie, plain `zombie`). Never recolor.

## Cast roles
pico = hero (always in shot) | remy = loyal best friend (can get infected = twist) | mia = smart planner | zed/ollie = comic relief or infected | sam = teacher/boss/mayor | doc = scientist with the cure/plan.

## Locations -> story beat
park/cafe/classroom (normal day, grade "none") -> street_sunset (first rumors) -> ruined_street (outbreak, `horde`) -> supermarket (supplies, hiding) -> abandoned_school (barricade, loss) -> lab (cure/answer) -> rooftop (climax / rescue) -> bedroom_night (calm after, or sting).

## Tools for tension
- `horde: N` (5-10) = background zombies that slowly grow closer during the shot. Use in shots 3, 8, climax.
- `fx`: `fog` (mood), `shake` (impact/run), `red_alert` (danger/bad news), `flicker` (power failing).
- `sfx`: growl (zombie appears), alarm (news/siren), boom, ding (relief), heartbeat, pop, whoosh.
- `prop`: bat or flashlight on the RIGHT hand only. Bat with idle pose auto-uses `defend`.
- Running: `{"x":0.2,"to_x":0.8,"run":true}`. Zombies never run; they use `to_x` slowly.
- Normal-world opening shots: set `"grade":"none"` so the contrast hits when horror starts.

## Short (<=60s) beat sheet: 11-14 shots x 3.5-4.5s
1 HOOK title + normal day (grade none) | 2 first sign (news, alarm) | 3 first zombies (horde, fog) | 4 chase (run, shake, growl) | 5 hide (cower) | 6 plan (bat/flashlight) | 7 emotional twist (friend bitten, red_alert) | 8 answer (doc/lab) | 9 climax (rooftop, horde) | 10 relief (cheer, ding, grade none) | 11 cliffhanger title "To be continued" + zombie_remy.
Template: `templates/story_zombie_short.json` (already valid, 41s).

## Long (<=300s) beat sheet: 45-60 shots x 4-6s
ACT 1 (0:00-0:50) hook, normal life, first rumors, news.  ACT 2 (0:50-2:00) outbreak, escape, losing home, new allies.  ACT 3 (2:00-3:30) hiding, supplies, internal conflict, friend infected, tough choice.  ACT 4 (3:30-4:30) cure plan, lab, big chase, rooftop climax.  ACT 5 (4:30-5:00) rescue, lesson, cliffhanger + "like/subscribe" caption.
Template: `templates/story_zombie_long.json` (placeholder beats; copy shots to extend to ~55).
Keep a recurring location every 4-6 shots and vary `camera.zoom` ([1.0,1.1] push-in, [1.12,1.0] pull-out).

## Caption bank (Hinglish, 8-12 words max)
Hook: "Din 1: shehar me kuch ajeeb ho raha tha." / "Kisi ne suna? Ye awaaz kahan se aa rahi hai?"
Fear: "Wo ruke nahi... wo bas chalte rahe." / "Darwaza band karo! Jaldi!"
Plan: "Rule 1: shor mat karo. Rule 2: kabhi akele mat jao."
Twist: "Aur tab pata chala... wo bhi infected tha."
Hope: "Antidote mil gaya! Bas ek aur koshish!"
End: "Part 2 chahiye? Comment karo YES."

## Topic ideas
School outbreak | Mall outbreak | Last bus to safety | Night in the supermarket | Zombie Day 100 | How to survive 24 hours | Cure hunters | Rooftop rescue
