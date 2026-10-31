#!/usr/bin/env python3
"""Synthesize a small starter sound kit, so a film can be scored with no downloads and no licence questions.

    python make_sfx.py audio/sfx

Everything here is generated from noise and sine waves by this script, so the output carries no third-party rights.
Recorded sounds from Freesound or Kenney usually sound richer (see references/sound-design.md); use these as the
baseline and swap in better ones when you can. The names match the example cue sheet.
"""
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

SR = 48000
R = np.random.default_rng(7)


def t_(d):
    return np.arange(int(d * SR)) / SR


def noise(d):
    return R.normal(0, 1, int(d * SR))


def lp(x, f):
    return sosfilt(butter(4, f, "lp", fs=SR, output="sos"), x)


def hp(x, f):
    return sosfilt(butter(4, f, "hp", fs=SR, output="sos"), x)


def sweep_filter(x, f0, f1, width=1.0):
    """Band-pass sweep by overlapping short filtered blocks; good enough for air and whooshes."""
    n, hop = len(x), 2048
    out = np.zeros(n + hop)
    win = np.hanning(hop)
    for i in range(0, n - hop, hop // 2):
        f = f0 * (f1 / f0) ** (i / n)
        lo, hi = max(f / (1 + width), 30), min(f * (1 + width), SR / 2 - 100)
        seg = sosfilt(butter(2, [lo, hi], "bp", fs=SR, output="sos"), x[i:i + hop] * win)
        out[i:i + hop] += seg
    return out[:n]


def hit(d=3.2):
    t = t_(d)
    sub = np.sin(2 * np.pi * (34 * t + 28 * (1 - np.exp(-t * 16)) / 16)) * np.exp(-t * 1.5)
    body = lp(noise(d), 900) * np.exp(-t * 7) * 0.7
    click = hp(noise(d), 2500) * np.exp(-t * 60) * 0.35
    return sub + body + click


def metal_hit(d=2.0, f0=142.0):
    t = t_(d)
    x = sum(a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t * k) for r, a, k in ((1, 1, 2.2), (2.76, .6, 3.4), (5.4, .4, 5), (8.93, .25, 8)))
    return x + lp(noise(d), 300) * np.exp(-t * 9) * 1.2 + np.sin(2 * np.pi * 48 * t) * np.exp(-t * 3)


def braam(d=2.2):
    t = t_(d)
    env = np.minimum(t / .02, 1) * np.exp(-t * 1.4)
    x = sum(np.sign(np.sin(2 * np.pi * f * t)) * a for f, a in ((55, 1), (55.7, .8), (82.5, .5)))
    return lp(x, 900) * env


def riser(d=2.4):
    t = t_(d)
    return sweep_filter(noise(d), 300, 7000, .6) * (t / d) ** 2.2


def reverse_cymbal(d=1.3):
    t = t_(d)
    return hp(noise(d), 3500) * (t / d) ** 3.5


def reverse_bass(d=1.7):
    t = t_(d)
    return np.sin(2 * np.pi * (40 + 40 * t / d) * t) * (t / d) ** 3


def whoosh(d=.8, f0=300, f1=3000):
    t = t_(d)
    return sweep_filter(noise(d), f0, f1, .9) * np.sin(np.pi * t / d) ** 2


def rustle(d=7.0):
    t = t_(d)
    grains = np.zeros(len(t))
    for _ in range(int(d * 26)):
        i = R.integers(0, len(t) - 2400)
        g = hp(noise(.05), 2200) * np.hanning(int(.05 * SR)) * R.uniform(.2, 1)
        grains[i:i + len(g)] += g
    return grains


def click():
    t = t_(.06)
    return hp(noise(.06), 1800) * np.exp(-t * 200) + np.sin(2 * np.pi * 1900 * t) * np.exp(-t * 240) * .6


def tick():
    t = t_(.03)
    return hp(noise(.03), 3200) * np.exp(-t * 420)


def pluck(f=880.0, d=.16):
    t = t_(d)
    return (np.sin(2 * np.pi * f * t) + .4 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 34)


def ting(f=4186.0, d=1.0):
    t = t_(d)
    return sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * k) for r, a, k in ((1, 1, 6), (1.506, .5, 9), (2.42, .3, 14)))


def confirm():
    return np.r_[pluck(660, .12), pluck(990, .24)]


KIT = {"hit": hit, "hit_long": lambda: hit(5.0), "metal1": metal_hit, "metal2": lambda: metal_hit(1.6, 118), "metal3": lambda: metal_hit(2.4, 96), "braam": braam,
       "riser": riser, "rev_cym": reverse_cymbal, "rev_bass": reverse_bass, "whoosh": whoosh, "whoosh_short": lambda: whoosh(.42, 700, 4200),
       "whoosh_long": lambda: whoosh(1.6, 180, 1800), "rustle": rustle, "ui_click": click, "ui_tick": tick, "ui_pluck1": pluck, "ui_pluck2": lambda: pluck(1320, .14),
       "ting": ting, "ui_confirm": confirm, "ui_drop": lambda: pluck(440, .2)}


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in KIT.items():
        y = fn().astype(np.float32)
        y = y / (np.abs(y).max() + 1e-9) * .89
        pan = R.uniform(.92, 1.0)
        sf.write(out / f"{name}.wav", np.stack([y, y * pan], axis=1), SR, subtype="FLOAT")
    print(len(KIT), "sounds in", out, ":", ", ".join(KIT))


if __name__ == "__main__":
    main()
