/* The cold open's picture. Replace this for every film: the strongest trailers take their image from the product's
   name or from the problem it removes. This default draws a field of thin strokes that fills the frame as the score
   builds, then falls away and leaves one lit stroke, the shape of "too much noise, then the one thing that matters".

   Keep it a pure function of t: no Math.random, no state between frames. Use the seeded generator below. */
(function () {
  const { P, E, lerp, clamp } = window.FILM_EASE || {};
  function rng(a) {
    return () => {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const N = 12000, R = rng(20261031);
  const hx = new Float32Array(N), hy = new Float32Array(N), hz = new Float32Array(N), ang = new Float32Array(N),
    len = new Float32Array(N), cur = new Float32Array(N), ton = new Uint8Array(N), del = new Float32Array(N), spin = new Float32Array(N);
  for (let i = 0; i < N; i++) {
    hx[i] = (R() * 2 - 1) * 1.15; hy[i] = (R() * 2 - 1) * 1.15; hz[i] = R();
    ang[i] = -0.5 + (R() - 0.5) * 2.5 + (R() < 0.3 ? 1.5 : 0);
    len[i] = 26 + R() * 64; cur[i] = (R() - 0.5) * 0.5; ton[i] = Math.floor(R() * 3); del[i] = R() * 0.62; spin[i] = (R() - 0.5) * 7;
  }
  const LV = [{ lw: 0.9, a: 0.26 }, { lw: 1.3, a: 0.42 }, { lw: 1.8, a: 0.6 }, { lw: 2.6, a: 0.74 }, { lw: 3.8, a: 0.62 }];

  window.FILM_CONCEPT = function (ctx, t, C) {
    const { P, E, lerp } = window.FILM_EASE;
    const CC = C.coldOpen, impact = CC.slams[0].t, stop = CC.slams[CC.slams.length - 1].until, TONE = C.concept.tones;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = C.brand.night; ctx.fillRect(0, 0, 1920, 1080);
    const warm = t >= impact ? P(t, impact, stop - 2.4) * (1 - P(t, stop + 0.3, stop + 1.6)) : 0.25 * P(t, 2, impact);
    if (warm > 0) {
      const g0 = ctx.createRadialGradient(960, 560, 80, 960, 560, 1000);
      g0.addColorStop(0, `rgba(${C.concept.glow},${(0.5 * warm).toFixed(3)})`); g0.addColorStop(1, "rgba(7,7,6,0)");
      ctx.fillStyle = g0; ctx.fillRect(0, 0, 1920, 1080);
    }
    let Z = t < impact ? 0.012 * t : 0.012 * impact + 0.13 * (Math.min(t, stop) - impact);
    for (const s of CC.slams) Z += 0.2 * P(t, s.t, s.t + 0.75, E.outE);
    if (t > stop) Z += (0.13 * (1 - Math.exp(-(t - stop) * 1.3))) / 1.3;
    const count = t < impact ? Math.floor(lerp(70, 1700, Math.pow(Math.min(t / (impact - 0.4), 1), 2))) : Math.floor(lerp(4200, N, P(t, impact, stop, E.ioS)));
    const implode = t < impact ? 1 - 0.55 * P(t, impact - 0.7, impact, E.inC) : 1;
    const burst = t >= impact ? 0.04 + 0.96 * P(t, impact, impact + 0.6, E.outE) : 1;
    const paths = []; for (let i = 0; i < 15; i++) paths.push(new Path2D());
    for (let i = 0; i < count; i++) {
      let z = hz[i] - Z; z -= Math.floor(z);
      const p = 0.82 / (z + 0.24);
      const x = 960 + hx[i] * 1050 * p * burst * implode; let y = 540 + hy[i] * 640 * p * burst * implode;
      let a0 = ang[i] + 0.12 * Math.sin(t * 0.5 + i), fade = 1;
      const L = len[i] * p;
      if (t > stop + 0.08) {
        const d = t - stop - 0.08 - del[i];
        if (d > 0) { y += 1250 * d * d; a0 += spin[i] * d; fade = 1 - Math.min(d / 1.25, 1); if (fade <= 0) continue; }
      }
      if (x < -260 || x > 2180 || y < -260 || y > 1340) continue;
      const lv = z > 0.72 ? 0 : z > 0.45 ? 1 : z > 0.24 ? 2 : z > 0.09 ? 3 : 4;
      if (fade < 0.45 && lv > 2) continue;
      const c = Math.cos(a0), s = Math.sin(a0), Q = paths[lv * 3 + ton[i]];
      Q.moveTo(x - c * L, y - s * L);
      Q.quadraticCurveTo(x - s * L * cur[i], y + c * L * cur[i], x + c * L, y + s * L);
    }
    ctx.lineCap = "round";
    const dim = t < impact ? 0.78 * P(t, 0.4, 2.4) : 1, gone = t > stop ? 1 - P(t, stop + 0.9, stop + 2.1) : 1;
    for (let lv = 0; lv < 5; lv++) for (let k = 0; k < 3; k++) {
      ctx.lineWidth = LV[lv].lw; ctx.strokeStyle = `rgba(${TONE[k]},${(LV[lv].a * dim * gone).toFixed(3)})`; ctx.stroke(paths[lv * 3 + k]);
    }
    const g = ctx.createRadialGradient(960, 520, 200, 960, 540, 1120);
    g.addColorStop(0, "rgba(7,7,6,0)"); g.addColorStop(1, "rgba(7,7,6,.72)");
    ctx.fillStyle = g; ctx.fillRect(0, 0, 1920, 1080);
    if (t >= impact && t < stop + 1.9) {   // keep the words readable over the field
      const k = 1 - P(t, stop + 1, stop + 1.9);
      const g2 = ctx.createRadialGradient(960, 540, 60, 960, 540, 820);
      g2.addColorStop(0, `rgba(7,7,6,${(0.84 * k).toFixed(3)})`); g2.addColorStop(0.62, `rgba(7,7,6,${(0.36 * k).toFixed(3)})`); g2.addColorStop(1, "rgba(7,7,6,0)");
      ctx.fillStyle = g2; ctx.fillRect(0, 0, 1920, 1080);
    }
    // the one lit stroke that survives, sitting where the white flood will open
    const [hxp, hyp] = CC.floodFrom, a = P(t, stop - 2.3, stop - 1.6, E.outC);
    if (a > 0) {
      ctx.save(); ctx.translate(hxp, hyp); ctx.rotate(-0.42); ctx.globalAlpha = a;
      ctx.shadowColor = C.brand.color; ctx.shadowBlur = 26; ctx.fillStyle = C.brand.color;
      ctx.beginPath(); ctx.moveTo(120, 0); ctx.lineTo(-90, -3.6); ctx.quadraticCurveTo(-125, -4.6, -130, 0); ctx.quadraticCurveTo(-125, 4.6, -90, 3.6); ctx.closePath(); ctx.fill();
      ctx.restore();
    }
  };
})();
