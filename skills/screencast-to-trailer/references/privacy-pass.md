# The privacy pass

A screen recording shows far more than the feature it was made for. Once a film is public it cannot be taken back, so go through the footage
for this before any creative work.

## What to look for

- Browser chrome: tabs reveal what else the person is working on, and the address bar can carry tokens or internal hostnames.
- Sign-in screens: emails and account pickers, usually in the first seconds.
- The user's name, avatar and workspace: greetings like "Good afternoon, ...", sidebar footers, account menus.
- Other people: leads, customers, teammates, contacts, comments. Their names, photos, emails, companies.
- Secrets: API keys, tokens, invite links, anything in a settings page.
- Other apps passing through: notification toasts, a second product's dashboard opened during setup.
- Third-party brands used as sample input. These are public but may imply a relationship, so tell the user rather than deciding alone.

Check the moments you plan to skip too. Rapid montages and stills reuse frames from anywhere.

## How to deal with it, best first

1. **Crop.** Removing the browser chrome from the footage at the start means it can never appear. Do this for every film.
2. **Skip.** Most sensitive screens are not needed. Start after the sign-in, leave out the dashboard if it adds nothing.
3. **Replace.** When the real data is the point of the scene, for example a list of results, overwrite it with invented data.
4. **Blur** only as a last resort. It reads as an error in a film and can leak at some zoom levels.

## Replacing data so it looks native

Sample rows look right when the metrics match, so measure instead of guessing:

1. Find the row rectangles from a reference frame: separators, column positions, background colour.
2. Fetch the app's font from its own stylesheet.
3. Build the replacement as HTML with a transparent background at the recording's size, and screenshot it with headless Chrome, which gives
   the same text rendering as the recording.
4. Put two real rows in first and compare them side by side with the recording. Adjust sizes until widths match to a pixel or two.
   Then switch to the sample rows. Do not keep the calibration file.
5. Pass the tile to `retime.py` as a redaction. The whole rectangle is overwritten in every frame, so no original pixel survives.
   Give it a `fade_ref` frame if the rows fade in, so the replacement fades with the same timing.

Invented data should be obviously invented on inspection and hard to confuse with a real entity. Use the reserved `.example` domain, invented
company names and simple drawn marks instead of logos. Say so on screen wherever it appears, in plain words such as "Names and companies changed for
privacy." Do not keep real people's names in project files you plan to share.

Check the result at full size in the moments of change: rows fading in, the first frame of a scene, every still.

## Bounds on the range

Give each redaction a recording-time range that ends when its page does. A redaction with no end will paint over the next screen. This happened on a real
film: the list appeared on top of the following page in a still, and only the contact sheet caught it.
