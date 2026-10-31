# Sound design

## Sources

`scripts/make_sfx.py` writes a synthetic starter kit with no licence conditions. It is enough for a first cut. For a final mix, recorded sounds are
richer, so use them when you can:

| Source | Licence | Good for |
| --- | --- | --- |
| [Kenney Interface Sounds](https://kenney.nl/assets/interface-sounds) | CC0 | Clicks, ticks, plucks, confirmations |
| [Freesound](https://freesound.org/search/?f=license:%22Creative+Commons+0%22) (CC0 filter) | Per sound, needs an account to download | Trailer hits, braams, risers, whooshes |
| [OpenGameArt](https://opengameart.org/art-search-advanced?field_art_type_tid%5B%5D=13) | Per item | Whooshes, impacts, UI packs |

Search Freesound for: trailer hit, braam, cinematic boom, riser, white noise build, reverse cymbal, whoosh. Copy what you use into `audio/sfx/` with short names and log the
author, licence and URL. The same licence table as for music applies.

## The cue sheet

`mix.py` reads a list of cues. Each sound is normalised first, so a gain reads as level against full scale. These starting levels worked with the score at -16.5 LUFS:

| Event | Sound | Gain dB | Notes |
| --- | --- | --- | --- |
| Quiet text lines | Soft kick | -14 | Barely felt |
| Build impact | Long hit + braam + whoosh | -8, -11, -13 | Hit is the sound's peak |
| Text slams | Metal hits | -8 | Cut tails to 2 s |
| Before any impact | Reverse cymbal + reverse bass | -13 | `at: peak`, ending on the impact |
| Big transition | Whoosh | -14 | Peak on the middle of the move |
| Keystrokes | Tick | -13 to -15 | Vary level and spacing |
| Clicks | Click | -9 | |
| Items appearing | Pluck, a few ms apart | -12 | Reads as a cascade |
| Task finished | Confirm + low bong | -10, -15 | |
| Final hit | Long hit | -7 | Cut at 4 to 5 s |

Under the demo, pull the score down 3 to 4 dB so interface sounds read, and ramp it back up over a second before the climax.

## Mixing without ears

An agent cannot hear the mix, and these checks stand in for that as far as they can:

- `mix.py` flags cues whose peak sits less than 4 dB over the score around them. Those are lost. Short clicks need more than you expect.
- It lists seconds that overshoot. Take hits down there before relying on the limiter. Stacked hits on one beat are the usual cause.
- `finish.py` measures the encoded file, since AAC adds peaks that the limiter did not see.

Tell the user the levels were measured, not auditioned. Recommend they listen once on headphones and name anything that sticks out.

## Targets

-14 LUFS integrated and -1 dBTP true peak suit YouTube, LinkedIn and most web players. A loudness range of 8 to 10 LU keeps the film dynamic, and
the quiet cold open will pull the average down, so the rest may sit a little hotter than you expect.
