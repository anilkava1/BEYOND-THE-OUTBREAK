#!/usr/bin/env python3
"""
Script-driven video builder.

  python3 studio/build.py                    # render every scene in script/script.json, then encode out/<name>.mp4
  python3 studio/build.py --scenes s02 s03   # re-render only these scenes (other scenes reuse frames/ from earlier runs)
  python3 studio/build.py --preview          # render ~1 frame per second of every scene -> out/preview.jpg (contact sheet), no video
  python3 studio/build.py --no-encode        # render frames only
  python3 studio/build.py --encode-only      # encode from existing frames/

Each scene id in the script must have scenes/<id>.py exposing  render(ctx).
"""
import argparse, importlib.util, json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from studio import engine as E  # noqa: E402

FRAMES = os.path.join(ROOT, "frames")
OUT = os.path.join(ROOT, "out")


class Ctx:
    """Passed to every scene's render(ctx)."""

    def __init__(self, scene, step=1, preview=False):
        self.scene = scene
        self.id = scene["id"]
        self.fps = E.FPS
        self.total = max(1, round(scene["seconds"] * E.FPS))
        self.step = step
        self.preview = preview
        self.dir = os.path.join(FRAMES, self.id + ("_preview" if preview else ""))
        shutil.rmtree(self.dir, ignore_errors=True)
        os.makedirs(self.dir, exist_ok=True)
        self.saved = 0

    @property
    def text(self):
        return self.scene.get("caption", "")

    def frames(self):
        """Iterate frame indexes of this scene (respects --preview step)."""
        return range(0, self.total, self.step)

    def t(self, f):
        """Scene progress 0..1 for frame f."""
        return f / self.total

    def sec(self, f):
        return f / self.fps

    def save(self, img, f):
        img.convert("RGB").save(os.path.join(self.dir, f"{f:06d}.jpg"), quality=93)
        self.saved += 1


def load_script(path):
    with open(path, encoding="utf-8") as fh:
        script = json.load(fh)
    ids = [s["id"] for s in script["scenes"]]
    if len(ids) != len(set(ids)):
        sys.exit("Duplicate scene ids in script.json")
    return script


def load_scene_module(scene_id):
    path = os.path.join(ROOT, "scenes", f"{scene_id}.py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location(f"scene_{scene_id}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def render_scene(scene, step, preview):
    mod = load_scene_module(scene["id"])
    if mod is None or not hasattr(mod, "render"):
        print(f"[missing] scenes/{scene['id']}.py with render(ctx) not found")
        return False
    ctx = Ctx(scene, step, preview)
    t0 = time.time()
    mod.render(ctx)
    print(f"[ok] {scene['id']}: {ctx.saved} frames in {time.time() - t0:.1f}s")
    return ctx.saved > 0


def contact_sheet(script):
    from PIL import Image
    thumbs = []
    for s in script["scenes"]:
        d = os.path.join(FRAMES, s["id"] + "_preview")
        if not os.path.isdir(d):
            continue
        files = sorted(os.listdir(d))
        pick = files[:: max(1, len(files) // 3)][:3] if files else []
        for fn in pick:
            thumbs.append(Image.open(os.path.join(d, fn)).resize((427, 240)))
    if not thumbs:
        return None
    cols = 3
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (427 * cols, 240 * rows), (0, 0, 0))
    for i, im in enumerate(thumbs):
        sheet.paste(im, ((i % cols) * 427, (i // cols) * 240))
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "preview.jpg")
    sheet.save(p, quality=88)
    return p


def encode(script):
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found. Install ffmpeg and make sure it is on PATH.")
    listing, total_sec = [], 0.0
    for s in script["scenes"]:
        d = os.path.join(FRAMES, s["id"])
        if not os.path.isdir(d) or not os.listdir(d):
            sys.exit(f"No frames for scene '{s['id']}'. Create scenes/{s['id']}.py and rebuild.")
        for fn in sorted(os.listdir(d)):
            listing.append(os.path.join(d, fn))
        total_sec += s["seconds"]
    lst = os.path.join(FRAMES, "frames.txt")
    with open(lst, "w", encoding="utf-8") as fh:
        for p in listing:
            fh.write(f"file '{p.replace(chr(92), '/')}'\nduration {1 / E.FPS:.6f}\n")
        fh.write(f"file '{listing[-1].replace(chr(92), '/')}'\n")
    out_cfg = script.get("output", {})
    name = out_cfg.get("name", "video.mp4")
    crf = str(out_cfg.get("crf", 27))
    os.makedirs(OUT, exist_ok=True)
    out_path = os.path.join(OUT, name)
    audio = script.get("audio", {}) or {}
    music = audio.get("file")
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst]
    vf = [f"fps={E.FPS}"]
    if out_cfg.get("scale"):
        vf.append(f"scale={out_cfg['scale']}")
    n_audio = 0
    if music and os.path.exists(os.path.join(ROOT, music)):
        cmd += ["-stream_loop", "-1", "-i", os.path.join(ROOT, music)]
        fc = f"[1:a]afade=t=in:d=2,afade=t=out:st={max(0, total_sec - 3)}:d=3[a]"
        n_audio = 1
    elif audio.get("ambient"):
        d = f"{total_sec:.2f}"
        cmd += ["-f", "lavfi", "-i", f"anoisesrc=d={d}:c=brown:r=44100:a=0.4",
                "-f", "lavfi", "-i", f"sine=f=55:d={d}:r=44100", "-f", "lavfi", "-i", f"sine=f=82:d={d}:r=44100"]
        fc = ("[1:a]lowpass=f=500,volume=0.9[n];[2:a]volume=0.2,tremolo=f=0.25:d=0.5[s1];[3:a]volume=0.07,tremolo=f=0.4:d=0.6[s2];"
              f"[n][s1][s2]amix=inputs=3:normalize=0,afade=t=in:d=2,afade=t=out:st={max(0, total_sec - 3):.2f}:d=3[a]")
        n_audio = 1
    cmd += ["-vf", ",".join(vf)]
    if n_audio:
        cmd += ["-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:a", "aac", "-b:a", "128k", "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", crf, "-maxrate", "3500k", "-bufsize", "7000k",
            "-preset", "medium", "-movflags", "+faststart", out_path]
    subprocess.run(cmd, check=True)
    print(f"[done] {out_path}  ({total_sec:.1f}s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", default=os.path.join(ROOT, "script", "script.json"))
    ap.add_argument("--scenes", nargs="*", help="only (re)render these scene ids")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--no-encode", action="store_true")
    ap.add_argument("--encode-only", action="store_true")
    a = ap.parse_args()
    script = load_script(a.script)
    todo = [s for s in script["scenes"] if not a.scenes or s["id"] in a.scenes]

    if a.encode_only:
        encode(script)
        return
    ok = True
    for s in todo:
        step = E.FPS if a.preview else 1
        ok = render_scene(s, step, a.preview) and ok
    if a.preview:
        p = contact_sheet(script)
        print(f"[preview] {p}" if p else "[preview] nothing rendered")
        return
    if not ok:
        sys.exit("Some scenes are missing. Design them in scenes/<id>.py first.")
    if not a.no_encode:
        encode(script)


if __name__ == "__main__":
    main()
