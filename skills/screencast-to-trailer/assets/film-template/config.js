/* Everything specific to one film. Times are film seconds and should come from the music map: every entrance sits on a
   bar line of the edited score. Page coordinates are pixels in the cropped footage (footage.w x footage.h).
   This example is a worked 1:53 layout with a made-up product; replace all of it. */
const BAR = 2.4;                                   // seconds per bar of your edit (60 / bpm * beats per bar)
const DROP = 27.0;                                 // where the score lands after the break
const b = (k) => DROP + BAR * k;                   // k-th bar after the drop. If your edit has splices, list real times instead.

window.FILM = {
  duration: 113.1,
  brand: {
    name: "Acme", url: "acme.example", tagline: "The one line from their own homepage.", cta: "Start for free", note: "From their own pricing page.",
    color: "#ff5a29", ink: "#1f1d1a", night: "#070706",
    // the logo as stroked paths lets the film draw it line by line; take them from the site's SVG
    logoView: [0, 0, 24, 24], logoStroke: 2.6,
    logoPaths: ["M12 3 L21 20", "M21 20 L3 20", "M3 20 L12 3"],
  },
  credit: "Music: “Track” by Composer, CC BY 4.0, edited for length. Sound effects CC0.",

  coldOpen: {
    quiet: [{ text: "Somewhere out there", t: 2.42 }, { text: "is the one thing", t: 4.82 }, { text: "your customer actually needs.", t: 7.22 }],
    quietEnd: 9.5,
    slams: [ // one line per bar, hard cuts
      { text: "But first you have to get through this.", t: 9.62, until: 12.02 },
      { text: "Pain one.", t: 12.02, until: 14.42 },
      { text: "Pain two.", t: 14.42, until: 16.82 },
      { text: "Pain three.", t: 16.82, until: 19.22 },
      { text: "Pain four.", t: 19.22, until: 21.62 },
      { text: "The problem in five words.", t: 21.62, until: 24.02 },
    ],
    payoff: [{ html: "The turn.", t: 24.35, until: 25.65 }, { html: "Your <i>answer.</i>", t: 25.75, until: 27.0 }],
    drop: DROP,
    floodFrom: [960, 400],                         // the white world opens from here on the drop
  },
  concept: { tones: ["212,172,88", "158,122,58", "243,214,140"], glow: "96,62,16" },   // used by the default concept.js

  lockup: { until: b(2), tagAt: b(1), to: [86, 59, 0.241] },   // to: where the logo lands on the app's own header, and its scale

  footage: {
    src: "assets/master.mp4", start: 31.8, duration: 31.3, w: 2416, h: 1314,   // literal numbers: setup_film.py --sync copies them into index.html
    knots: [[31.8, 9.2], [63.1, 79.2]],            // copy the same knots you gave retime.py, the clock reads them
    // t, scale, page x, page y, where that point sits in the frame (0-1). Hold by repeating a value.
    cam: [[31.8, 1.06, 1209, 480, 0.698, 0.505], [38.1, 1.06, 1209, 480, 0.698, 0.505], [38.95, 0.7036, 1208, 657, 0.5, 0.5], [63.1, 0.7036, 1208, 657, 0.5, 0.5]],
    // t, left, top, width, height, corner radius, shadow 0-1. Full bleed first, then the floating window.
    frame: [[31.8, 0, 0, 1920, 1080, 0, 0], [38.1, 0, 0, 1920, 1080, 0, 0], [38.95, 110, 160, 1700, 980, 24, 1], [63.1, 110, 160, 1700, 980, 24, 1]],
  },
  typing: { text: "acme.example", t: 33.0, until: 34.2, rect: [862, 313, 340, 38], size: 20.6, pad: 11 },   // optional, typed over a held frame
  click: { t: 37.8, at: [1208, 838] },             // optional ripple on the moment of the click
  clock: { from: 37.8, until: 63.0, startS: 12.44, seconds: 66.3, doneAt: 62.3 },   // real recording time, leave out unless it is true

  headlines: [ // <i> marks the accent word
    { html: "Start with your<br><i>website.</i>", pos: "left", t: 32.1, until: 38.1 },
    { html: "Step two in <i>five words.</i>", t: 39.02, until: 45.6 },
    { html: "Step three in <i>three.</i>", t: 46.22, until: 51.02 },
    { html: "And the <i>payoff.</i>", t: 51.02, until: 55.82 },
    { html: "Then it does the <i>hard part.</i>", t: 55.82, until: 63.02 },
  ],
  rings: [{ rect: [1532, 224, 316, 744], t: 51.75, until: 55.8, dim: true }],   // on the page; dim fades everything else back
  footnotes: [{ text: "Names and companies changed for privacy.", t: 48.1, until: 55.8 }],

  stillScenes: [ // white scenes built from stills
    {
      t: 63.02, until: 70.22, headline: "You keep the <i>last word.</i>",
      cards: [{ src: "assets/stills/st_a.png", box: [152, 300, 742, 480], focus: [589, 675], scale: 1.6, push: 0.06, in: 63.27, rings: [{ rect: [521, 642, 162, 38], t: 64.8 }] },
              { src: "assets/stills/st_b.png", box: [964, 440, 806, 212], focus: [2135, 805], scale: 1.58, in: 65.42, marks: [{ rect: [2027, 781, 258, 30], t: 66.62, dur: 0.7 }] }],
    },
    {
      t: 70.22, until: 77.42, pos: "left", headline: "Run it from<br>your <i>agent.</i>", sub: "One supporting sentence, quoted from their site.",
      cards: [{ src: "assets/stills/st_c.png", box: [820, 210, 1040, 660], focus: [1208, 368], scale: 1.16, push: 0.04, in: 70.42,
                rings: [{ rect: [801, 274, 191, 102], t: 72.62 }] }],
    },
  ],
  statements: [{ text: "One input.", t: 77.42, until: 79.82 }, { text: "One finished result.", t: 79.82, until: 82.23 }],

  climax: {
    t: 82.23,
    big: { html: "66 <i>seconds.</i>", sub: "What was measured, and where.", until: 84.63 },
    slides: [ // one per bar, card comes in from the right
      { say: "The first claim.", t: 84.63, until: 87.03, src: "assets/stills/st_a.png", box: [960, 96, 880, 888], focus: [1400, 590], scale: 0.99 },
      { say: "The second.", t: 87.03, until: 89.43, src: "assets/stills/st_b.png", box: [960, 280, 860, 520], focus: [589, 675], scale: 1.9 },
    ],
    rapid: { t: 96.63, step: 0.3, srcs: ["assets/stills/st_a.png", "assets/stills/st_b.png", "assets/stills/st_c.png"] },
    footnote: "Names and companies changed for privacy.", footnoteFrom: 84.63, footnoteUntil: 89.43,
  },

  end: { t: 99.03, hit: 102.0, tagAt: 103.95, ctaAt: 105.4, shineAt: 107.3, creditAt: 108.6 },
};
