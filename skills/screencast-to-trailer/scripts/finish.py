#!/usr/bin/env python3
"""Marry the silent render with the mix and check the result.

    python finish.py renders/silent.mp4 audio/mix.wav deliver/film.mp4 [--sheet deliver/qa]

The video stream is copied untouched. The limiter is tightened until the encoded AAC measures at or under -1 dBTP,
because AAC encoding adds inter-sample peaks the limiter cannot see. Prints loudness and writes one contact sheet
every 2 seconds so the whole film can be read at a glance, plus a list of near-uniform frames (flash frames, blanks).
"""
import argparse
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def ff(*args):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(r.stderr[-1500:])
    return r.stderr


def loudness(path):
    s = ff("-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-")
    s = s[s.rfind("Summary:"):]
    return (float(re.search(r"I:\s+(-?[\d.]+) LUFS", s).group(1)), float(re.search(r"LRA:\s+(-?[\d.]+) LU", s).group(1)),
            float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", s).group(1)))


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,avg_frame_rate:format=duration,size",
                          "-of", "default=nw=1", str(path)], capture_output=True, text=True).stdout
    return " ".join(out.split())


def sheets(video, folder, every=2.0, cols=5, rows=6, w=384, h=216):
    """Labelled in Python because ffmpeg's drawtext depends on a fontconfig setup many builds do not have."""
    p = subprocess.Popen(["ffmpeg", "-v", "quiet", "-i", str(video), "-vf", f"fps=1/{every},scale={w}:{h}", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    n, page, canvas = 0, 1, None
    while True:
        b = p.stdout.read(w * h * 3)
        if len(b) < w * h * 3:
            break
        k = n % (cols * rows)
        if k == 0:
            if canvas:
                canvas.save(folder / f"sheet_{page:02d}.jpg", quality=85)
                page += 1
            canvas = Image.new("RGB", (w * cols, h * rows), "white")
        cell = Image.frombytes("RGB", (w, h), b)
        d = ImageDraw.Draw(cell)
        d.rectangle((0, 0, 58, 16), fill=(255, 230, 0))
        d.text((4, 2), f"{int(n * every // 60)}:{n * every % 60:04.1f}", fill=(0, 0, 0))
        canvas.paste(cell, ((k % cols) * w, (k // cols) * h))
        n += 1
    if canvas:
        canvas.save(folder / f"sheet_{page:02d}.jpg", quality=85)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("mix")
    ap.add_argument("out")
    ap.add_argument("--sheet", help="folder for the QA contact sheets")
    a = ap.parse_args()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    for limit in (0.86, 0.82, 0.78, 0.74, 0.70):
        ff("-y", "-i", a.video, "-i", a.mix, "-map", "0:v", "-map", "1:a", "-af", f"alimiter=limit={limit}:attack=4:release=80:level=disabled",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out))
        lufs, lra, tp = loudness(out)
        print(f"limit {limit}: {lufs} LUFS, LRA {lra}, true peak {tp} dBTP")
        if tp <= -1.0:
            break
    else:
        print("true peak still above -1 dBTP: trim the hottest cues in the mix instead of limiting harder")
    print(probe(out))
    if a.sheet:
        d = Path(a.sheet)
        d.mkdir(parents=True, exist_ok=True)
        sheets(out, d)
        print("contact sheets:", d)
        p = subprocess.Popen(["ffmpeg", "-v", "quiet", "-i", str(out), "-vf", "fps=10,scale=64:36,format=gray", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
        flat, i = [], 0
        while True:
            b = p.stdout.read(64 * 36)
            if len(b) < 64 * 36:
                break
            if np.frombuffer(b, np.uint8).std() < 2:
                flat.append(i / 10)
            i += 1
        print("near-uniform moments (s), check they are intended:", flat[:40] if flat else "none")


if __name__ == "__main__":
    main()
