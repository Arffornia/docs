/*
 * Arffornia screen previews: shared isometric engine (canvas 2D, deterministic).
 *
 * Everything is a pure function of time t (seconds), so a page can be played live
 * (requestAnimationFrame) or recorded frame by frame (window.renderFrame(t)).
 * Machines are mock prototypes of the tier plan (spec 003): Miner, Smelter, Constructor,
 * Foundry, Assembler and the Space Elevator. They stand in for the Blockbench models.
 */
(function () {
  'use strict';
  const C30 = Math.cos(Math.PI / 6);
  const TAU = Math.PI * 2;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
  const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  const easeOut = (t) => 1 - Math.pow(1 - clamp(t, 0, 1), 3);
  const easeIn = (t) => Math.pow(clamp(t, 0, 1), 3);
  const fract = (x) => x - Math.floor(x);
  const hex = (h) => {
    if (Array.isArray(h)) return h;
    h = h.replace('#', '');
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  };
  const tone = (h, f) => { const c = hex(h); return f >= 0 ? c.map((v) => v + (255 - v) * f) : c.map((v) => v * (1 + f)); };
  const css = (c, a) => { c = hex(c); return a === undefined ? `rgb(${c[0] | 0},${c[1] | 0},${c[2] | 0})` : `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`; };
  const mixc = (a, b, t) => { a = hex(a); b = hex(b); return [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)]; };
  function rng(seed) {
    return function () {
      seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // ---------------------------------------------------------------- themes
  const THEMES = {
    night: {
      name: 'night', isDark: true, additive: true,
      bg: ['#0b1116', '#0f1a20', '#141f26'], fog: '#0d161c',
      grid: [47, 209, 193], gridA: 0.075,
      slab: '#1a252d', slabEdge: '#e0703c', seam: [255, 255, 255], seamA: 0.04,
      body: '#2a3640', body2: '#33424e', plinth: '#1c252c', roof: '#3b4b57', dark: '#10171c', glass: [120, 220, 230],
      steel: '#8a9aa6', rim: [214, 232, 240], rimA: 0.22,
      top: 0.16, sideL: 0.0, sideR: -0.32,
      orange: '#e0703c', orangeHot: '#ff9a52', teal: '#2fd1c1', tealDeep: '#0f8f86', warn: '#f2b134',
      shadow: [0, 0, 0], shadowA: 0.55, glowK: 1.0, smoke: [150, 170, 180], smokeA: 0.22,
      ore: '#5b4a42', ingot: '#e0703c', plate: '#b9c6cf', rod: '#7f909c', rplate: '#d6dee4', pkg: '#e0703c',
      silhouette: '#121c23', vignette: 0.62, shaft: '#10171c', deck: '#1a2329', itemK: 1.2,
    },
    maquette: {
      name: 'maquette', isDark: false, additive: false,
      bg: ['#f4f6f7', '#e9eef1', '#dfe6ea'], fog: '#e9eef1',
      grid: [70, 96, 111], gridA: 0.11,
      slab: '#e3e9ed', slabEdge: '#e0703c', seam: [70, 96, 111], seamA: 0.12,
      body: '#d9e1e6', body2: '#e7edf0', plinth: '#b8c5cd', roof: '#f1f4f6', dark: '#46606f', glass: [15, 143, 134],
      steel: '#9eadb7', rim: [255, 255, 255], rimA: 0.75,
      top: 0.42, sideL: 0.0, sideR: -0.14,
      orange: '#e0703c', orangeHot: '#f08a4e', teal: '#0f8f86', tealDeep: '#0b6f68', warn: '#e0a21e',
      shadow: [46, 66, 80], shadowA: 0.26, glowK: 0.55, smoke: [176, 190, 198], smokeA: 0.35,
      ore: '#8a7468', ingot: '#e0703c', plate: '#a5b3bc', rod: '#5a6a74', rplate: '#c3ced5', pkg: '#e0703c',
      silhouette: '#e2e8eb', vignette: 0.12, shaft: '#cfe3e1', deck: '#c3ced5', itemK: 1.2,
    },
  };

  // ---------------------------------------------------------------- iso renderer
  class Iso {
    constructor(ctx, th) { this.ctx = ctx; this.th = th; this.s = 40; this.ox = 0; this.oy = 0; this.base = new DOMMatrix(); this.list = []; this.t = 0; this.power = 1; this.curPower = 1; }
    p(x, y, z) { return [(x - y) * C30 * this.s + this.ox, (x + y) * 0.5 * this.s - z * this.s + this.oy]; }
    reset() { this.ctx.setTransform(this.base); }
    // Face-local coordinates in block units. top: u=x, v=y. left (+y face): u=x, v=z (up). right (+x face): u from y+d towards y, v=z.
    face(kind, x, y, z, w, d, h) {
      const s = this.s; this.reset();
      let o;
      if (kind === 'top') { o = this.p(x, y, z + h); this.ctx.transform(C30 * s, 0.5 * s, -C30 * s, 0.5 * s, o[0], o[1]); }
      else if (kind === 'left') { o = this.p(x, y + d, z); this.ctx.transform(C30 * s, 0.5 * s, 0, -s, o[0], o[1]); }
      else { o = this.p(x + w, y + d, z); this.ctx.transform(C30 * s, -0.5 * s, 0, -s, o[0], o[1]); }
    }
    poly(pts, fill, stroke, lw) {
      const c = this.ctx; this.reset(); c.beginPath(); c.moveTo(pts[0][0], pts[0][1]);
      for (let i = 1; i < pts.length; i++) c.lineTo(pts[i][0], pts[i][1]);
      c.closePath(); if (fill) { c.fillStyle = fill; c.fill(); } if (stroke) { c.strokeStyle = stroke; c.lineWidth = lw || 1; c.stroke(); }
    }
    line(a, b, col, lw, cap) { const c = this.ctx; this.reset(); c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); c.strokeStyle = col; c.lineWidth = lw; c.lineCap = cap || 'butt'; c.stroke(); }
    add(depth, fn) { const pw = this.curPower; this.list.push({ d: depth, fn: () => { this.power = pw; fn(); this.power = 1; } }); }
    flush() { this.list.sort((a, b) => a.d - b.d); for (const e of this.list) e.fn(); this.list = []; }

    // A shaded box with optional per-face decoration callbacks (called in face-local coordinates).
    box(x, y, z, w, d, h, col, o = {}) {
      const th = this.th, c = this.ctx, base = hex(col);
      const P = (a, b, cc) => this.p(a, b, cc);
      // left (+y) face
      this.face('left', x, y, z, w, d, h);
      let g = c.createLinearGradient(0, 0, 0, h);
      g.addColorStop(0, css(tone(base, th.sideL - (o.ao === false ? 0 : 0.16))));
      g.addColorStop(Math.min(1, 0.6 / Math.max(h, 0.01)), css(tone(base, th.sideL)));
      g.addColorStop(1, css(tone(base, th.sideL + 0.04)));
      c.fillStyle = g; c.fillRect(0, 0, w, h);
      if (o.left) o.left(this, w, h);
      // right (+x) face
      this.face('right', x, y, z, w, d, h);
      g = c.createLinearGradient(0, 0, 0, h);
      g.addColorStop(0, css(tone(base, th.sideR - (o.ao === false ? 0 : 0.14))));
      g.addColorStop(Math.min(1, 0.6 / Math.max(h, 0.01)), css(tone(base, th.sideR)));
      g.addColorStop(1, css(tone(base, th.sideR + 0.03)));
      c.fillStyle = g; c.fillRect(0, 0, d, h);
      if (o.right) o.right(this, d, h);
      // top
      this.face('top', x, y, z, w, d, h);
      g = c.createLinearGradient(0, 0, w, d);
      g.addColorStop(0, css(tone(base, th.top + 0.05)));
      g.addColorStop(1, css(tone(base, th.top - 0.03)));
      c.fillStyle = g; c.fillRect(0, 0, w, d);
      if (o.top) o.top(this, w, d);
      // rim light on the three front edges
      if (o.rim !== false) {
        const a = P(x, y + d, z + h), b = P(x + w, y + d, z + h), e = P(x + w, y, z + h), f = P(x + w, y + d, z);
        const rc = css(th.rim, th.rimA * (o.rimK || 1));
        this.line(a, b, rc, 1); this.line(b, e, rc, 1); this.line(b, f, css(th.rim, th.rimA * 0.45 * (o.rimK || 1)), 1);
      }
    }

    // Vertical cylinder.
    cyl(cx, cy, z, r, h, col, o = {}) {
      const c = this.ctx, s = this.s, th = this.th;
      const rx = 1.2247 * r * s, ry = 0.7071 * r * s;
      const b = this.p(cx, cy, z), t = this.p(cx, cy, z + h);
      this.reset();
      const g = c.createLinearGradient(b[0] - rx, 0, b[0] + rx, 0);
      g.addColorStop(0, css(tone(col, th.sideL - 0.05)));
      g.addColorStop(0.35, css(tone(col, th.sideL + 0.12)));
      g.addColorStop(1, css(tone(col, th.sideR - 0.05)));
      c.beginPath(); c.moveTo(t[0] - rx, t[1]); c.lineTo(b[0] - rx, b[1]);
      c.ellipse(b[0], b[1], rx, ry, 0, Math.PI, 0, true); c.lineTo(t[0] + rx, t[1]);
      c.ellipse(t[0], t[1], rx, ry, 0, 0, Math.PI, false); c.closePath(); c.fillStyle = g; c.fill();
      if (o.band) o.band(this, b, t, rx, ry);
      if (o.noTop) return;
      c.beginPath(); c.ellipse(t[0], t[1], rx, ry, 0, 0, TAU); c.fillStyle = css(o.topCol || tone(col, th.top)); c.fill();
      c.strokeStyle = css(th.rim, th.rimA * 0.8); c.lineWidth = 1; c.stroke();
    }

    // Soft light (additive on dark themes).
    glow(x, y, z, rpx, col, a) {
      const c = this.ctx, th = this.th; a *= this.power; if (a <= 0.003) return;
      const q = this.p(x, y, z); this.reset();
      const g = c.createRadialGradient(q[0], q[1], 0, q[0], q[1], rpx);
      const k = a * th.glowK;
      g.addColorStop(0, css(col, k)); g.addColorStop(0.35, css(col, k * 0.35)); g.addColorStop(1, css(col, 0));
      c.save(); c.globalCompositeOperation = th.additive ? 'lighter' : 'source-over'; c.fillStyle = g;
      c.fillRect(q[0] - rpx, q[1] - rpx, rpx * 2, rpx * 2); c.restore();
    }
    // Light pool on the floor (ellipse in floor plane).
    pool(x, y, r, col, a) {
      const c = this.ctx, th = this.th; a *= this.power; if (a <= 0.003) return;
      this.face('top', x - r, y - r, 0, 2 * r, 2 * r, 0);
      const g = c.createRadialGradient(r, r, 0, r, r, r);
      g.addColorStop(0, css(col, a * th.glowK)); g.addColorStop(1, css(col, 0));
      c.save(); c.globalCompositeOperation = th.additive ? 'lighter' : 'source-over'; c.fillStyle = g; c.fillRect(0, 0, 2 * r, 2 * r); c.restore();
    }
    // Emissive strip in face-local coordinates (call inside a face transform).
    strip(u0, v0, u1, v1, col, a, blurPx) {
      const c = this.ctx, pw = this.power; c.save(); c.shadowColor = css(col, Math.min(1, a) * pw); c.shadowBlur = (blurPx || 10) * this.th.glowK * pw;
      c.fillStyle = css(mixc(tone(this.th.dark, -0.2), tone(col, 0.25), 0.25 + 0.75 * pw), a); c.fillRect(u0, v0, u1 - u0, v1 - v0); c.restore();
    }
  }

  // ---------------------------------------------------------------- items
  function drawItem(R, kind, x, y, z, axis, scale) {
    const th = R.th; const sc = (scale === undefined ? 1 : scale) * (th.itemK || 1); if (sc <= 0.02) return;
    const W = (a) => a * sc;
    const sw = (w, d) => (axis === 'y' ? [d, w] : [w, d]);
    if (kind === 'ore') {
      const a = W(0.34); R.box(x - a / 2, y - a / 2, z, a, a, a, th.ore, {
        top: (r) => { const c = r.ctx; c.fillStyle = css(th.orangeHot, 0.95); c.fillRect(a * 0.15, a * 0.2, a * 0.22, a * 0.2); c.fillRect(a * 0.6, a * 0.55, a * 0.18, a * 0.18); },
        left: (r) => { r.ctx.fillStyle = css(th.orange, 0.9); r.ctx.fillRect(a * 0.55, a * 0.25, a * 0.2, a * 0.2); }, rimK: 0.6,
      });
    } else if (kind === 'ingot') {
      const [w, d] = sw(W(0.44), W(0.24)); R.box(x - w / 2, y - d / 2, z, w, d, W(0.13), th.ingot, { rimK: 1.4 });
    } else if (kind === 'plate') {
      const a = W(0.44); R.box(x - a / 2, y - a / 2, z, a, a, W(0.07), th.plate, { rimK: 1.2 });
      R.box(x - a / 2 + W(0.05), y - a / 2 + W(0.05), z + W(0.07), a - W(0.1), a - W(0.1), W(0.05), th.plate, { rimK: 0.8, ao: false });
    } else if (kind === 'rod') {
      for (let i = -1; i <= 1; i += 2) {
        const [w, d] = sw(W(0.52), W(0.1)); const ox = axis === 'y' ? i * W(0.09) : 0, oy = axis === 'y' ? 0 : i * W(0.09);
        R.box(x - w / 2 + ox, y - d / 2 + oy, z, w, d, W(0.1), th.rod, { rimK: 1.2 });
      }
    } else if (kind === 'rplate') {
      const a = W(0.48); R.box(x - a / 2, y - a / 2, z, a, a, W(0.13), th.rplate, {
        top: (r) => { r.strip(a * 0.4, a * 0.08, a * 0.6, a * 0.92, th.teal, 0.95, 8); const c = r.ctx; c.fillStyle = css(th.orange); const k = a * 0.16; c.fillRect(0, 0, k, k); c.fillRect(a - k, 0, k, k); c.fillRect(0, a - k, k, k); c.fillRect(a - k, a - k, k, k); },
        rimK: 1.2,
      });
    } else if (kind === 'pkg') {
      const a = W(0.42); R.box(x - a / 2, y - a / 2, z, a, a, a * 0.9, th.pkg, {
        left: (r, w, h) => { r.ctx.fillStyle = css(tone(th.dark, 0.05), 0.85); r.ctx.fillRect(0, h * 0.42, w, h * 0.16); },
        right: (r, w, h) => { r.ctx.fillStyle = css(tone(th.dark, 0.05), 0.85); r.ctx.fillRect(0, h * 0.42, w, h * 0.16); },
        top: (r, w, d) => { r.ctx.fillStyle = css(tone(th.dark, 0.05), 0.85); r.ctx.fillRect(w * 0.42, 0, w * 0.16, d); }, rimK: 1.3,
      });
    }
  }

  // ---------------------------------------------------------------- conveyors
  const BELT_V = 0.9; // blocks per second
  const GAP = 1.5;   // blocks between items -> one item every GAP/BELT_V seconds
  const CYCLE = GAP / BELT_V;

  function beltSegment(R, cv, i) {
    const th = R.th; const t = R.t;
    const L = Math.min(1, cv.len - i);
    let x, y, w, d;
    if (cv.axis === 'x') { x = cv.x0 + i; y = cv.c - 0.37; w = L; d = 0.74; }
    else { x = cv.c - 0.37; y = cv.y0 + i; w = 0.74; d = L; }
    const depth = x + w / 2 + y + d / 2 + 0.11;
    R.add(depth, () => {
      // frame + belt
      R.box(x, y, 0, w, d, 0.2, th.plinth, {
        top: (r, ww, dd) => {
          const c = r.ctx; c.fillStyle = css(tone(th.dark, -0.15)); c.fillRect(0, 0, ww, dd);
          // moving chevrons
          const along = cv.axis === 'x' ? ww : dd; const off = fract((t * BELT_V + i) / 0.5) * 0.5;
          c.strokeStyle = css(th.isDark ? [70, 86, 96] : tone(th.dark, 0.35), 0.9); c.lineWidth = 0.05;
          for (let k = -1; k < along / 0.5 + 1; k++) {
            const s0 = k * 0.5 + off; c.beginPath();
            if (cv.axis === 'x') { c.moveTo(s0, 0.1); c.lineTo(s0 + 0.14, dd / 2); c.lineTo(s0, dd - 0.1); }
            else { c.moveTo(0.1, s0); c.lineTo(ww / 2, s0 + 0.14); c.lineTo(ww - 0.1, s0); }
            c.stroke();
          }
          c.fillStyle = css(th.steel, 0.9);
          if (cv.axis === 'x') { c.fillRect(0, 0, ww, 0.07); c.fillRect(0, dd - 0.07, ww, 0.07); }
          else { c.fillRect(0, 0, 0.07, dd); c.fillRect(ww - 0.07, 0, 0.07, dd); }
        },
        left: (r, ww, hh) => { if (cv.axis === 'x') { r.ctx.fillStyle = css(th.orange, 0.85); r.ctx.fillRect(0, hh * 0.55, ww, hh * 0.12); } },
        right: (r, dd, hh) => { if (cv.axis === 'y') { r.ctx.fillStyle = css(th.orange, 0.85); r.ctx.fillRect(0, hh * 0.55, dd, hh * 0.12); } },
        rimK: 0.8,
      });
    });
  }

  function beltItems(R, cv) {
    const t = R.t; const n = Math.ceil((cv.len + 0.35) / GAP); const cyc = n * GAP;
    for (let k = 0; k < n; k++) {
      const u = fract((t * BELT_V + (cv.ph || 0) + k * GAP) / cyc) * cyc - 0.05;
      if (u < 0 || u > cv.len + 0.28) continue;
      const sc = cv.noFade ? 1 : smooth(0, 0.3, u);
      const x = cv.axis === 'x' ? cv.x0 + u : cv.c, y = cv.axis === 'x' ? cv.c : cv.y0 + u;
      R.add(x + y + 0.62, () => drawItem(R, cv.item, x, y, 0.2, cv.axis, sc));
    }
  }

  // phase of a machine fed by conveyor cv: 0 at item arrival, grows to 1 one cycle later
  const arrivalPhase = (t, cv) => fract((t * BELT_V + (cv.ph || 0) - cv.len) / GAP);

  // ---------------------------------------------------------------- machines
  function hatch(r, u0, v0, u1, v1, th, hot) {
    const c = r.ctx; c.fillStyle = css(tone(th.dark, -0.4)); c.fillRect(u0, v0, u1 - u0, v1 - v0);
    if (hot) { const g = c.createLinearGradient(0, v0, 0, v1); g.addColorStop(0, css(hot, 0.0)); g.addColorStop(1, css(hot, 0.55 * r.power)); c.fillStyle = g; c.fillRect(u0, v0, u1 - u0, v1 - v0); }
    c.strokeStyle = css(th.steel, 0.8); c.lineWidth = 0.04; c.strokeRect(u0, v0, u1 - u0, v1 - v0);
  }
  function vents(r, u0, v0, w, h, n, th) {
    const c = r.ctx; c.fillStyle = css(tone(th.dark, -0.2), 0.85);
    for (let i = 0; i < n; i++) c.fillRect(u0, v0 + (i * h) / n, w, (h / n) * 0.45);
  }
  function seams(r, w, h, th, us, vs) {
    const c = r.ctx; c.strokeStyle = css(th.seam, th.seamA * 2.2); c.lineWidth = 0.025;
    (us || []).forEach((u) => { c.beginPath(); c.moveTo(u, 0.05); c.lineTo(u, h - 0.05); c.stroke(); });
    (vs || []).forEach((v) => { c.beginPath(); c.moveTo(0.05, v); c.lineTo(w - 0.05, v); c.stroke(); });
  }
  function hazard(r, w, h, th) {
    const c = r.ctx; c.save(); c.beginPath(); c.rect(0, 0, w, h); c.clip();
    c.fillStyle = css(tone(th.dark, -0.1)); c.fillRect(0, 0, w, h); c.fillStyle = css(th.warn, 0.9);
    for (let u = -h; u < w + h; u += 0.24) { c.beginPath(); c.moveTo(u, 0); c.lineTo(u + 0.12, 0); c.lineTo(u + 0.12 + h, h); c.lineTo(u + h, h); c.closePath(); c.fill(); }
    c.restore();
  }
  function screen(r, u0, v0, w, h, th, t, seed) {
    const c = r.ctx; c.fillStyle = css(tone(th.dark, -0.45)); c.fillRect(u0, v0, w, h);
    const g = c.createLinearGradient(0, v0, 0, v0 + h); g.addColorStop(0, css(th.teal, 0.12 * r.power)); g.addColorStop(1, css(th.teal, 0.3 * r.power)); c.fillStyle = g; c.fillRect(u0, v0, w, h);
    const R = rng(seed); c.fillStyle = css(th.teal, 0.95 * r.power);
    for (let i = 0; i < 4; i++) { const lw = (0.35 + 0.65 * fract(R() + t * 0.13 * (i + 1))) * (w - 0.12); c.fillRect(u0 + 0.06, v0 + h - 0.1 - i * (h - 0.12) / 4, lw, (h - 0.12) / 9); }
  }
  function plinth(R, x, y, w, d, th) {
    R.box(x - 0.1, y - 0.1, 0, w + 0.2, d + 0.2, 0.14, th.plinth, { left: (r, ww, hh) => hazard(r, ww, hh, th), right: (r, dd, hh) => hazard(r, dd, hh, th), rimK: 0.7 });
  }

  function miner(R, m) {
    const th = R.th, t = R.t, { x, y } = m; const cx = x + 1, cy = y + 1;
    const bob = Math.sin(t * 5.2) * 0.08;
    R.add(cx + cy - 0.3, () => {
      // ore node outcrop
      const rr = rng(11);
      for (let i = 0; i < 9; i++) {
        const ox = x + 0.05 + rr() * 1.5, oy = y + 0.05 + rr() * 1.5, s = 0.35 + rr() * 0.45, hh = 0.2 + rr() * 0.45;
        if (Math.abs(ox + s / 2 - cx) < 0.35 && Math.abs(oy + s / 2 - cy) < 0.35) continue;
        R.box(ox, oy, 0, s, s, hh, th.ore, { top: (r, w, d) => { r.ctx.fillStyle = css(th.orange, 0.9); r.ctx.fillRect(w * 0.3, d * 0.3, w * 0.25, d * 0.2); }, rimK: 0.5 });
      }
      // legs (back first)
      const leg = (lx, ly) => R.box(lx, ly, 0, 0.18, 0.18, 2.3, th.body2, { left: (r, w, h) => { r.ctx.fillStyle = css(th.orange, 0.9); r.ctx.fillRect(0, h - 0.18, w, 0.08); }, rimK: 0.8 });
      leg(x + 0.1, y + 0.1); leg(x + 1.72, y + 0.1); leg(x + 0.1, y + 1.72);
      // drill column
      R.cyl(cx, cy, 0.35 + bob, 0.2, 1.95, th.steel, {
        noTop: true,
        band: (r, b, tt, rx) => { const c = r.ctx; c.strokeStyle = css(th.dark, 0.6); c.lineWidth = 2; for (let k = 0; k < 7; k++) { const yy = tt[1] + fract(k / 7 + t * 1.6) * (b[1] - tt[1]); c.beginPath(); c.moveTo(b[0] - rx, yy - rx * 0.25); c.lineTo(b[0] + rx, yy + rx * 0.25); c.stroke(); } },
      });
      // sparks at the drill bit
      const c = R.ctx; const tip = R.p(cx, cy, 0.3 + bob); R.reset(); c.save(); c.globalCompositeOperation = th.additive ? 'lighter' : 'source-over';
      const sr = rng(Math.floor(t * 12));
      for (let i = 0; i < 7; i++) { const a = sr() * Math.PI - Math.PI; const l = 6 + sr() * 14; c.strokeStyle = css(th.orangeHot, (0.5 + sr() * 0.5) * R.power); c.lineWidth = 1.4; c.beginPath(); c.moveTo(tip[0], tip[1]); c.lineTo(tip[0] + Math.cos(a) * l, tip[1] + Math.sin(a) * l * 0.6); c.stroke(); }
      c.restore();
      R.glow(cx, cy, 0.3, R.s * 1.1, th.orangeHot, 0.45 + 0.15 * Math.sin(t * 23));
      leg(x + 1.72, y + 1.72);
      // head
      R.box(x, y, 2.3, 2, 2, 0.32, th.body, {
        left: (r, w, h) => { r.strip(0.15, h * 0.35, w - 0.15, h * 0.55, th.orange, 0.95, 10); },
        right: (r, d, h) => { r.strip(0.15, h * 0.35, d - 0.15, h * 0.55, th.orange, 0.95, 10); },
        top: (r, w, d) => seams(r, w, d, th, [w / 2], [d / 2]),
      });
      R.box(x + 0.55, y + 0.55, 2.62, 0.9, 0.9, 0.42, th.body2, {
        top: (r, w, d) => { // spinning fan
          const c2 = r.ctx; c2.fillStyle = css(tone(th.dark, -0.3)); c2.beginPath(); c2.arc(w / 2, d / 2, 0.38, 0, TAU); c2.fill();
          c2.fillStyle = css(th.steel, 0.95); for (let k = 0; k < 5; k++) { const a = t * 9 + (k * TAU) / 5; c2.beginPath(); c2.moveTo(w / 2, d / 2); c2.arc(w / 2, d / 2, 0.34, a, a + 0.55); c2.closePath(); c2.fill(); }
          c2.fillStyle = css(th.orange); c2.beginPath(); c2.arc(w / 2, d / 2, 0.08, 0, TAU); c2.fill();
        },
        left: (r, w, h) => vents(r, 0.12, 0.1, w - 0.24, h - 0.2, 3, th),
      });
      // output chute towards +x
      R.box(x + 2.0, cy - 0.3, 0.2, 0.32, 0.6, 0.5, th.body, { left: (r, w, h) => hatch(r, 0.05, 0.05, w - 0.05, h - 0.1, th, th.orange) });
    });
  }

  function smelter(R, m, cvIn) {
    const th = R.th, t = R.t, { x, y } = m;
    const ph = arrivalPhase(t, cvIn); const heat = 0.75 + 0.25 * Math.sin(t * 7.3) * Math.sin(t * 3.1) + 0.25 * (1 - smooth(0, 0.5, ph));
    R.add(x + y + 2, () => {
      plinth(R, x, y, 2, 2, th);
      R.box(x, y, 0.14, 2, 2, 1.55, th.body, {
        left: (r, w, h) => {
          seams(r, w, h, th, [0.32, w - 0.32]);
          const c = r.ctx; c.fillStyle = css(tone(th.dark, -0.3)); c.fillRect(0.5, 0.32, w - 1.0, 0.82);
          const hp = heat * r.power; const g = c.createLinearGradient(0, 0.32, 0, 1.14); g.addColorStop(0, css(th.orange, 0.5 * hp)); g.addColorStop(1, css(th.orangeHot, 1.0 * Math.min(1, hp)));
          c.save(); c.shadowColor = css(th.orangeHot, 0.9 * r.power); c.shadowBlur = 22 * th.glowK * r.power; c.fillStyle = g; c.fillRect(0.56, 0.36, w - 1.12, 0.74); c.restore();
          c.fillStyle = css(tone(th.dark, -0.2), 0.9); for (let k = 0; k < 5; k++) c.fillRect(0.6 + k * 0.2, 0.36, 0.05, 0.74);
          r.strip(0.12, 0.1, w - 0.12, 0.16, th.orange, 0.9, 10);
        },
        right: (r, d, h) => {
          seams(r, d, h, th, [0.32, d - 0.32]); hatch(r, 0.62, 0.0, 1.38, 0.42, th, th.orange);
          vents(r, 0.45, 0.62, 1.1, 0.55, 4, th); screen(r, 1.5, 1.05, 0.38, 0.3, th, t, 4);
        },
        top: (r, w, d) => seams(r, w, d, th, [], [d / 2]),
      });
      R.box(x + 0.12, y + 0.12, 1.69, 1.76, 1.76, 0.12, th.roof, { rimK: 0.8 });
      R.cyl(x + 0.55, y + 0.55, 1.81, 0.27, 1.25, th.body2, {
        band: (r, b, tt, rx, ry) => { const c = r.ctx; c.save(); c.shadowColor = css(th.orange, 0.9 * r.power); c.shadowBlur = 10 * th.glowK * r.power; c.fillStyle = css(mixc(th.dark, th.orange, 0.3 + 0.7 * r.power), 0.95); c.fillRect(b[0] - rx, tt[1] + 6, rx * 2, 4); c.restore(); },
        topCol: tone(th.dark, -0.4),
      });
    });
    // smoke (drawn late, above everything nearby)
    R.add(x + y + 4.2, () => {
      const c = R.ctx; R.reset();
      for (let k = 0; k < 7; k++) {
        const life = fract(t / 3.4 + k / 7); const q = R.p(x + 0.55 + life * 0.9, y + 0.55 - life * 0.5, 3.1 + life * 2.6);
        const rad = R.s * (0.22 + life * 0.75); const a = th.smokeA * Math.sin(Math.PI * life) * R.power;
        const g = c.createRadialGradient(q[0], q[1], 0, q[0], q[1], rad); g.addColorStop(0, css(th.smoke, a)); g.addColorStop(1, css(th.smoke, 0));
        c.fillStyle = g; c.beginPath(); c.arc(q[0], q[1], rad, 0, TAU); c.fill();
      }
    });
    R.addLight(() => { R.pool(x + 1, y + 2.6, 1.6, th.orangeHot, 0.32 * heat); R.glow(x + 1, y + 2, 0.8, R.s * 1.8, th.orange, 0.22 * heat); });
  }

  function constructor_(R, m, cvIn) {
    const th = R.th, t = R.t, { x, y } = m;
    const ph = arrivalPhase(t, cvIn);
    const down = ph < 0.18 ? 0 : ph < 0.34 ? easeIn((ph - 0.18) / 0.16) : ph < 0.4 ? 1 : 1 - easeInOut((ph - 0.4) / 0.45);
    const flash = ph > 0.34 && ph < 0.5 ? 1 - (ph - 0.34) / 0.16 : 0;
    R.add(x + y + 2, () => {
      plinth(R, x, y, 2, 2, th);
      R.box(x, y, 0.14, 2, 2, 1.8, th.body, {
        left: (r, w, h) => {
          const c = r.ctx; seams(r, w, h, th, [0.3, w - 0.3]);
          // press bay window
          c.fillStyle = css(tone(th.dark, -0.35)); c.fillRect(0.45, 0.3, w - 0.9, 1.15);
          c.fillStyle = css(th.glass, 0.08); c.fillRect(0.45, 0.3, w - 0.9, 1.15);
          // anvil + head
          c.fillStyle = css(th.steel); c.fillRect(0.6, 0.32, w - 1.2, 0.18);
          const hy = 1.25 - down * 0.62; c.fillStyle = css(tone(th.steel, 0.15)); c.fillRect(0.62, hy, w - 1.24, 0.18);
          c.fillStyle = css(th.steel, 0.8); c.fillRect(w / 2 - 0.06, hy + 0.18, 0.12, 1.45 - hy - 0.18);
          if (flash > 0 && r.power > 0.5) { c.save(); c.shadowColor = css(th.orangeHot, 1); c.shadowBlur = 24 * th.glowK; c.fillStyle = css(th.orangeHot, flash); c.fillRect(0.66, 0.5, w - 1.32, 0.06); c.restore(); }
          r.strip(0.08, 1.58, w - 0.08, 1.64, th.teal, 0.95, 10);
        },
        right: (r, d, h) => { seams(r, d, h, th, [0.3, d - 0.3]); hatch(r, 0.62, 0.0, 1.38, 0.4, th, th.teal); screen(r, 0.5, 0.75, 1.0, 0.55, th, t, 9); r.strip(0.08, 1.58, d - 0.08, 1.64, th.teal, 0.95, 10); },
        top: (r, w, d) => { seams(r, w, d, th, [0.25, w - 0.25], [0.25, d - 0.25]); },
      });
      // piston housing and rod
      R.box(x + 0.55, y + 0.55, 1.94, 0.9, 0.9, 0.5, th.body2, { left: (r, w, h) => vents(r, 0.1, 0.1, w - 0.2, h - 0.2, 3, th), right: (r, d, h) => vents(r, 0.1, 0.1, d - 0.2, h - 0.2, 3, th) });
      R.cyl(x + 1, y + 1, 2.44, 0.13, 0.75 - down * 0.62, th.steel, { topCol: th.orange });
    });
    R.addLight(() => { if (flash > 0 && R.power > 0.5) R.glow(x + 1, y + 2, 0.5, R.s * 2.2, th.orangeHot, 0.6 * flash); R.pool(x + 1, y + 2.5, 1.2, th.teal, 0.12); });
  }

  function foundry(R, m) {
    const th = R.th, t = R.t, { x, y } = m;
    R.add(x + y + 3, () => {
      plinth(R, x, y, 3, 3, th);
      R.box(x, y, 0.14, 3, 3, 2.1, th.body, {
        left: (r, w, h) => {
          seams(r, w, h, th, [0.4, 1.0, 2.0, w - 0.4]);
          for (let k = 0; k < 2; k++) r.strip(1.08 + k * 0.84, 0.35, 1.1 + k * 0.84 + 0.04, 1.75, th.orange, 0.6 + 0.3 * Math.sin(t * 2 + k), 12);
          hatch(r, 1.1, 0.0, 1.9, 0.42, th, th.orange);
        },
        right: (r, d, h) => { seams(r, d, h, th, [0.4, d - 0.4]); vents(r, 0.6, 0.6, 1.8, 1.0, 6, th); screen(r, 0.7, 1.7, 0.9, 0.3, th, t, 21); },
        top: (r, w, d) => seams(r, w, d, th, [0.35, w - 0.35], [0.35, d - 0.35]),
      });
      // corner pillars
      const pil = (px, py) => R.box(px, py, 0.14, 0.34, 0.34, 2.5, th.plinth, { left: (r, w, h) => { r.ctx.fillStyle = css(th.warn, 0.9); r.ctx.fillRect(0, h - 0.2, w, 0.08); }, rimK: 0.9 });
      pil(x - 0.05, y - 0.05); pil(x + 2.71, y - 0.05); pil(x - 0.05, y + 2.71); pil(x + 2.71, y + 2.71);
      // crucible
      R.box(x + 0.5, y + 0.5, 2.24, 2.0, 2.0, 0.32, th.body2, {
        top: (r, w, d) => {
          const c = r.ctx; c.fillStyle = css(tone(th.dark, -0.35)); c.fillRect(0.12, 0.12, w - 0.24, d - 0.24);
          const pw = r.power; c.fillStyle = css([70, 40, 30]); c.fillRect(0.2, 0.2, w - 0.4, d - 0.4);
          const g = c.createRadialGradient(w / 2, d / 2, 0.1, w / 2, d / 2, 0.9); g.addColorStop(0, css(th.orangeHot, pw)); g.addColorStop(1, css(th.orange, 0.85 * pw));
          c.save(); c.shadowColor = css(th.orangeHot, pw); c.shadowBlur = 26 * th.glowK * pw; c.fillStyle = g; c.fillRect(0.2, 0.2, w - 0.4, d - 0.4); c.restore();
          const br = rng(Math.floor(t * 3)); c.fillStyle = css([255, 220, 160], 0.7 * pw);
          for (let k = 0; k < 5; k++) { const bx = 0.35 + br() * 1.3, by = 0.35 + br() * 1.3, rr = 0.04 + 0.06 * fract(t * 3); c.beginPath(); c.arc(bx, by, rr, 0, TAU); c.fill(); }
        },
      });
    });
    R.addLight(() => { R.glow(x + 1.5, y + 1.5, 2.6, R.s * 3.0, th.orangeHot, 0.4 + 0.08 * Math.sin(t * 4.1)); R.pool(x + 1.5, y + 3.4, 1.4, th.orange, 0.22); });
  }

  function assembler(R, m, cvIn) {
    const th = R.th, t = R.t, { x, y } = m;
    const ph = arrivalPhase(t, cvIn);
    // pick (back-left) -> place (front-right) path for the arm tip
    const bx = x + 1.5, by = y + 1.5, bz = 1.92;
    const pick = [x + 0.7, y + 1.0, 1.75], place = [x + 2.3, y + 2.0, 1.75];
    let k, carry;
    if (ph < 0.12) { k = 0; carry = false; } else if (ph < 0.55) { k = easeInOut((ph - 0.12) / 0.43); carry = true; } else if (ph < 0.65) { k = 1; carry = false; } else { k = 1 - easeInOut((ph - 0.65) / 0.35); carry = false; }
    const lift = Math.sin(Math.PI * k) * 0.55;
    const tip = [lerp(pick[0], place[0], k), lerp(pick[1], place[1], k), lerp(pick[2], place[2], k) + lift + (ph < 0.12 || (ph > 0.55 && ph < 0.65) ? 0 : 0.12)];
    const sh = [bx, by, bz + 0.35];
    const dx = tip[0] - sh[0], dy = tip[1] - sh[1], dz = tip[2] - sh[2]; const dh = Math.hypot(dx, dy); const D = Math.hypot(dh, dz);
    const L1 = 1.0, L2 = 0.95; const a1 = Math.atan2(dz, dh) + Math.acos(clamp((L1 * L1 + D * D - L2 * L2) / (2 * L1 * D), -1, 1));
    const el = [sh[0] + (dx / (dh || 1)) * Math.cos(a1) * L1, sh[1] + (dy / (dh || 1)) * Math.cos(a1) * L1, sh[2] + Math.sin(a1) * L1];
    R.add(x + y + 3, () => {
      plinth(R, x, y, 3, 3, th);
      R.box(x, y, 0.14, 3, 3, 1.62, th.body, {
        left: (r, w, h) => {
          seams(r, w, h, th, [0.35, w - 0.35]);
          for (let i = 0; i < 3; i++) {
            const c = r.ctx; const u = 0.75 + i * 0.55; c.fillStyle = css(tone(th.dark, -0.3)); c.fillRect(u, 0.35, 0.3, 0.95);
            const f = clamp(ph * 3 - i, 0, 1); r.strip(u + 0.05, 0.4, u + 0.25, 0.4 + 0.85 * f, th.teal, 0.95, 10);
          }
          r.strip(0.1, 1.44, w - 0.1, 1.5, th.orange, 0.95, 10);
        },
        right: (r, d, h) => { seams(r, d, h, th, [0.35, d - 0.35]); hatch(r, 1.6, 0.0, 2.4, 0.42, th, th.teal); vents(r, 0.5, 0.7, 0.9, 0.6, 4, th); r.strip(0.1, 1.44, d - 0.1, 1.5, th.orange, 0.95, 10); },
        top: (r, w, d) => { const c = r.ctx; c.fillStyle = css(th.deck, 0.75); c.fillRect(0.3, 0.3, w - 0.6, d - 0.6); seams(r, w, d, th, [0.3, w - 0.3], [0.3, d - 0.3]); },
      });
      // work pads
      R.box(pick[0] - 0.3, pick[1] - 0.3, 1.76, 0.6, 0.6, 0.06, th.steel, { rimK: 0.6 });
      R.box(place[0] - 0.3, place[1] - 0.3, 1.76, 0.6, 0.6, 0.06, th.steel, { rimK: 0.6 });
      if (ph > 0.6 || ph < 0.12) drawItem(R, 'plate', pick[0], pick[1], 1.82, 'x', 1);
      if (ph > 0.55 && ph < 0.95) drawItem(R, 'rplate', place[0], place[1], 1.82, 'x', 1 - smooth(0.85, 0.95, ph));
      // turret + arm
      R.cyl(bx, by, 1.76, 0.36, 0.3, th.body2, { topCol: tone(th.body2, 0.2) });
      const P = (q) => R.p(q[0], q[1], q[2]);
      const s = R.s; const armCol = th.orange;
      R.line(P(sh), P(el), css(tone(armCol, -0.35)), s * 0.24, 'round');
      R.line(P(sh), P(el), css(armCol), s * 0.17, 'round');
      R.line(P(el), P(tip), css(tone(armCol, -0.35)), s * 0.19, 'round');
      R.line(P(el), P(tip), css(tone(armCol, 0.1)), s * 0.13, 'round');
      const c = R.ctx; R.reset();
      [sh, el].forEach((q) => { const pp = P(q); c.fillStyle = css(th.dark); c.beginPath(); c.arc(pp[0], pp[1], s * 0.12, 0, TAU); c.fill(); c.fillStyle = css(th.steel); c.beginPath(); c.arc(pp[0], pp[1], s * 0.05, 0, TAU); c.fill(); });
      const tp = P(tip); c.strokeStyle = css(th.steel); c.lineWidth = s * 0.06; c.beginPath(); c.moveTo(tp[0] - s * 0.14, tp[1] + s * 0.16); c.lineTo(tp[0] - s * 0.1, tp[1]); c.lineTo(tp[0] + s * 0.1, tp[1]); c.lineTo(tp[0] + s * 0.14, tp[1] + s * 0.16); c.stroke();
      if (carry) drawItem(R, 'plate', tip[0], tip[1], tip[2] - 0.2, 'x', 1);
      R.glow(tip[0], tip[1], tip[2], s * 0.6, th.teal, 0.35);
    });
    R.addLight(() => { R.pool(x + 1.5, y + 3.4, 1.7, th.teal, 0.16); });
  }

  function elevator(R, m, cvIn) {
    const th = R.th, t = R.t, { x, y } = m; const H = 7.4;
    const period = CYCLE * 4; const e = fract((t * BELT_V + (cvIn.ph || 0) - cvIn.len) / (GAP * 4));
    const rise = e < 0.15 ? 0 : easeInOut(clamp((e - 0.15) / 0.6, 0, 1)); const cz = 1.0 + rise * (H - 1.6);
    const arrive = e > 0.75 ? 1 - (e - 0.75) / 0.25 : 0; void period;
    R.add(x + y + 3, () => {
      plinth(R, x, y, 3, 3, th);
      R.box(x, y, 0.14, 3, 3, 0.75, th.body, {
        left: (r, w, h) => { seams(r, w, h, th, [1, 2]); r.strip(0.1, 0.5, w - 0.1, 0.56, th.teal, 0.95, 10); },
        right: (r, d, h) => { seams(r, d, h, th, [1, 2]); r.strip(0.1, 0.5, d - 0.1, 0.56, th.teal, 0.95, 10); },
      });
      const pil = (px, py, lights) => R.box(px, py, 0.89, 0.3, 0.3, H, th.body2, {
        left: lights ? (r, w, h) => { for (let k = 0; k < 7; k++) { const on = fract(t * 0.9 - k / 7) < 0.2; r.strip(0.08, 0.5 + k, 0.22, 0.62 + k, on ? th.teal : th.dark, on ? 1 : 0.6, 8); } } : null,
        right: lights ? (r, d, h) => { for (let k = 0; k < 7; k++) { const on = fract(t * 0.9 - k / 7) < 0.2; r.strip(0.08, 0.5 + k, 0.22, 0.62 + k, on ? th.teal : th.dark, on ? 1 : 0.6, 8); } } : null,
        rimK: 1,
      });
      pil(x + 0.15, y + 0.15, false);
      // shaft (glass) + capsule
      const sx = x + 0.95, sy = y + 0.95;
      R.box(sx, sy, 0.89, 1.1, 1.1, H, th.shaft, {
        left: (r, w, h) => { const c = r.ctx; c.fillStyle = css(th.glass, th.isDark ? 0.07 : 0.1); c.fillRect(0, 0, w, h); },
        right: (r, d, h) => { const c = r.ctx; c.fillStyle = css(th.glass, th.isDark ? 0.05 : 0.08); c.fillRect(0, 0, d, h); }, rimK: 0.5,
      });
      R.box(sx + 0.15, sy + 0.15, cz, 0.8, 0.8, 0.7, th.orange, {
        left: (r, w, h) => { r.strip(0.1, h * 0.45, w - 0.1, h * 0.55, th.teal, 1, 12); },
        right: (r, d, h) => { r.strip(0.1, h * 0.45, d - 0.1, h * 0.55, th.teal, 1, 12); }, rimK: 1.4,
      });
      R.glow(sx + 0.55, sy + 0.55, cz + 0.35, R.s * 1.5, th.orangeHot, 0.35 + 0.4 * rise * (1 - rise) * 4 * 0.25);
      // glass front panes over the capsule
      const pf = [R.p(sx, sy + 1.1, 0.89), R.p(sx + 1.1, sy + 1.1, 0.89), R.p(sx + 1.1, sy + 1.1, 0.89 + H), R.p(sx, sy + 1.1, 0.89 + H)];
      R.poly(pf, css(th.glass, th.isDark ? 0.06 : 0.12), css(th.rim, th.rimA * 0.6), 1);
      const pr = [R.p(sx + 1.1, sy + 1.1, 0.89), R.p(sx + 1.1, sy, 0.89), R.p(sx + 1.1, sy, 0.89 + H), R.p(sx + 1.1, sy + 1.1, 0.89 + H)];
      R.poly(pr, css(th.glass, th.isDark ? 0.04 : 0.08), css(th.rim, th.rimA * 0.6), 1);
      pil(x + 2.55, y + 0.15, true); pil(x + 0.15, y + 2.55, true); pil(x + 2.55, y + 2.55, true);
      // braces on the two visible faces
      const c = R.ctx; R.reset(); c.strokeStyle = css(th.steel, 0.45); c.lineWidth = Math.max(1, R.s * 0.03);
      for (let k = 0; k < 4; k++) {
        const z0 = 1.2 + k * 1.6, z1 = z0 + 1.6; let a = R.p(x + 0.45, y + 2.7, z0), b = R.p(x + 2.55, y + 2.7, z1);
        c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); a = R.p(x + 2.55, y + 2.7, z0); b = R.p(x + 0.45, y + 2.7, z1); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]);
        a = R.p(x + 2.7, y + 2.55, z0); b = R.p(x + 2.7, y + 0.45, z1); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); a = R.p(x + 2.7, y + 0.45, z0); b = R.p(x + 2.7, y + 2.55, z1); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); c.stroke();
      }
      // crown
      R.box(x - 0.1, y - 0.1, H + 0.89, 3.2, 3.2, 0.35, th.body, {
        left: (r, w, h) => r.strip(0.1, h * 0.4, w - 0.1, h * 0.62, th.teal, 0.95, 14),
        right: (r, d, h) => r.strip(0.1, h * 0.4, d - 0.1, h * 0.62, th.teal, 0.95, 14),
        top: (r, w, d) => { const c2 = r.ctx; c2.strokeStyle = css(th.orange, 0.9); c2.lineWidth = 0.06; c2.strokeRect(0.25, 0.25, w - 0.5, d - 0.5); },
      });
      R.cyl(x + 1.5, y + 1.5, H + 1.24, 0.3, 0.4, th.body2, { topCol: th.teal });
      R.glow(x + 1.5, y + 1.5, H + 1.7, R.s * (1.6 + arrive * 2.5), th.teal, 0.5 + 0.5 * arrive);
    });
    // beacon beam
    R.addLight(() => {
      const c = R.ctx; const b = R.p(x + 1.5, y + 1.5, H + 1.64); R.reset();
      const w = R.s * (0.28 + arrive * 0.4); const g = c.createLinearGradient(0, b[1], 0, b[1] - R.s * 14);
      g.addColorStop(0, css(th.teal, (0.5 + 0.45 * arrive) * th.glowK * R.power)); g.addColorStop(1, css(th.teal, 0));
      c.save(); c.globalCompositeOperation = th.additive ? 'lighter' : 'source-over'; c.fillStyle = g; c.fillRect(b[0] - w / 2, b[1] - R.s * 14, w, R.s * 14); c.restore();
      R.pool(x + 1.5, y + 3.5, 2.0, th.teal, 0.14);
    });
  }

  // ---------------------------------------------------------------- the line
  // Main line along +x at y = 3.5; rods come from the Foundry along +y at x = 17.
  function buildLine() {
    const cv = {
      c1: { axis: 'x', x0: 2.32, len: 3.18, c: 3.5, item: 'ore' },
      c2: { axis: 'x', x0: 7.5, len: 3.0, c: 3.5, item: 'ingot' },
      c3: { axis: 'x', x0: 12.5, len: 3.0, c: 3.5, item: 'plate' },
      c4a: { axis: 'x', x0: 14.2, len: 3.17, c: -1.4, item: 'rod' },
      c4: { axis: 'y', y0: -1.03, len: 3.53, c: 17.0, item: 'rod', noFade: true },
      c5: { axis: 'x', x0: 18.5, len: 4.0, c: 3.5, item: 'pkg' },
    };
    // chain phases so an item leaves a machine D seconds after one arrives (see spec: item flow)
    const D = 0.55 * CYCLE * BELT_V; // blocks
    cv.c1.ph = 0;
    cv.c2.ph = cv.c1.ph - cv.c1.len - D;
    cv.c3.ph = cv.c2.ph - cv.c2.len - D;
    cv.c4.ph = cv.c3.ph - cv.c3.len + cv.c4.len; // rods arrive with plates
    cv.c4a.ph = cv.c4.ph + cv.c4a.len;
    cv.c5.ph = cv.c3.ph - cv.c3.len - D * 1.1;
    const M = {
      miner: { x: 0.3, y: 2.5 }, smelter: { x: 5.5, y: 2.5 }, constructor: { x: 10.5, y: 2.5 },
      foundry: { x: 11.2, y: -2.9 }, assembler: { x: 15.5, y: 2.5 }, elevator: { x: 22.5, y: 2.0 },
    };
    return { cv, M };
  }
  const LINE = buildLine();

  // ---------------------------------------------------------------- environment
  function drawBackground(R, W, H) {
    const c = R.ctx, th = R.th; c.setTransform(R.dpr, 0, 0, R.dpr, 0, 0);
    const g = c.createLinearGradient(0, 0, W * 0.3, H); g.addColorStop(0, th.bg[0]); g.addColorStop(0.55, th.bg[1]); g.addColorStop(1, th.bg[2]);
    c.fillStyle = g; c.fillRect(0, 0, W, H);
  }
  function drawSilhouettes(R) {
    const th = R.th, t = R.t; const rr = rng(77);
    for (let i = 0; i < 16; i++) {
      const x = -10 + i * 3.4 + rr() * 1.5, y = -19 - rr() * 6, w = 1.2 + rr() * 2.2, d = 1.2 + rr() * 1.8, h = 0.8 + rr() * 3.6;
      R.box(x, y, 0, w, d, h, th.silhouette, {
        left: th.isDark ? (r, ww, hh) => { const c = r.ctx; for (let k = 0; k < 3; k++) { if (fract(rr() + t * 0.05 * (k + 1)) < 0.75) { c.fillStyle = css(k % 2 ? th.orange : th.teal, 0.35); c.fillRect(0.3 + k * 0.5, hh * 0.6, 0.12, 0.08); } } } : null,
        rimK: 0.25, ao: false,
      });
    }
  }
  function drawFloor(R, cx, cy, radius) {
    const c = R.ctx, th = R.th;
    // foundation slab under the line
    R.box(-1.2, 1.4, -0.32, 28.2, 5.2, 0.32, th.slab, {
      top: (r, w, d) => { const cc = r.ctx; const lg = cc.createLinearGradient(0, 0, w, 0); lg.addColorStop(0, css(th.rim, 0)); lg.addColorStop(0.55, css(th.rim, th.isDark ? 0.035 : 0.25)); lg.addColorStop(1, css(th.rim, 0)); cc.fillStyle = lg; cc.fillRect(0, 0, w, d); cc.strokeStyle = css(th.seam, th.seamA * 2); cc.lineWidth = 0.03; for (let u = 2; u < w; u += 2) { cc.beginPath(); cc.moveTo(u, 0); cc.lineTo(u, d); cc.stroke(); } for (let v = 2; v < d; v += 2) { cc.beginPath(); cc.moveTo(0, v); cc.lineTo(w, v); cc.stroke(); } },
      left: (r, w, h) => { r.ctx.fillStyle = css(th.slabEdge, 0.85); r.ctx.fillRect(0, h - 0.07, w, 0.05); },
      right: (r, d, h) => { r.ctx.fillStyle = css(th.slabEdge, 0.85); r.ctx.fillRect(0, h - 0.07, d, 0.05); }, rimK: 0.7,
    });
    R.box(10.4, -3.7, -0.32, 7.6, 5.1, 0.32, th.slab, { rimK: 0.7, top: (r, w, d) => { const cc = r.ctx; cc.strokeStyle = css(th.seam, th.seamA * 2); cc.lineWidth = 0.03; for (let u = 2; u < w; u += 2) { cc.beginPath(); cc.moveTo(u, 0); cc.lineTo(u, d); cc.stroke(); } } });
    // infinite grid, faded radially
    R.face('top', cx - radius, cy - radius, 0, 2 * radius, 2 * radius, 0);
    c.save(); c.strokeStyle = css(th.grid, th.gridA); c.lineWidth = 0.025; c.beginPath();
    for (let k = 0; k <= 2 * radius; k++) { c.moveTo(k, 0); c.lineTo(k, 2 * radius); c.moveTo(0, k); c.lineTo(2 * radius, k); }
    c.stroke(); c.restore();
  }
  function drawShadows(R, items) {
    const c = R.ctx, th = R.th; c.save(); c.filter = `blur(${Math.round(R.s * 0.35)}px)`;
    for (const [x, y, w, d, h] of items) {
      R.face('top', x, y, 0, w, d, 0); c.fillStyle = css(th.shadow, th.shadowA);
      const k = Math.min(1.6, h * 0.22); c.beginPath(); c.moveTo(0, 0); c.lineTo(w, 0); c.lineTo(w + k, d + k * 0.4); c.lineTo(k * 0.2, d + k); c.closePath(); c.fill();
    }
    c.restore();
  }
  function drawDust(R, W, H) {
    const c = R.ctx, th = R.th, t = R.t; if (!th.isDark) return; c.setTransform(R.dpr, 0, 0, R.dpr, 0, 0);
    const rr = rng(5); c.save(); c.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 60; i++) {
      const x0 = rr() * W, y0 = rr() * H, sp = 6 + rr() * 14, ph = rr() * TAU, sz = 0.6 + rr() * 1.4;
      const x = (x0 + t * sp) % W, y = (y0 - t * sp * 0.4 + H) % H; const a = 0.1 + 0.12 * Math.sin(t * 0.8 + ph);
      c.fillStyle = css(i % 3 ? [200, 230, 235] : [255, 170, 110], Math.max(0, a)); c.beginPath(); c.arc(x, y, sz, 0, TAU); c.fill();
    }
    c.restore();
  }
  function drawGrade(R, W, H) {
    const c = R.ctx, th = R.th; c.setTransform(R.dpr, 0, 0, R.dpr, 0, 0);
    let g = c.createRadialGradient(W * 0.55, H * 0.5, H * 0.25, W * 0.55, H * 0.5, Math.max(W, H) * 0.8);
    g.addColorStop(0, css(th.fog, 0)); g.addColorStop(1, css(th.isDark ? [4, 7, 9] : th.bg[2], th.vignette));
    c.fillStyle = g; c.fillRect(0, 0, W, H);
    if (th.isDark) {
      g = c.createLinearGradient(0, 0, W, H); g.addColorStop(0, 'rgba(47,209,193,0.05)'); g.addColorStop(0.6, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(224,112,60,0.07)');
      c.save(); c.globalCompositeOperation = 'lighter'; c.fillStyle = g; c.fillRect(0, 0, W, H); c.restore();
    }
  }

  // ---------------------------------------------------------------- scene
  // cam: {cx, cy, cz, scale(px per block relative to H), fx, fy (screen anchor 0..1)}
  function renderScene(ctx, W, H, dpr, th, t, cam) {
    const R = new Iso(ctx, th); R.t = t; R.dpr = dpr; R.base = new DOMMatrix([dpr, 0, 0, dpr, 0, 0]);
    const lights = []; R.addLight = (fn) => { const pw = R.curPower; lights.push(() => { R.power = pw; fn(); R.power = 1; }); };
    const tl = cam.timeline ? cam.timeline(t) : null;
    const use = (name) => { R.t = tl ? tl.mt[name] : t; R.curPower = tl ? tl.pw[name] : 1; };
    const drift = cam.drift === false ? 0 : 1;
    R.s = H * cam.scale * (1 + 0.012 * Math.sin(t * 0.21) * drift);
    const anchor = [W * cam.fx + Math.sin(t * 0.13) * W * 0.008 * drift, H * cam.fy + Math.cos(t * 0.17) * H * 0.006 * drift];
    R.ox = 0; R.oy = 0; const q = R.p(cam.cx, cam.cy, cam.cz || 0); R.ox = anchor[0] - q[0]; R.oy = anchor[1] - q[1];
    drawBackground(R, W, H);
    if (cam.silhouettes !== false) drawSilhouettes(R);
    drawFloor(R, 11, 2, 22);
    const { cv, M } = LINE;
    drawShadows(R, [
      [M.miner.x, M.miner.y, 2, 2, 2.9], [M.smelter.x, M.smelter.y, 2, 2, 3.0], [M.constructor.x, M.constructor.y, 2, 2, 3.0],
      [M.foundry.x, M.foundry.y, 3, 3, 2.6], [M.assembler.x, M.assembler.y, 3, 3, 2.2], [M.elevator.x, M.elevator.y, 3, 3, 8.6],
    ]);
    R.t = tl ? tl.bt : t; R.curPower = 1;
    Object.values(cv).forEach((c) => { for (let i = 0; i < Math.ceil(c.len); i++) beltSegment(R, c, i); beltItems(R, c); });
    use('miner'); miner(R, M.miner); use('smelter'); smelter(R, M.smelter, cv.c1); use('constructor'); constructor_(R, M.constructor, cv.c2);
    use('foundry'); foundry(R, M.foundry); use('assembler'); assembler(R, M.assembler, cv.c3); use('elevator'); elevator(R, M.elevator, cv.c5);
    R.t = t; R.curPower = 1;
    if (tl) { // power-on flashes and the final launch
      const tops = { miner: [M.miner.x + 1, M.miner.y + 1, 3.0], smelter: [M.smelter.x + 1, M.smelter.y + 1, 2.0], constructor: [M.constructor.x + 1, M.constructor.y + 1, 2.4], foundry: [M.foundry.x + 1.5, M.foundry.y + 1.5, 2.6], assembler: [M.assembler.x + 1.5, M.assembler.y + 1.5, 2.0], elevator: [M.elevator.x + 1.5, M.elevator.y + 1.5, 8.6] };
      Object.keys(tops).forEach((k) => { const f = tl.flash[k] || 0; if (f > 0.01) R.addLight(() => { const q = tops[k]; R.glow(q[0], q[1], q[2], R.s * (1.5 + 2.5 * f), th.teal, 0.9 * f); R.pool(q[0], q[1] + 1.5, 2.2, th.teal, 0.35 * f); }); });
      if (tl.launch > 0) R.addLight(() => { const q = tops.elevator; const c = R.ctx; const b = R.p(q[0], q[1], q[2] + 1); R.reset(); const w = R.s * (0.6 + 2.2 * tl.launch); const g = c.createLinearGradient(0, b[1], 0, 0); g.addColorStop(0, css(th.teal, 0.85 * tl.launch * th.glowK)); g.addColorStop(1, css(th.teal, 0)); c.save(); c.globalCompositeOperation = th.additive ? 'lighter' : 'source-over'; c.fillStyle = g; c.fillRect(b[0] - w / 2, 0, w, b[1]); c.restore(); R.glow(q[0], q[1], q[2] + 1, R.s * 5 * tl.launch, th.teal, 0.8 * tl.launch); });
    }
    R.flush();
    lights.forEach((fn) => fn());
    drawDust(R, W, H);
    drawGrade(R, W, H);
    return R;
  }

  // ---------------------------------------------------------------- emblem (crafting-table cube)
  function drawEmblem(ctx, size, th, t) {
    const R = new Iso(ctx, th); R.base = new DOMMatrix([1, 0, 0, 1, 0, 0]); R.s = size * 0.5; R.t = t || 0;
    const q = R.p(0.5, 0.5, 0.5); R.ox = size / 2 - q[0]; R.oy = size / 2 - q[1] + size * 0.02;
    const dark = th.isDark ? '#1e2a33' : '#2a3640';
    R.box(0, 0, 0, 1, 1, 1, dark, {
      top: (r) => {
        const c = r.ctx; c.fillStyle = css('#e0703c'); c.fillRect(0, 0, 1, 1);
        c.fillStyle = css('#8f3b14'); const g = 0.06, cell = (1 - 4 * g) / 3;
        for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) { c.fillStyle = css((i + j) % 2 ? '#a8461a' : '#c25a24'); c.fillRect(g + i * (cell + g), g + j * (cell + g), cell, cell); }
        c.fillStyle = css('#ffd2b0'); c.fillRect(g + 1 * (cell + g), g + 1 * (cell + g), cell, cell);
      },
      left: (r) => { const c = r.ctx; c.fillStyle = css('#e0703c'); c.fillRect(0, 0.84, 1, 0.16); c.fillStyle = css('#2fd1c1', 0.9); c.fillRect(0.18, 0.3, 0.64, 0.08); },
      right: (r) => { const c = r.ctx; c.fillStyle = css('#c25a24'); c.fillRect(0, 0.84, 1, 0.16); c.fillStyle = css(th.isDark ? '#2a3a45' : '#3d4f5c'); c.fillRect(0.2, 0.25, 0.6, 0.4); },
      rimK: 2,
    });
  }

  window.ARF = { mixc, THEMES, renderScene, drawEmblem, clamp, lerp, smooth, easeInOut, easeOut, fract, rng, css, tone, CYCLE };
})();
