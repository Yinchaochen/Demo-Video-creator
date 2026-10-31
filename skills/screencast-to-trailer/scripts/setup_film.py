#!/usr/bin/env python3
"""Create a film project from the template, install what it needs, and check the machine.

    python setup_film.py my-film

Makes my-film/ with the composition in my-film/film/ (index.html, film.js, config.js, concept.js), a local HyperFrames
install, GSAP, and two open-licence fonts (Lora for headlines, Instrument Sans for body) as defaults. Swap the fonts
for the brand's own when their licence allows it.

    python setup_film.py --sync my-film      keeps data-duration in index.html equal to duration in config.js
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "film-template"
FONTS = {"head-500.woff2": "@fontsource/lora/files/lora-latin-500-normal.woff2",
         "head-500-italic.woff2": "@fontsource/lora/files/lora-latin-500-italic.woff2",
         "body-400.woff2": "@fontsource/instrument-sans/files/instrument-sans-latin-400-normal.woff2",
         "body-500.woff2": "@fontsource/instrument-sans/files/instrument-sans-latin-500-normal.woff2",
         "body-600.woff2": "@fontsource/instrument-sans/files/instrument-sans-latin-600-normal.woff2"}


def sync(root):
    cfg = (root / "film/config.js").read_text(encoding="utf-8")
    dur = re.search(r"duration:\s*([\d.]+)", cfg).group(1)
    idx = root / "film/index.html"
    s = idx.read_text(encoding="utf-8")
    s = re.sub(r'(id="root"[^>]*data-duration=")[\d.]+', r"\g<1>" + dur, s)
    # HyperFrames plans video extraction from the static HTML, so these cannot be set at runtime
    m = re.search(r'footage:\s*\{[^}]*?src:\s*"([^"]+)"[^}]*?start:\s*([\d.]+)[^}]*?duration:\s*([\d.]+)', cfg)
    if not m:
        raise SystemExit('config.js footage needs literal numbers: src: "...", start: 31.8, duration: 31.3')
    s = re.sub(r'(<video id="master"[^>]*?src=")[^"]*', r"\g<1>" + m.group(1), s)
    s = re.sub(r'(<video id="master"[^>]*?data-start=")[\d.]+', r"\g<1>" + m.group(2), s)
    s = re.sub(r'(<video id="master"[^>]*?data-duration=")[\d.]+', r"\g<1>" + m.group(3), s)
    idx.write_text(s, encoding="utf-8")
    print(f"index.html: film {dur} s, footage {m.group(1)} from {m.group(2)} for {m.group(3)} s")


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--sync":
        sync(Path(sys.argv[2]))
        return
    root = Path(sys.argv[1])
    missing = [t for t in ("node", "npm", "ffmpeg", "ffprobe") if shutil.which(t) is None]
    if missing:
        raise SystemExit("missing on this machine: " + ", ".join(missing))
    (root / "film").parent.mkdir(parents=True, exist_ok=True)
    if (root / "film").exists():
        raise SystemExit(f"{root / 'film'} already exists, not overwriting it")
    shutil.copytree(TEMPLATE, root / "film")
    for d in ("audio/sfx", "assets/music", "work", "deliver", "renders"):
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / "film/assets/fonts").mkdir(parents=True, exist_ok=True)
    (root / "film/vendor").mkdir(exist_ok=True)
    (root / "package.json").write_text(json.dumps({"name": "trailer", "private": True}), encoding="utf-8")
    npm = shutil.which("npm")
    subprocess.run([npm, "install", "--no-audit", "--no-fund", "hyperframes", "gsap", "@fontsource/lora", "@fontsource/instrument-sans"], cwd=root, check=True)
    nm = root / "node_modules"
    shutil.copy(nm / "gsap/dist/gsap.min.js", root / "film/vendor/gsap.min.js")
    for dst, src in FONTS.items():
        shutil.copy(nm / src, root / "film/assets/fonts" / dst)
    (root / "film/hyperframes.json").write_text(json.dumps({"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
                                                            "media": {"autoProxy": False}}, indent=1), encoding="utf-8")
    print(f"Ready. Edit {root}/film/config.js and concept.js, then from {root}/film run:\n"
          "  npx hyperframes lint .\n  npx hyperframes snapshot . --no-end -o ../work/snaps --at 5,20,30,40\n"
          "  npx hyperframes render . -o ../renders/silent.mp4 -f 60 --video-frame-format png")


if __name__ == "__main__":
    main()
