#!/usr/bin/env python3
"""Read a music track's structure so the film can be cut to it.

    python music_map.py map track1.mp3 [track2.mp3 ...] -o work/music
        energy chart (PNG) + one line per track: length, tempo, and the big events (entries, breaks, final hits)

    python music_map.py bars track.mp3 --anchor 71.7 --bpm 100 --from 71.7 --to 218
        per-bar table on a grid anchored at a known attack: level, low/high energy, strongest notes.
        Chord changes show you where a bar can be removed without the harmony noticing.

    python music_map.py splice track.mp3 23.1:54.3 83.7:93.3
        compares what follows each out point with what would be spliced in. Spectral distance under 1.0 and
        chroma similarity over 0.85 with the levels within 3 dB has been inaudible in practice under a 40 ms crossfade.
"""
import argparse
import json
from pathlib import Path

import librosa
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SR, HOP = 22050, 512
NOTES = "C C# D D# E F F# G G# A A# B".split()


def tempo_of(onset):
    """Comb search on the onset envelope. Returns the best tempos, strongest first.

    A single answer from a beat tracker is often a related tempo (x2, x0.5, x4/3 on dotted patterns), so list
    the candidates and confirm the grid against attacks you can measure, such as the track's big entries.
    """
    fps = SR / HOP
    scores = []
    for bpm in np.arange(60, 200, 0.25):
        per = 60 / bpm * fps
        idx = np.arange(0, len(onset) - 1, per)
        best = max(onset[np.minimum((idx + ph).astype(int), len(onset) - 1)].mean() for ph in np.arange(0, per, per / 16))
        scores.append((float(best), float(bpm)))
    top = []
    for sc, bpm in sorted(scores, reverse=True):
        if all(abs(bpm - b) > 3 for _, b in top):
            top.append((sc, bpm))
        if len(top) == 4:
            break
    return [b for _, b in top]


