# Dark Video Studio

Script likho, opencode se visuals design karwao, aur MP4 render karo. **Isme koi fixed visual ya bana-banaya scene nahi hai.** `scenes/` khaali hai. opencode har scene ko `script/script.json` ke hisaab se khud design karega, aur ye project sirf tools (lighting, fog, glow, characters, camera, caption) deta hai.

## Requirements
- Python 3.9+
- ffmpeg (PATH mein), check: `ffmpeg -version`
- `pip install -r requirements.txt` (Pillow, numpy)

## Setup
```bash
unzip dark-video-studio.zip
cd dark-video-studio
pip install -r requirements.txt
```

## Use kaise karein
1. `script/script.json` mein apni script likho (ya opencode ko plain text script do aur bolo "script.json mein convert karo").
   - `seconds`: scene ki length
   - `narration`: kya bola ja raha hai (reference ke liye)
   - `visual`: kya dikhna chahiye (jitna detail utna accha)
   - `caption`: screen par bada text (khali chhod sakte ho)
   - `style`: poore video ka look/mood
   - `audio.ambient`: true to halka dark ambient sound; `audio.file`: apni music file (jaise `assets/music.mp3`)
2. Project folder mein `opencode` chalao aur ye prompt do:
   > AGENTS.md aur script/script.json padho. Har scene ko script ke hisaab se design karo scenes/ mein (koi fixed visual nahi), `python3 studio/build.py --preview` se check karo, jo khali ya flat lage use fix karo, phir `python3 studio/build.py` se out/video.mp4 banao.
3. Result: `out/video.mp4`

## Commands
```bash
python3 studio/build.py --preview        # har scene ke kuch frames -> out/preview.jpg (jaldi check)
python3 studio/build.py                  # poori video render + encode
python3 studio/build.py --scenes s02     # sirf ek scene dobara render, baaki purane frames use honge
python3 studio/build.py --no-encode      # sirf frames
python3 studio/build.py --encode-only    # existing frames se video
```

## Folder structure
```
script/script.json   <- aapki script (yahin se sab decide hota hai)
scenes/              <- opencode yahan har scene ka code likhega (shuru mein khaali)
studio/engine.py     <- drawing tools: lighting, fog, glow, characters, camera, caption
studio/build.py      <- script padh kar scenes render karta hai aur ffmpeg se video banata hai
docs/PRIMITIVES.md   <- sab tools ki list
examples/api_reference.py <- sirf API ka example (visual copy nahi karna)
AGENTS.md            <- opencode ke liye rules aur workflow
out/  frames/        <- output aur temporary frames
```

## Notes
- Video size 1280x720, 30fps. Bada chahiye to `output.scale` mein `"1920:1080"` likho (sirf upscale hota hai).
- Render speed approx 0.1 se 0.3 second per frame. 36 sec ki video mein kuch minute lagte hain.
- Default font English ke liye hai. Hindi (Devanagari) caption chahiye to `assets/fonts/` mein koi Devanagari font daalo.
- Sound sirf ambient ya aapki music file hai. Voiceover ke liye alag audio file banake `audio.file` mein do.
