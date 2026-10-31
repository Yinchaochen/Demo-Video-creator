/* Trailer engine. The film is one pure function of time, render(t): every frame is computed from t alone, so seeking
   is exact and re-renders are identical. GSAP only carries t. Everything specific to a film lives in config.js and
   concept.js; change those first and touch this file only for a new kind of scene. */
(function () {
  const C = window.FILM;
  const $ = (id) => document.getElementById(id);
  const clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
  const lerp = (a, b, p) => a + (b - a) * p;
  const E = {
    lin: (x) => x,
    outC: (x) => 1 - Math.pow(1 - x, 3),
    outQ: (x) => 1 - Math.pow(1 - x, 4),
    outE: (x) => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x)),
    inC: (x) => x * x * x,
    ioC: (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
    ioS: (x) => -(Math.cos(Math.PI * x) - 1) / 2,
    outB: (x) => 1 + 2.4 * Math.pow(x - 1, 3) + 1.4 * Math.pow(x - 1, 2),
  };
  const P = (t, a, b, e = E.lin) => e(clamp((t - a) / (b - a)));
  window.FILM_EASE = { P, E, clamp, lerp };

  const el = (tag, parent, cls, html) => { const n = document.createElement(tag); if (cls) n.className = cls; if (html !== undefined) n.innerHTML = html; parent.appendChild(n); return n; };
  const setd = (n, on) => { n.style.display = on ? "block" : "none"; };
  const words = (html) => html.split(/(<br\s*\/?>)/).map((chunk) => (/^<br/.test(chunk) ? chunk : chunk.replace(/(<i[^>]*>.*?<\/i>|[^\s<]+)/g, '<span class="w"><span>$1</span></span>'))).join("");
  const stitched = (html) => html.replace(/<i>([^<]*)<\/i>/g, '<i class="u">$1<b class="st"></b></i>');

  /* ---------- theme ---------- */
  const R = document.documentElement.style;
  R.setProperty("--brand", C.brand.color); R.setProperty("--ink", C.brand.ink); R.setProperty("--night", C.brand.night);

  /* ---------- build the page from config ---------- */
  const a1 = $("a1"), flood = $("flood"), cx = $("cx"), end = $("end");
  const quiet = C.coldOpen.quiet.map((q) => Object.assign(el("div", $("quiet"), "", q.text), { _t: q.t }));
  const slams = C.coldOpen.slams.map((s) => { const n = el("div", a1, "slam" + (s.text.length > 24 ? " long" : ""), s.text); n._s = s; return n; });
  const payoff = C.coldOpen.payoff.map((p) => { const n = el("div", a1, "payoff", p.html); n._s = p; return n; });

  const logoSVG = (id, stroke) => `<svg id="${id}" width="170" height="${Math.round((170 * C.brand.logoView[3]) / C.brand.logoView[2])}" viewBox="${C.brand.logoView.join(" ")}" fill="none">${C.brand.logoPaths.map((d) => `<path d="${d}" stroke="${stroke}" stroke-width="${C.brand.logoStroke}" stroke-linecap="round" stroke-linejoin="round"/>`).join("")}</svg>`;
  $("lock").innerHTML = logoSVG("lsvg", C.brand.color) + `<div id="word">${C.brand.name}</div>`;
  $("tag").innerHTML = `<span class="w"><span>${C.brand.tagline}</span></span>`;
  $("elogo").innerHTML = logoSVG("esvg", C.brand.color);
  $("eword").textContent = C.brand.name; $("etag").textContent = C.brand.tagline; $("ctatxt").textContent = C.brand.cta;
  $("eurl").textContent = C.brand.url; $("enote").textContent = C.brand.note || ""; $("credit").textContent = C.credit || "";

  const master = $("master");
  const pg = $("pg");
  pg.style.width = master.style.width = C.footage.w + "px";
  pg.style.height = master.style.height = C.footage.h + "px";

  const heads = C.headlines.map((h) => { const n = el("div", flood, "hl " + (h.pos || "top"), words(stitched(h.html))); n._s = h; return n; });
  const rings = (C.rings || []).map((r) => { const n = el("div", pg, "ring" + (r.dim ? " dim" : "")); Object.assign(n.style, { left: r.rect[0] + "px", top: r.rect[1] + "px", width: r.rect[2] + "px", height: r.rect[3] + "px" }); n._s = r; return n; });
  const notes = (C.footnotes || []).map((f) => { const n = el("div", flood, "fn", f.text); n._s = f; return n; });

  function cardNode(parent, c) {
    const box = el("div", parent, "crop card");
    Object.assign(box.style, { left: c.box[0] + "px", top: c.box[1] + "px", width: c.box[2] + "px", height: c.box[3] + "px" });
    const img = el("img", box); img.src = c.src; img.alt = "";
    img.style.width = (c.pageW || C.footage.w) + "px"; img.style.height = (c.pageH || C.footage.h) + "px";
    const rs = (c.rings || []).map((r) => { const n = el("div", box, "tag-ring"); n._s = r; return n; });
    const ms = (c.marks || []).map((m) => { const n = el("div", box, "mark"); n._s = m; return n; });
    return { box, img, rs, ms, c };
  }
  const placeCard = (K, t, base) => {
    const { box, img, rs, ms, c } = K, [px, py] = c.focus, s = c.scale * (1 + (c.push || 0) * P(t, base.t, base.until));
    const x0 = px - c.box[2] / 2 / s, y0 = py - c.box[3] / 2 / s;
    img.style.transform = `translate(${-x0 * s}px,${-y0 * s}px) scale(${s})`;
    const p = P(t, c.in, c.in + 0.7, E.outQ);
    box.style.opacity = p; box.style.transform = `translateY(${(1 - p) * 70}px)`;
    for (const n of rs.concat(ms)) {
      const r = n._s;
      Object.assign(n.style, { left: (r.rect[0] - x0) * s + "px", top: (r.rect[1] - y0) * s + "px", width: r.rect[2] * s + "px", height: r.rect[3] * s + "px" });
    }
    for (const n of rs) n.style.opacity = P(t, n._s.t, n._s.t + 0.3, E.outC);
    for (const n of ms) n.style.transform = `scaleX(${P(t, n._s.t, n._s.t + (n._s.dur || 0.6), E.ioC)})`;
  };
  const stills = (C.stillScenes || []).map((S) => {
    const root = el("div", flood, "still");
    const cards = S.cards.map((c) => cardNode(root, c));
    const hl = el("div", root, "hl " + (S.pos || "top"), words(stitched(S.headline)));
    hl._s = { t: S.t, until: S.until };
    const sub = S.sub ? el("div", root, "sub", S.sub) : null;
    return { S, root, cards, hl, sub };
  });
  const stmts = (C.statements || []).map((s) => { const n = el("div", flood, "stmt", s.text); n._s = s; return n; });

  const big = el("div", cx, "big", C.climax.big.html), bigsub = el("div", cx, "bigsub", C.climax.big.sub || "");
  const slides = C.climax.slides.map((s) => {
    const root = el("div", cx, "sl"); el("div", root, "say", s.say);
    const K = cardNode(root, Object.assign({ scale: s.scale, in: s.t }, s));
    return { s, root, K };
  });
  const raps = (C.climax.rapid ? C.climax.rapid.srcs : []).map((src) => { const n = el("img", cx, "rap"); n.src = src; n.alt = ""; return n; });
  const cxfn = el("div", cx, "cxfn", C.climax.footnote || "");

  /* ---------- the concept layer (cold open) ---------- */
  const canvas = $("cold"), ctx = canvas.getContext("2d");

  /* ---------- camera and clock ---------- */
  function recS(t) {
    const K = C.footage.knots;
    if (t <= K[0][0]) return K[0][1];
    for (let i = 1; i < K.length; i++) if (t <= K[i][0]) return lerp(K[i - 1][1], K[i][1], (t - K[i - 1][0]) / (K[i][0] - K[i - 1][0]));
    return K[K.length - 1][1];
  }
  function key(tab, t, logFirst) {
    if (t <= tab[0][0]) return tab[0].slice(1);
    for (let i = 1; i < tab.length; i++) if (t <= tab[i][0]) {
      const p = E.ioC((t - tab[i - 1][0]) / (tab[i][0] - tab[i - 1][0]));
      return tab[i].slice(1).map((v, k) => (k === 0 && logFirst ? Math.exp(lerp(Math.log(tab[i - 1][1]), Math.log(v), p)) : lerp(tab[i - 1][k + 1], v, p)));
    }
    return tab[tab.length - 1].slice(1);
  }
  function headline(n, t) {
    const { t: t0, until } = n._s, on = t >= t0 - 0.02 && t < until;
    n.style.opacity = on ? 1 : 0;
    if (!on) return;
    n.querySelectorAll(".w > span").forEach((s, i) => { s.style.transform = `translateY(${(1 - P(t, t0 + i * 0.07, t0 + i * 0.07 + 0.6, E.outQ)) * 115}%)`; });
    const st = n.querySelector(".st");
    if (st) st.style.clipPath = `inset(0 ${(1 - P(t, t0 + 0.75, t0 + 1.35, E.ioC)) * 100}% 0 0)`;
  }
  const paths = (svg) => [...$(svg).querySelectorAll("path")].map((p) => { const l = p.getTotalLength(); p.style.strokeDasharray = `${l} ${l + 2}`; return [p, l]; });
  const logoA = paths("lsvg"), logoB = paths("esvg");
  function stitch(list, p) {
    let left = p * list.reduce((a, [, l]) => a + l, 0);
    for (const [n, l] of list) { const d = clamp(left, 0, l); n.style.strokeDashoffset = l - d; n.style.visibility = d > 0 ? "visible" : "hidden"; left -= d; }
  }

  const lockLeft = () => 960 - (196 + $("word").offsetWidth) / 2;
  const D = C.coldOpen.drop, OX = C.coldOpen.floodFrom[0], OY = C.coldOpen.floodFrom[1];
  const LK = C.lockup, EN = C.end, CL = C.climax;

  function render(t) {
    /* cold open */
    const a1on = t < D + 0.5;
    setd(a1, a1on); setd(canvas, a1on);
    if (a1on) {
      window.FILM_CONCEPT(ctx, t, C);
      quiet.forEach((q) => { const p = P(t, q._t, q._t + 0.9, E.outC), o = 1 - P(t, C.coldOpen.quietEnd - 0.4, C.coldOpen.quietEnd); q.style.opacity = p * o; q.style.filter = `blur(${(1 - p) * 7}px)`; });
      let shake = 0, flash = 0;
      for (const n of slams) {
        const { t: a, until: b } = n._s, on = t >= a && t < b;
        n.style.opacity = on ? P(t, a, a + 0.04) : 0;
        if (on) { n.style.transform = `translateY(-50%) scale(${1.05 - 0.05 * P(t, a, b, E.outC)})`; shake = Math.max(shake, 1 - P(t, a, a + 0.55)); }
        if (t >= a) flash = Math.max(flash, (n === slams[0] ? 0.4 : 0.12) * (1 - P(t, a, a + 0.22)));
      }
      a1.style.transform = canvas.style.transform = `translate(${Math.sin(t * 91) * 11 * shake * shake}px,${Math.cos(t * 77) * 8 * shake * shake}px)`;
      $("fl").style.opacity = flash;
      for (const n of payoff) { const { t: a, until: b } = n._s; n.style.opacity = P(t, a, a + 0.3) * (1 - P(t, b - 0.2, b)) * (t < b ? 1 : 0); }
    }

    /* white world */
    const white = t >= D && t < CL.t;
    setd(flood, white);
    if (white) {
      flood.style.clipPath = t < D + 0.45 ? `circle(${P(t, D, D + 0.42, E.outE) * 2400}px at ${OX}px ${OY}px)` : "none";
      const lockOn = t < LK.until + 0.52;
      setd($("lock"), lockOn);
      if (lockOn) {
        stitch(logoA, P(t, D + 0.06, D + 1.3, E.ioS));
        $("word").style.clipPath = `inset(-20% ${(1 - P(t, D + 1.1, D + 1.75, E.outQ)) * 100}% -20% 0)`;
        const m = P(t, LK.until, LK.until + 0.48, E.ioC), ll = lockLeft();
        $("lock").style.left = ll + "px";
        $("lock").style.transform = `translate(${lerp(0, LK.to[0] - ll, m)}px,${lerp(0, LK.to[1] - 402, m)}px) scale(${lerp(1, LK.to[2], m)})`;
        $("lock").style.opacity = 1 - P(t, LK.until + 0.28, LK.until + 0.44);
      }
      $("tag").style.opacity = t >= LK.tagAt && t < LK.until + 0.2 ? 1 - P(t, LK.until, LK.until + 0.2) : 0;
      $("tag").querySelector(".w > span").style.transform = `translateY(${(1 - P(t, LK.tagAt, LK.tagAt + 0.6, E.outQ)) * 115}%)`;

      const F = C.footage, pageOn = t >= F.start && t < F.start + F.duration;
      setd($("win"), pageOn);
      if (pageOn) {
        const [l, tp, w, h, rad, sh] = key(F.frame, t), [s, cx0, cy0, fx, fy] = key(F.cam, t, true), wn = $("win");
        Object.assign(wn.style, { left: l + "px", top: tp + "px", width: w + "px", height: h + "px", borderRadius: rad + "px", opacity: P(t, F.start + 0.15, F.start + 0.5) });
        wn.style.boxShadow = sh > 0 ? `0 30px 90px rgba(30,25,15,${0.16 * sh}), 0 0 0 1.5px rgba(231,228,222,${sh})` : "none";
        pg.style.transform = `translate(${fx * w - s * cx0}px,${fy * h - s * cy0}px) scale(${s})`;
        const T = C.typing;
        if (T) {
          const on = t >= T.t && t < T.until, n = $("typed");
          n.style.visibility = on ? "visible" : "hidden";
          Object.assign(n.style, { left: T.rect[0] + "px", top: T.rect[1] + "px", width: T.rect[2] + "px", height: T.rect[3] + "px", lineHeight: T.rect[3] + "px", fontSize: (T.size || 20) + "px", paddingLeft: (T.pad || 10) + "px", background: T.bg || "#fff" });
          if (on) $("ty").textContent = T.text.slice(0, Math.min(T.text.length, Math.floor((t - T.t) / (T.step || 0.115)) + 1));
        }
        for (const n of rings) { const r = n._s; n.style.opacity = P(t, r.t, r.t + 0.4, E.outC) * (1 - P(t, r.until - 0.22, r.until)); }
        const rp = C.click ? P(t, C.click.t, C.click.t + 0.45, E.outC) : 1, rpn = $("ripple");
        if (C.click) { rpn.style.left = C.click.at[0] + "px"; rpn.style.top = C.click.at[1] + "px"; rpn.style.opacity = t >= C.click.t ? 1 - rp : 0; rpn.style.transform = `scale(${1 + 3.2 * rp})`; }
      }
      heads.forEach((n) => headline(n, t));

      const K = C.clock, pill = $("pill"), pillOn = K && t >= K.from && t < K.until;
      pill.style.opacity = pillOn ? P(t, K.from, K.from + 0.2) : 0;
      if (pillOn) {
        const sec = clamp(recS(t) - K.startS, 0, K.seconds), done = t >= K.doneAt, p = P(t, K.doneAt, K.doneAt + 0.25, E.outB);
        $("clk").textContent = `${Math.floor(sec / 60)}:${String(Math.floor(sec % 60)).padStart(2, "0")}`;
        pill.style.transform = `scale(${1 + 0.16 * p})`;
        pill.style.background = done ? C.brand.color : "#fff"; pill.style.borderColor = done ? C.brand.color : "#e7e4de";
        $("clk").style.color = done ? "#fff" : C.brand.ink;
        pill.querySelector("span").style.color = done ? "#fff" : "#6e6a62";
        pill.querySelector("em").style.background = done ? "#fff" : C.brand.color;
      }
      for (const n of notes) { const f = n._s; n.style.opacity = P(t, f.t, f.t + 0.4) * (1 - P(t, f.until - 0.3, f.until)); }
      for (const Q of stills) {
        const on = t >= Q.S.t && t < Q.S.until;
        setd(Q.root, on);
        if (on) { headline(Q.hl, t); Q.cards.forEach((K2) => placeCard(K2, t, Q.S)); if (Q.sub) Q.sub.style.opacity = P(t, Q.S.t + 0.9, Q.S.t + 1.5); }
      }
      let anyStmt = false;
      for (const n of stmts) { const s = n._s, on = t >= s.t && t < s.until; n.style.opacity = on ? P(t, s.t, s.t + 0.22) : 0; anyStmt = anyStmt || on; }
      setd($("stmtbg"), anyStmt);
    }

    /* climax on black */
    const cxOn = t >= CL.t && t < EN.t;
    setd(cx, cxOn);
    if (cxOn) {
      const bo = t < CL.big.until;
      big.style.opacity = bo ? 1 : 0; big.style.transform = `scale(${1.05 - 0.05 * P(t, CL.t, CL.big.until, E.outC)})`;
      bigsub.style.opacity = bo ? P(t, CL.t + 0.7, CL.t + 1.2) : 0;
      for (const S of slides) {
        const { t: a, until: b } = S.s, on = t >= a && t < b;
        setd(S.root, on);
        if (on) {
          placeCard(S.K, t, S.s);
          const p = P(t, a, a + 0.42, E.outQ);
          S.K.box.style.transform = `translateX(${(1 - p) * 180}px) scale(${1 + 0.035 * P(t, a, b)})`;
          S.K.box.style.opacity = p;
          S.root.querySelector(".say").style.opacity = P(t, a + 0.04, a + 0.2);
        }
      }
      raps.forEach((n) => { n.style.visibility = "hidden"; });
      const Rp = CL.rapid;
      if (Rp && t >= Rp.t) {
        const k = Math.min(Rp.srcs.length - 1, Math.floor((t - Rp.t) / Rp.step)), n = raps[k];
        n.style.visibility = "visible";
        n.style.transform = `scale(${1.1 - 0.1 * P(t, Rp.t + k * Rp.step, Rp.t + (k + 1) * Rp.step, E.outC)})`;
      }
      cxfn.style.opacity = CL.footnoteUntil && t < CL.footnoteUntil && t >= (CL.footnoteFrom || 0) ? 1 : 0;
    }

    /* end card */
    const endOn = t >= EN.t;
    setd(end, endOn);
    if (endOn) {
      const ew = $("eword").offsetWidth, el0 = 960 - (190 + ew) / 2;
      $("elogo").style.left = el0 + "px"; $("eword").style.left = el0 + 190 + "px";
      const u = logoB[0][0].getPointAtLength(0), sc = 170 / C.brand.logoView[2];
      const hx0 = el0 + (u.x - C.brand.logoView[0]) * sc, hy0 = 339 + (u.y - C.brand.logoView[1]) * sc, th = $("ethread");
      th.setAttribute("d", `M-40 770 C 180 700, 300 840, 470 742 S ${hx0 - 107} ${hy0 + 195}, ${hx0} ${hy0}`);
      const thL = th.getTotalLength(), span = EN.hit - EN.t, tp = 0.62 * P(t, EN.t, EN.t + span * 0.63, E.outC) + 0.38 * P(t, EN.t + span * 0.52, EN.hit - 0.22, E.inC);
      th.style.strokeDasharray = `${thL} ${thL + 2}`; th.style.strokeDashoffset = thL * (1 - tp); th.style.opacity = 1 - P(t, EN.hit, EN.hit + 0.7);
      stitch(logoB, P(t, EN.hit - 0.28, EN.hit + 0.02, E.ioS));
      $("eword").style.opacity = t >= EN.hit ? 1 : 0;
      $("eword").style.transform = `scale(${1.03 - 0.03 * P(t, EN.hit, EN.hit + 0.8, E.outC)})`;
      $("etag").style.opacity = P(t, EN.tagAt, EN.tagAt + 0.55);
      $("cta").style.opacity = P(t, EN.ctaAt, EN.ctaAt + 0.2);
      $("cta").style.transform = `scale(${0.92 + 0.08 * P(t, EN.ctaAt, EN.ctaAt + 0.45, E.outB)})`;
      $("eurl").style.opacity = P(t, EN.ctaAt + 0.35, EN.ctaAt + 0.8);
      $("enote").style.opacity = P(t, EN.ctaAt + 0.7, EN.ctaAt + 1.2);
      $("shine").style.left = `${lerp(-120, 520, P(t, EN.shineAt, EN.shineAt + 0.7, E.ioC))}px`;
      $("credit").style.opacity = P(t, EN.creditAt, EN.creditAt + 0.7);
    }
    $("fade").style.opacity = P(t, C.duration - 0.9, C.duration - 0.1, E.ioS);
  }

  const clock = { _t: -1, get t() { return this._t; }, set t(v) { this._t = v; render(v); } };
  const tl = gsap.timeline({ paused: true });
  tl.fromTo(clock, { t: 0 }, { t: C.duration, duration: C.duration, ease: "none" }, 0);
  window.__timelines = window.__timelines || {};
  window.__timelines["main"] = tl;
  window.__filmTimeline = tl;
  tl.seek(0);
  render(0);
})();
