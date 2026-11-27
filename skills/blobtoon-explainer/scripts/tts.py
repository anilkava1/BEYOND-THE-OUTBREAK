#!/usr/bin/env python3
"""Optional voice-over. Adds shot['voice'] mp3 files using edge-tts (pip install edge-tts, needs internet).
Text spoken = shot['say'] if present else shot['caption']. Hindi voices read Devanagari best; en-IN-NeerjaNeural reads Hinglish OK.
Usage: python tts.py story.json [--voice en-IN-NeerjaNeural] [--rate +0%]"""
import argparse, asyncio, json, os, sys
try: import edge_tts
except ImportError: sys.exit("edge-tts missing: pip install edge-tts (voice is optional, video works without it)")
ap = argparse.ArgumentParser(); ap.add_argument("story"); ap.add_argument("--voice", default="en-IN-NeerjaNeural"); ap.add_argument("--rate", default="+0%"); a = ap.parse_args()
story = json.load(open(a.story)); os.makedirs("voice", exist_ok=True)
async def go():
    for i, s in enumerate(story["shots"], 1):
        txt = s.get("say") or s.get("caption")
        if not txt: continue
        p = f"voice/shot_{i:02d}.mp3"; await edge_tts.Communicate(txt, a.voice, rate=a.rate).save(p); s["voice"] = p; print("voice", p)
asyncio.run(go()); json.dump(story, open(a.story, "w"), ensure_ascii=False, indent=1); print("story updated with voice files")
