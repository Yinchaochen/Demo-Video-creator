# screencast-to-trailer

An agent skill that turns a raw screen recording of your software and one sentence about it into a finished product trailer. You get a 1 to 2 minute 1080p film with an openly licensed score, sound design, on-screen copy and every cut on the beat.

You record your app the way you normally would. Your coding agent does the rest:

```text
> Here's a recording of my app, recording.mp4. The site is acme.com.
  Make a 90 second launch trailer.
```

## What it does

The film is built around one rule: pick the music first, read its bars, and cut everything to them. That single constraint is most of the difference between a walkthrough and a trailer.

From there the agent works through these steps:

1. Reads your site and docs, so every claim in the film traces to something you actually say.
2. Maps the recording frame by frame and finds the real state changes, the dead air and any time worth measuring.
3. Runs a privacy pass. It crops browser chrome and skips sign-in screens, and it can replace real customer rows with sample data in your app's own font, burned into every frame.
4. Finds a CC0 or CC BY score, charts its structure and cuts it to length on matching chord positions.
5. Retimes the footage onto the music, with waiting sped up and clicks landing on beats.
6. Builds the film in code with [HyperFrames](https://github.com/heygen-com/hyperframes), including a cold open drawn from your product's name or problem.
7. Places a cue for every visible event, mixes to -14 LUFS and -1 dBTP, and flags sounds that would get lost under the score.
8. Reviews the result frame sheet by frame sheet and writes a credits file with the attribution your licences require.

## Install

With the [skills CLI](https://github.com/vercel-labs/skills), which works across Claude Code, Codex, Cursor and other agents:

```bash
npx skills add Yinchaochen/Demo-Video-creator
```

In Claude Code you can also add it as a plugin:

```text
/plugin marketplace add Yinchaochen/Demo-Video-creator
/plugin install screencast-to-trailer@screencast-to-trailer
```

Or copy `skills/screencast-to-trailer/` into your agent's skills folder, for example `~/.claude/skills/`.

## Requirements

- Node 22 or newer, `ffmpeg` and `ffprobe`
- Python 3.10 or newer, then `pip install -r skills/screencast-to-trailer/requirements.txt`
- About 10 GB of free disk space during a render. Two minutes of 1080p at 60 fps took 11 minutes on a laptop.

No API keys are needed. Everything runs on your machine, and the skill ships a small synthesized sound kit, so a film works with no sound downloads at all.

## What's inside

```text
skills/screencast-to-trailer/
├── SKILL.md            the workflow
├── scripts/            footage map, music analysis and edit, retime and redaction, mix, finish
├── assets/film-template/  the composition: engine, config and cold-open concept
└── references/         music sources, privacy pass, storyboard, sound design, HyperFrames notes
```

## Things to know

The film needs an openly licensed score, so the agent downloads one from sources such as Scott Buckley's CC BY library or OpenGameArt. Check the licence of anything you add by hand: NC and ND tracks are not safe for a product film, since the film is commercial and the track gets edited.

An agent cannot hear. It sets levels by measurement and tells you so, which means you should listen once on headphones before you publish.

If you make a film about someone else's product, you need their permission to publish it.

## Licence

MIT, see [LICENSE](LICENSE). The skill installs HyperFrames (Apache-2.0), GSAP (GSAP Standard License) and open fonts at setup time. It bundles none of them, and it bundles no music or recorded sound.
