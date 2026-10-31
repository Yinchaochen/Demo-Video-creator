#!/usr/bin/env python3
"""Turn the raw recording into constant-frame-rate footage for the film.

    python retime.py spec.json

spec.json:
    {
      "source": "recording.mp4",
      "crop": [0, 126, 2416, 1314],             // the app, without browser tabs or the address bar
      "fps": 60,
      "output": "film/assets/master.mp4",
      "knots": [[31.8, 9.2], [34.2, 11.3], [38.1, 12.74]],   // [film time, recording time], piecewise linear
      "stills": {"st_form": 11.4},              // optional, saved as PNGs next to the output in stills/
      "redactions": [
        {"rect": [986, 219, 860, 72], "from": 57.0, "to": 108.1, "fill": [250, 250, 250]},
        {"rect": [986, 293, 860, 73], "from": 57.0, "to": 108.1, "fill": [250, 250, 250],
         "tile": "work/row_tile.png", "fade_ref": "work/final_frame.png", "settled": 61.0}
      ]
    }

Coordinates in rect are in the cropped picture, times in the recording. A redaction overwrites its whole rectangle in
every frame of its range, so nothing underneath survives. "tile" (same size as the cropped picture, with alpha) paints
replacement content. "fade_ref" is a cropped frame where the original content is fully visible: the script measures how
far the original has faded in and fades the replacement the same way, until "settled", after which it stays at full.
"""
import bisect
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def recording_pts(src):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "frame=pts_time", "-of", "csv=p=0", src],
                         capture_output=True, text=True, check=True).stdout
    return [float(x.strip(",")) for x in out.split() if x.strip(",")]


class Redactions:
    def __init__(self, items):
        self.items = []
        for it in items:
            x, y, w, h = it["rect"]
            r = dict(it, x=x, y=y, w=w, h=h, fill=np.array(it.get("fill", [255, 255, 255]), dtype=np.float32))
            if "tile" in it:
                t = np.array(Image.open(it["tile"]).convert("RGBA")).astype(np.float32)[y:y + h, x:x + w]
                a = t[..., 3:4] / 255
                r["comp"] = r["fill"] * (1 - a) + t[..., :3] * a
            if "fade_ref" in it:
                f = np.array(Image.open(it["fade_ref"]).convert("RGB")).astype(np.float32)[y:y + h, x:x + w].mean(2) - r["fill"].mean()
                r["ref"], r["ref2"] = f, float((f * f).sum()) + 1e-6
            self.items.append(r)

    def apply(self, frame, s):
        for r in self.items:
            if not r["from"] <= s < r["to"]:
                continue
            x, y, w, h = r["x"], r["y"], r["w"], r["h"]
            if "comp" not in r:
                frame[y:y + h, x:x + w] = r["fill"].astype(np.uint8)
                continue
            a = 1.0
            if "ref" in r and s < r.get("settled", r["to"]):
                cur = frame[y:y + h, x:x + w].astype(np.float32).mean(2) - r["fill"].mean()
                a = float((cur * r["ref"]).sum() / r["ref2"])
                a = 0.0 if a < 0.04 else 1.0 if a > 0.97 else a
            frame[y:y + h, x:x + w] = np.clip(r["fill"] * (1 - a) + r["comp"] * a, 0, 255).astype(np.uint8)
        return frame


def main(path):
    spec = json.load(open(path, encoding="utf-8"))
    src, (cx, cy, cw, ch), fps = spec["source"], spec["crop"], spec.get("fps", 60)
    if cw % 2 or ch % 2:
        raise SystemExit("crop width and height must be even")
    knots = spec["knots"]
    ft, st = [k[0] for k in knots], [k[1] for k in knots]
    if any(b < a for a, b in zip(st, st[1:])) or any(b <= a for a, b in zip(ft, ft[1:])):
        raise SystemExit("knots must move forward in both film and recording time")
    pts = recording_pts(src)
    red = Redactions(spec.get("redactions", []))
    n = int(round((ft[-1] - ft[0]) * fps))
    want = sorted(spec.get("stills", {}).items(), key=lambda kv: kv[1])
    last_s = max([st[-1]] + [s for _, s in want])
    stills_dir = Path(spec["output"]).parent / "stills"
    if want:
        stills_dir.mkdir(parents=True, exist_ok=True)
    Path(spec["output"]).parent.mkdir(parents=True, exist_ok=True)
    dec = subprocess.Popen(["ffmpeg", "-v", "quiet", "-i", src, "-vf", f"crop={cw}:{ch}:{cx}:{cy}", "-fps_mode", "passthrough",
                            "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], stdout=subprocess.PIPE, bufsize=10 ** 8)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{cw}x{ch}", "-r", str(fps), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p", "-g", str(fps // 2), spec["output"]], stdin=subprocess.PIPE)
    size = cw * ch * 3
    # walk the recording once: frames arrive in order, film frames and stills ask for them in order
    requests = [(float(np.interp(ft[0] + k / fps, ft, st)), "film", None) for k in range(n)] + [(s, "still", name) for name, s in want]
    requests.sort(key=lambda r: r[0])
    idx, buf, written = -1, None, {}
    films = []
    for s, kind, name in requests:
        target = max(bisect.bisect_right(pts, s) - 1, 0)
        while idx < target:
            b = dec.stdout.read(size)
            if len(b) < size:
                raise SystemExit(f"recording ended at frame {idx}, wanted {target}")
            buf, idx = b, idx + 1
        fr = red.apply(np.frombuffer(buf, np.uint8).reshape(ch, cw, 3).copy(), s)
        if kind == "still":
            Image.fromarray(fr).save(stills_dir / f"{name}.png", optimize=True)
            written[name] = s
        else:
            enc.stdin.write(fr.tobytes())
            films.append(s)
    enc.stdin.close()
    enc.wait()
    dec.kill()
    print(f"{spec['output']}: {len(films)} frames at {fps} fps, {len(films) / fps:.2f} s; recording used up to {last_s:.2f} s; stills {list(written)}")


if __name__ == "__main__":
    main(sys.argv[1])
