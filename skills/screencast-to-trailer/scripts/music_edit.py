#!/usr/bin/env python3
"""Cut a track to the film's structure from a list of segments.

    python music_edit.py spec.json

spec.json:
    {
      "source": "assets/music/track.mp3",
      "segments": [[1.5, 3.9], [15.9, 23.1], [54.3, 83.7]],
      "output": "audio/music_edit.wav",
      "end_fade": 1.6
    }

Segment times are in the track. Each join is snapped to the real attack (within 30 ms of the bar line you gave)
and joined with a 40 ms equal-power crossfade that ends on the attack, so the transient stays whole.
Writes the wav and <output>.map.json with film time <-> track time for every segment.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

SR = 48000
XF = 0.040


def to_wav(path):
    p = Path(path)
    if p.suffix.lower() == ".wav":
        info = sf.info(str(p))
        if info.samplerate == SR:
            return p
    out = Path(tempfile.mkdtemp()) / (p.stem + "_48k.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(p), "-ar", str(SR), "-c:a", "pcm_f32le", str(out)], check=True)
    return out


def main(spec_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    y, _ = sf.read(to_wav(spec["source"]), dtype="float32", always_2d=True)
    if y.shape[1] == 1:
        y = np.repeat(y, 2, axis=1)
    mono = y.mean(axis=1)

    def refine(t, win=0.03):
        a, b = max(int((t - win - 0.08) * SR), 0), int((t + win + 0.08) * SR)
        env = librosa.onset.onset_strength(y=mono[a:b], sr=SR, hop_length=64)
        ts = librosa.frames_to_time(np.arange(len(env)), sr=SR, hop_length=64) + a / SR
        ok = np.abs(ts - t) <= win
        return float(ts[ok][np.argmax(env[ok])]) if ok.any() else t

    x = int(XF * SR)
    out = np.zeros((0, 2), dtype=np.float32)
    table = []
    segs = spec["segments"]
    for k, (a, b) in enumerate(segs):
        ra = refine(a) if k else a                   # the first segment keeps its own start
        rb = refine(b) if k + 1 < len(segs) else b   # the last segment keeps its own end
        seg = y[int(round(ra * SR)) - (x if k else 0):int(round(rb * SR))].copy()
        if k:
            seg[:x] *= np.sin(np.linspace(0, np.pi / 2, x))[:, None]
            out[-x:] *= np.cos(np.linspace(0, np.pi / 2, x))[:, None]
            start = len(out) - x
            buf = np.zeros((start + len(seg), 2), dtype=np.float32)
            buf[:len(out)] = out
            buf[start:start + len(seg)] += seg
            out, film_in = buf, (start + x) / SR
        else:
            out, film_in = seg, 0.0
        table.append({"track_in": round(ra, 4), "track_out": round(rb, 4), "film_in": round(film_in, 4)})
        print(f"segment {k}: track {ra:.3f}-{rb:.3f} -> film {film_in:.3f}")
    n = int(spec.get("end_fade", 1.6) * SR)
    if n:
        out[-n:] *= (np.cos(np.linspace(0, np.pi / 2, n)) ** 2)[:, None]
    dst = Path(spec["output"])
    dst.parent.mkdir(parents=True, exist_ok=True)
    sf.write(dst, out, SR, subtype="FLOAT")
    total = len(out) / SR
    json.dump({"seconds": total, "segments": table}, open(str(dst) + ".map.json", "w"), indent=1)
    print(f"{dst}: {int(total // 60)}:{total % 60:05.2f}. To place a musical event in the film: "
          "film time = segment film_in + (track time - segment track_in).")


if __name__ == "__main__":
    main(sys.argv[1])
