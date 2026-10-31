#!/usr/bin/env python3
"""Map a screen recording: what changes, when, and where the dead air is.

Screen recordings are usually variable frame rate, so this works from real frame timestamps.

    python footage_map.py recording.mp4 -o work/footage [--crop X,Y,W,H]
        writes frames/ (640 px JPEGs), change_log.json, timeline.md and overview contact sheets

    python footage_map.py sheet work/footage out.jpg 12.0 12.5 13.0 ...
        timestamped contact sheet for exact moments (run after the first command)

Read timeline.md first. It lists active spans and idle spans, which is what you need for deciding
where to speed up and which click starts a real-time clock.
"""
import argparse
import bisect
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

THUMB_W = 640
CHANGE_LEVEL = 12      # a pixel counts as changed above this difference (0-255), low enough for fades, above encoder noise
ACTIVE_PIXELS = 30     # frames with fewer changed thumbnail pixels than this count as idle


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout
    w, h = (int(x) for x in out.strip().split(",")[:2])
    pts = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "frame=pts_time",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout
    return w, h, [float(x.strip(",")) for x in pts.split() if x.strip(",")]


def load_font(size):
    for f in ("arialbd.ttf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf", "Helvetica.ttc"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def contact_sheet(frames_dir, pts, times, out, cols=4):
    width = int(1600 / cols)
    font = load_font(18)
    cells = []
    for t in times:
        i = max(bisect.bisect_right(pts, t) - 1, 0)
        im = Image.open(Path(frames_dir) / f"{i + 1:06d}.jpg").convert("RGB")
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 92, 24), fill=(255, 230, 0))
        d.text((4, 2), f"{pts[i]:.2f}", fill=(0, 0, 0), font=font)
        cells.append(im)
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (width * cols, cells[0].height * rows), "white")
    for k, im in enumerate(cells):
        sheet.paste(im, ((k % cols) * width, (k // cols) * cells[0].height))
    sheet.save(out, quality=85)


def spans(rows, duration):
    """Merge changed frames into active spans, keeping gaps shorter than 0.4 s together."""
    active = []
    for t, changed in rows:
        if changed < ACTIVE_PIXELS:
            continue
        if active and t - active[-1][1] < 0.4:
            active[-1][1] = t
            active[-1][2] = max(active[-1][2], changed)
        else:
            active.append([t, t, changed])
    out, cur = [], 0.0
    for a, b, peak in active:
        if a - cur > 0.5:
            out.append(("idle", cur, a, 0))
        out.append(("active", a, b, peak))
        cur = b
    if duration - cur > 0.5:
        out.append(("idle", cur, duration, 0))
    return out


def analyse(args):
    src = Path(args.recording)
    out = Path(args.o)
    frames = out / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    w, h, pts = probe(src)
    crop = [int(x) for x in args.crop.split(",")] if args.crop else [0, 0, w, h]
    th = int(round(crop[3] * THUMB_W / crop[2])) & ~1
    vf = f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]},scale={THUMB_W}:{th}"
    proc = subprocess.Popen(["ffmpeg", "-v", "quiet", "-i", str(src), "-vf", vf, "-fps_mode", "passthrough", "-pix_fmt", "bgr24",
                             "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    size = THUMB_W * th * 3
    prev, rows, i = None, [], 0
    while True:
        b = proc.stdout.read(size)
        if len(b) < size:
            break
        fr = np.frombuffer(b, np.uint8).reshape(th, THUMB_W, 3)
        i += 1
        cv2.imwrite(str(frames / f"{i:06d}.jpg"), fr, [cv2.IMWRITE_JPEG_QUALITY, 85])
        g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).astype(np.int16)
        if prev is not None and i <= len(pts):
            rows.append((pts[i - 1], int((np.abs(g - prev) > CHANGE_LEVEL).sum())))
        prev = g
    n = min(i, len(pts))
    pts = pts[:n]
    json.dump({"source": str(src), "size": [w, h], "crop": crop, "pts": pts, "changes": rows}, open(out / "change_log.json", "w"))
    dur = pts[-1] if pts else 0
    lines = [f"# Footage map: {src.name}", "", f"{w}x{h}, {n} frames, {dur:.2f} s, median frame step "
             f"{float(np.median(np.diff(pts))) * 1000:.0f} ms", "", "| kind | from | to | length | peak change |", "| --- | --- | --- | --- | --- |"]
    for kind, a, b, peak in spans(rows, dur):
        lines.append(f"| {kind} | {a:.2f} | {b:.2f} | {b - a:.2f} | {peak or ''} |")
    (out / "timeline.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    step = max(dur / 24, 1.0)
    ts = list(np.arange(0.5, dur, step))
    for k in range(0, len(ts), 24):
        contact_sheet(frames, pts, ts[k:k + 24], out / f"overview_{k // 24 + 1:02d}.jpg")
    print(f"{n} frames mapped. Read {out / 'timeline.md'} and the overview sheets.")


def sheet(argv):
    root, out = Path(argv[0]), argv[1]
    pts = json.load(open(root / "change_log.json"))["pts"]
    contact_sheet(root / "frames", pts, [float(x) for x in argv[2:]], out)
    print("wrote", out)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sheet":
        sheet(sys.argv[2:])
    else:
        ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
        ap.add_argument("recording")
        ap.add_argument("-o", required=True)
        ap.add_argument("--crop", help="X,Y,W,H of the app inside the recording, to cut browser chrome out of the analysis")
        analyse(ap.parse_args())
