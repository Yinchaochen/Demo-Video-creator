# Finding a score you are allowed to use

## Licence rules

Editing a track to length is a derivative work, and the film is usually commercial, so:

| Licence | Use it? | Why |
| --- | --- | --- |
| CC0, public domain | Yes | No conditions |
| CC BY | Yes | Credit the author and say it was edited |
| Any NC | No | Forbids commercial use, and a product film is commercial |
| Any ND | No | Forbids the edit |
| SA, GPL | No | Copyleft can reach the whole film |
| "Royalty free" with no licence text | No | Means nothing until you read the terms |

Trust a licence when the author set it for their own work on a page you can cite. Be wary of re-upload accounts and sites where
anyone can type any licence on anyone's music. Save the URL, the licence line and the attribution text at the moment you download, in
`deliver/CREDITS.md`.

## Where to look

| Source | Licence | Notes |
| --- | --- | --- |
| [Scott Buckley](https://www.scottbuckley.com.au/library/) | CC BY 4.0 | Professional cinematic and hybrid scores, the best first stop for trailers. Each track page gives the direct MP3 link and exact attribution text. The server rejects non-browser clients, so send a browser `User-Agent` and a `Referer` of the library page. |
| [OpenGameArt](https://opengameart.org/art-search-advanced?field_art_type_tid%5B%5D=12) | Per item | Filter by licence. Good for electronic and action cues. |
| [Openverse](https://api.openverse.org/v1/audio/?q=cinematic&license_type=commercial,modification&category=music&page_size=20) | Per item | Search across open sources through an API. Anonymous requests are limited to 20 results per page and rate limited, so go slowly. Check the licence on the landing page. |
| [Free Music Archive](https://freemusicarchive.org/) | Per track | Check each track, many are NC or ND. |
| [Incompetech](https://incompetech.com/) | Check its current terms | Large catalogue by Kevin MacLeod, widely heard, so it can sound familiar. |

FreePD closed, so old links to it are dead.

## What makes a track work for a trailer

You are looking for structure more than a mood. Search terms that find it: trailer, hybrid, epic, driving, build, cinematic. A composer
describing a track as "slowly builds to a break, then a thematic ending" is telling you the structure outright.

On the chart from `music_map.py map`, look for:

- A quiet opening of at least 8 seconds for the cold open.
- A long climb, because it can be shortened.
- A break where the level falls 10 dB or more. This is your flip into the product.
- A steady body with a dip in the middle. The dip is where to put the calm, trust-building scene.
- A last section louder than the body, and a real ending with a final hit and a ring-out, since a track that fades out gives you no end card.

Length matters less than these: a 4 minute track with the right structure cuts down to 1:50 cleanly.

## Cutting it down

Repeating chord cycles are what make this possible. In the bar table, find two bars with the same chord position in the cycle, and jump between
them. Moving from one section of a cycle to the same place in a louder section sounds like a deliberate lift. Good joins measured:

| Join | Spectral | Chroma | Level |
| --- | --- | --- | --- |
| Quiet intro into high-intensity build | 0.79 | 0.91 | -21.5 to -21.5 dB |
| Same chord position, next cycle | 0.45 | 0.95 | -19.5 to -17.5 dB |
| End of the body into the final section | 0.26 | 0.91 | -14.7 to -14.9 dB |

Keep the track's own break, last hit and ring-out. Those moments are the reason you picked it, and synthetic replacements never match.
