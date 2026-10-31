# HyperFrames notes

Things that have already gone wrong, so you can skip them. HyperFrames (Apache-2.0) renders an HTML page frame by frame in headless Chrome.

## Composition

- The film template keeps every frame a function of `t`. Keep it that way: no `Math.random`, no `Date`, no state carried between frames. A seek must give the same picture as playing up to that point.
- Drive canvas drawing from a setter on the object GSAP tweens. `onUpdate` does not fire on seeks.
- `lint` looks for `window.__timelines` in inline script, so the small inline block at the bottom of `index.html` needs to stay there.
- Hide layers with `display: none`. If you hide a parent with `visibility: hidden`, any child that has its own `visibility` set stays visible. This produced a stray logo over a whole film.
- A `<video>` nested in a transformed container follows the transform, so camera moves can be plain CSS on the parent.
- Overlays placed inside the same transformed parent, such as rings and typed text, stay locked to the page.
- Two elements using the same image give a `duplicate_media_discovery_risk` warning. It is harmless for stills.

## Rendering

- `--video-frame-format png` keeps interface text clean. It writes large temporary files, so make sure the temp folder has room (several GB for a 30 second clip at 2416 px wide). If the system drive is small, point `TEMP` and `TMP` at another drive.
- Rendering captures about 12 frames per second at 1080p with CSS transforms and canvas, then encodes in a couple of minutes. Two minutes of 60 fps took 11 minutes in total on a laptop.
- Set `HYPERFRAMES_NO_TELEMETRY=1`, `DO_NOT_TRACK=1` and `HYPERFRAMES_SKIP_SKILLS=1` if you do not want the CLI reporting or adding files to global folders.
- The compile step fetches some Google Fonts, so the first render needs a network connection.

## Footage

- Screen recordings are variable frame rate. Read real timestamps, never assume a fixed rate. `retime.py` resamples to a constant rate for you.
- Writing frames out with ffmpeg's image2 muxer and passthrough timing can stop early on duplicate timestamps. Pipe raw frames into Python instead, as the scripts do.
- ffmpeg's `drawtext` needs fontconfig and crashes or errors on many Windows builds. Draw labels with Pillow.
- Render a few snapshots at the moments of change, not at the middle of scenes. The errors are almost always at transitions.
