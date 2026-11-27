# Allowed values
**Characters:** pico (hero, yellow), remy (blue, curly hair), mia (pink, brown bob), zed (teal, red beanie), ollie (orange, blue cap), sam (navy suit adult/teacher/boss)
**Locations:** bedroom_night, classroom, living_room, street_sunset, cafe, stage, bus, park
**pose:** idle, talk, wave, think, point, shrug, cheer, stress, sit, walk (auto when to_x is set)
**expr:** neutral, happy, sad, angry, surprised, worried, smug, sleepy
**look:** center, camera, left, right, up, down, up_left, up_right
**sfx:** pop (default), whoosh, ding, none
**camera.zoom:** [start, end] e.g. [1.0,1.12]; **camera.focus:** [fx,fy] 0..1

# Location -> good for
bedroom_night: procrastination, sleep, studying, thoughts | classroom: exams, school, facts | living_room: family, money talk, news | street_sunset: walking, friends, journeys | cafe: hangout, food, gossip, business | stage: confidence, fear, fame, results | bus: commute, ideas, strangers | park: nature, health, calm, lessons learned

# Examples
Panic: pose stress + expr surprised. Idea: pose point + expr happy + look up. Doubt: pose think + expr worried. Win: pose cheer + expr happy. Bad news: pose shrug + expr sad.

# v2 additions (zombie genre)
**Characters (extra):** doc (scientist, white coat+glasses), zombie, zombie_girl, zombie_boss (bigger), zombie_remy, zombie_ollie (zombies auto-use stiff `zwalk` + `zombie` face)
**Locations (extra):** ruined_street (burning city, wrecked car), abandoned_school (red emergency light, desk barricade), supermarket (shelves, cart), rooftop (night skyline, railing), lab (green tubes, screens), hospital (ward beds, IV stands, nurse station), hospital_hall (perspective corridor, red exit sign)
**pose (extra):** run, zwalk, cower, defend (bat raised)
**expr (extra):** scared, terrified, determined, zombie, groan
**prop (right hand):** none, bat, flashlight
**fx:** fog, shake, red_alert, flicker | **grade:** none, horror (auto "horror" when genre=zombie) | **horde:** 0-12 | **sfx (extra):** growl, alarm, boom, heartbeat