def events(t, db):
    """Jumps of 5 dB or more in the 1 s loudness curve: the entries, breaks and hits an edit hangs on."""
    out, last = [], -9
    step = int(1.0 * SR / HOP)
    for i in range(step, len(db) - step):
        d = db[i + step // 2] - db[i - step // 2]
        if abs(d) >= 5 and t[i] - last > 2.5:
            out.append((round(float(t[i]), 1), round(float(d), 1)))
            last = t[i]
    return out


def cmd_map(a):
    out = Path(a.o)
    out.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(len(a.tracks), 1, figsize=(18, 4 * len(a.tracks)))
    axes = np.atleast_1d(axes)
    report = {}
    for ax, f in zip(axes, a.tracks):
        y, _ = librosa.load(f, sr=SR, mono=True)
        S = np.abs(librosa.stft(y, n_fft=2048, hop_length=HOP))
        fr = librosa.fft_frequencies(sr=SR, n_fft=2048)
        t = librosa.frames_to_time(np.arange(S.shape[1]), sr=SR, hop_length=HOP)
        rms = librosa.feature.rms(S=S, frame_length=2048)[0]
        onset = librosa.onset.onset_strength(S=librosa.amplitude_to_db(S, ref=np.max), sr=SR, hop_length=HOP)
        k = int(SR / HOP) | 1
        sm = lambda v: np.convolve(v, np.ones(k) / k, "same")
        db = 20 * np.log10(sm(rms) + 1e-6)
        low, high = sm(S[fr < 150].sum(0)), sm(S[fr > 3000].sum(0))
        tempos = tempo_of(onset)
        ev = events(t, db)
        ax.plot(t, db, color="#222", lw=1.2)
        ax2 = ax.twinx()
        ax2.plot(t, low / low.max(), color="#c33", lw=.8, label="low < 150 Hz")
        ax2.plot(t, high / high.max(), color="#39c", lw=.8, label="high > 3 kHz")
        ax2.legend(loc="upper left", fontsize=8)
        for e, _d in ev:
            ax.axvline(e, color="#999", ls="--", lw=.6)
        ax.set_xlim(0, t[-1])
        ax.set_xticks(np.arange(0, t[-1], 10))
        ax.grid(axis="x", alpha=.2)
        ax.set_title(f"{Path(f).name}  {t[-1]:.1f} s  tempo candidates {tempos}  events {ev}")
        report[f] = {"seconds": float(t[-1]), "tempo_candidates": tempos, "events": ev}
        print(f"{Path(f).name}: {t[-1]:.1f} s, tempo candidates {tempos} BPM (confirm against event spacing), events {ev}")
    fig.tight_layout()
    fig.savefig(out / "music_map.png", dpi=75)
    json.dump(report, open(out / "music_map.json", "w"), indent=1)
    print("chart:", out / "music_map.png")


def cmd_bars(a):
    y, _ = librosa.load(a.track, sr=SR, mono=True)
    ch = librosa.feature.chroma_cqt(y=y, sr=SR, hop_length=HOP, bins_per_octave=36)
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=HOP))
    fr = librosa.fft_frequencies(sr=SR, n_fft=2048)
    fps = SR / HOP
    bar = 60 / a.bpm * a.beats
    k0 = int(np.ceil((getattr(a, "from") - a.anchor) / bar))
    k1 = int(np.floor((a.to - a.anchor) / bar))
    print("bar  time     level    low   high  strongest notes")
    for k in range(k0, k1):
        t = a.anchor + k * bar
        i, j = int(t * fps), int((t + bar) * fps)
        c = ch[:, i:j].mean(1)
        top = " ".join(NOTES[x] for x in np.argsort(c)[::-1][:3])
        r = 20 * np.log10(np.sqrt(np.mean(y[int(t * SR):int((t + bar) * SR)] ** 2)) + 1e-7)
        print(f"{k:3d} {t:7.2f} {r:6.1f} dB {S[fr < 150][:, i:j].sum(0).mean():6.0f} {S[fr > 3000][:, i:j].sum(0).mean():6.0f}  {top}")


def cmd_splice(a):
    y, _ = librosa.load(a.track, sr=48000, mono=True)

    def feat(t, dur=0.6):
        s = y[int(t * 48000):int((t + dur) * 48000)]
        S = np.abs(np.fft.rfft(s * np.hanning(len(s))))
        f = np.fft.rfftfreq(len(s), 1 / 48000)
        edges = np.geomspace(40, 16000, 25)
        band = np.array([S[(f >= edges[i]) & (f < edges[i + 1])].sum() + 1e-6 for i in range(24)])
        c = librosa.feature.chroma_stft(y=s, sr=48000, n_fft=8192, hop_length=4096).mean(1)
        return np.log(band), c / (np.linalg.norm(c) + 1e-9), 20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-7)

    for pair in a.pairs:
        o, i = (float(x) for x in pair.split(":"))
        ba, ca, la = feat(o)
        bb, cb, lb = feat(i)
        print(f"{o:8.2f} -> {i:8.2f}  spectral {np.mean(np.abs(ba - bb)):.2f}  chroma {float(ca @ cb):.3f}  level {la:.1f} -> {lb:.1f} dB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("map")
    m.add_argument("tracks", nargs="+")
    m.add_argument("-o", required=True)
    b = sub.add_parser("bars")
    b.add_argument("track")
    b.add_argument("--anchor", type=float, required=True)
    b.add_argument("--bpm", type=float, required=True)
    b.add_argument("--beats", type=int, default=4)
    b.add_argument("--from", type=float, default=0.0)
    b.add_argument("--to", type=float, required=True)
    s = sub.add_parser("splice")
    s.add_argument("track")
    s.add_argument("pairs", nargs="+")
    args = ap.parse_args()
    {"map": cmd_map, "bars": cmd_bars, "splice": cmd_splice}[args.cmd](args)
