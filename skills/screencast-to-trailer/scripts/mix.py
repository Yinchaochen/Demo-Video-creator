#!/usr/bin/env python3
"""Mix the score and the sound design to picture, and report what a listener would notice.

    python mix.py cues.json

cues.json:
    {
      "music": "audio/music_edit.wav",
      "sfx_dir": "audio/sfx",
      "output": "audio/mix.wav",
      "music_lufs": -16.5,
      "target_lufs": -14,
      "duck": [[0, 0], [31.4, 0], [32.2, -3.5], [77, -3.5], [78, 0]],   // [time, dB] automation of the score
      "cues": [
        {"sound": "hit", "t": 9.62, "gain": -8, "dur": 3.6},            // the sound's loudest 10 ms lands on t
        {"sound": "rustle", "t": 2.6, "gain": -30, "at": "start", "hp": 900, "dur": 6.8},
        {"sound": "reverse_cymbal", "t": 27.0, "gain": -14, "at": "end"}
      ]
    }

Each sound is peak-normalised to -1 dBFS first, so "gain" reads as level against full scale. "at" is what lands on t:
peak (default), start or end. "dur" cuts a long tail with a fade. "hp" is a high-pass in Hz.

The report flags cues that peak less than 4 dB over the score around them (they will be lost) and names the
seconds where the sum overshoots, which is where to trim hits instead of leaning on the limiter.
Peak over score is a proxy for audibility, not a replacement for listening when you can.
"""
import json
import sys
from pathlib import Path

import librosa
import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy.signal import butter, sosfilt

SR = 48000


def load(path, cache={}):
    p = str(path)
    if p not in cache:
        y, sr = sf.read(p, dtype="float32", always_2d=True)
        y = np.repeat(y, 2, axis=1) if y.shape[1] == 1 else y[:, :2]
        if sr != SR:
            y = np.stack([librosa.resample(y[:, k], orig_sr=sr, target_sr=SR) for k in range(2)], axis=1)
        cache[p] = y / (np.abs(y).max() + 1e-9) * 10 ** (-1 / 20)
    return cache[p]


def peak_index(y):
    n = int(0.01 * SR)
    return int(np.argmax(np.convolve(y.mean(axis=1) ** 2, np.ones(n) / n, "same")))


def rms_db(a):
    return 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-9)


def main(path):
    spec = json.load(open(path, encoding="utf-8"))
    music, sr = sf.read(spec["music"], dtype="float32", always_2d=True)
    if sr != SR:
        raise SystemExit("music must be 48 kHz; music_edit.py writes it that way")
    music = np.repeat(music, 2, axis=1) if music.shape[1] == 1 else music[:, :2]
    n = len(music)
    meter = pyln.Meter(SR)
    raw = meter.integrated_loudness(music)
    t_axis = np.arange(n) / SR
    duck = spec.get("duck", [[0, 0]])
    gain = 10 ** (np.interp(t_axis, [d[0] for d in duck], [d[1] for d in duck]) / 20)
    music = music * gain[:, None] * 10 ** ((spec.get("music_lufs", -16.5) - raw) / 20)
    fx = np.zeros((n, 2), dtype=np.float32)
    lost = []
    for c in spec["cues"]:
        y = load(Path(spec["sfx_dir"]) / f"{c['sound']}.wav").copy()
        if "hp" in c:
            y = sosfilt(butter(3, c["hp"], "hp", fs=SR, output="sos"), y, axis=0).astype(np.float32)
        at = c.get("at", "peak")
        p = peak_index(y) if at == "peak" else 0 if at == "start" else len(y)
        if "dur" in c:
            m = int(c["dur"] * SR)
            f = min(int(0.5 * SR), m // 2)
            if at == "start":
                y = y[:m].copy()
                y[:f] *= np.linspace(0, 1, f)[:, None]
                y[-f:] *= np.linspace(1, 0, f)[:, None]
            else:
                y = y[:p + m].copy()
                y[-f:] *= (np.cos(np.linspace(0, np.pi / 2, f)) ** 2)[:, None]
        a = int(round(c["t"] * SR)) - p
        s0, e0 = max(a, 0), min(a + len(y), n)
        if s0 >= e0:
            continue
        fx[s0:e0] += y[s0 - a:e0 - a] * 10 ** (c["gain"] / 20)
        i = int(c["t"] * SR)
        over = 20 * np.log10(np.abs(y).max() + 1e-9) + c["gain"] - rms_db(music[max(i - SR // 5, 0):i + SR // 5])
        if over < 4:
            lost.append((c["t"], c["sound"], round(float(over), 1)))
    mix = music + fx
    lufs = meter.integrated_loudness(mix)
    mix = mix * 10 ** ((spec.get("target_lufs", -14.0) - lufs) / 20)
    dst = Path(spec.get("output", "audio/mix.wav"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    sf.write(dst, mix, SR, subtype="FLOAT")
    env = np.abs(mix).max(axis=1)
    hot = []
    for i in range(0, n, SR // 2):
        p = float(env[i:i + SR // 2].max())
        if p > 1.26:
            hot.append((round(i / SR, 1), round(20 * np.log10(p), 1)))
    print(f"{dst}: {len(spec['cues'])} cues, {n / SR:.2f} s, {spec.get('target_lufs', -14.0)} LUFS before limiting")
    print("overshoot above +2 dBFS (trim the hits here):", hot or "none")
    print("cues likely lost under the score (t, sound, dB over score):", lost or "none")


if __name__ == "__main__":
    main(sys.argv[1])
