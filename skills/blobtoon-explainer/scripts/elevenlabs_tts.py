#!/usr/bin/env python3
"""ElevenLabs voice-over for BlobToon stories.

Usage:
    python elevenlabs_tts.py story.json [--voice VOICE_ID] [--model MODEL] [--force] [--workers 4]

Reads ELEVENLABS_API_KEY from .env in the current folder (or --env PATH).
Writes voice/shot_XX.mp3 next to the story and adds shot["voice"] paths.
Default voice is Adam (built-in, available on free plans).
"""
import argparse
import concurrent.futures
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

DEFAULT_VOICE = "pNInz6obpgDQGcFmaJgB"  # Adam, built-in English narrator
DEFAULT_MODEL = "eleven_multilingual_v2"
API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}"


def load_env(path):
    cfg = {}
    p = pathlib.Path(path)
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


def synth(text, voice, model, api_key, out_path, retries=4):
    body = json.dumps({
        "text": text,
        "model_id": model,
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }).encode("utf-8")
    req = urllib.request.Request(
        API.format(voice=voice), data=body, method="POST",
        headers={"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
    )
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if not data:
                raise RuntimeError("empty audio response")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(data)
            return len(data)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            last = f"HTTP {e.code}: {detail}"
            if e.code in (400, 401, 402, 403):
                break
            time.sleep(2 ** attempt)
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
            time.sleep(2 ** attempt)
    raise RuntimeError(last or "unknown error")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("story")
    ap.add_argument("--voice", default=os.environ.get("ELEVENLABS_VOICE_ID") or DEFAULT_VOICE)
    ap.add_argument("--model", default=os.environ.get("ELEVENLABS_MODEL") or DEFAULT_MODEL)
    ap.add_argument("--env", default=".env")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()

    cfg = load_env(a.env)
    api_key = cfg.get("ELEVENLABS_API_KEY") or os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY missing (put it in .env)")

    story_path = pathlib.Path(a.story).resolve()
    story = json.loads(story_path.read_text(encoding="utf-8"))
    shots = story.get("shots", [])
    voice_dir = story_path.parent / "voice"
    voice_dir.mkdir(parents=True, exist_ok=True)

    jobs = []
    for i, sh in enumerate(shots, 1):
        text = (sh.get("say") or sh.get("caption") or "").strip()
        if not text:
            continue
        out = voice_dir / f"shot_{i:02d}.mp3"
        rel = out.relative_to(pathlib.Path.cwd()).as_posix() if out.is_relative_to(pathlib.Path.cwd()) else str(out)
        sh["voice"] = rel
        if out.exists() and not a.force:
            print(f"skip {out.name} (exists)")
            continue
        jobs.append((i, text, out))

    if jobs:
        print(f"ElevenLabs: {len(jobs)} clips | voice={a.voice} | model={a.model}")
        failures = []

        def run(job):
            i, text, out = job
            try:
                n = synth(text, a.voice, a.model, api_key, out)
                print(f"  shot {i:02d}: {n} bytes")
            except Exception as e:
                failures.append((i, str(e)))
                print(f"  shot {i:02d}: FAIL {e}")
            return i

        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, a.workers)) as ex:
            list(ex.map(run, jobs))
        if failures:
            print("FAILURES:", failures)
            sys.exit(1)

    story_path.write_text(json.dumps(story, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"updated {story_path} with {len(shots)} voice paths")


if __name__ == "__main__":
    main()
