/*
 * Arffornia screen previews: loading screens and title screens built on engine.js.
 * URL parameters: ?lang=en|fr  &t=<seconds> (freeze)  &keys=1 (show translation keys)
 * Recording: window.renderFrame(t) draws one deterministic frame; window.READY resolves when fonts are loaded.
 */
(function () {
  'use strict';
  const A = window.ARF;
  const qs = new URLSearchParams(location.search);
  const LANG = qs.get('lang') === 'fr' ? 'fr' : 'en';
  const SHOW_KEYS = qs.get('keys') === '1';
  const VIEW = window.VIEW;

  // ------------------------------------------------------------ i18n (keys mirror the spec's lang files)
  const NB = ' '; // narrow no-break space before French ":" "!" "?"
  const I18N = {
    'gui.arffornia.brand.tagline': { en: 'Modded Minecraft · NeoForge 1.21.1', fr: 'Minecraft moddé · NeoForge 1.21.1' },
    'gui.arffornia.loading.stage.boot': { en: 'Starting Java & NeoForge', fr: 'Démarrage de Java et NeoForge' },
    'gui.arffornia.loading.stage.discovery': { en: 'Discovering mods', fr: 'Découverte des mods' },
    'gui.arffornia.loading.stage.mods': { en: 'Loading mods', fr: 'Chargement des mods' },
    'gui.arffornia.loading.stage.registries': { en: 'Registering content', fr: 'Enregistrement du contenu' },
    'gui.arffornia.loading.stage.resources': { en: 'Loading textures & models', fr: 'Chargement des textures et modèles' },
    'gui.arffornia.loading.stage.ready': { en: 'Ready', fr: 'Prêt' },
    'gui.arffornia.loading.detail.found': { en: '%s mods found', fr: '%s mods détectés' },
    'gui.arffornia.loading.detail.registries': { en: 'Blocks, items, recipes', fr: 'Blocs, objets, recettes' },
    'gui.arffornia.loading.detail.atlas': { en: 'Stitching atlas %s / 7', fr: 'Assemblage de l’atlas %s / 7' },
    'gui.arffornia.loading.detail.ready': { en: 'Welcome to the factory', fr: 'Bienvenue à l’usine' },
    'gui.arffornia.loading.tip.label': { en: 'Tip', fr: 'Astuce' },
    'gui.arffornia.loading.tip.1': { en: 'Each Space Elevator phase unlocks a new tier.', fr: 'Chaque phase de l’ascenseur spatial débloque un nouveau palier.' },
    'gui.arffornia.loading.tip.2': { en: 'Machines need power: grow your power plant before the next tier.', fr: `Les machines consomment de l’énergie${NB}: agrandissez votre centrale avant le palier suivant.` },
    'gui.arffornia.loading.tip.3': { en: 'Press G to open the progression graph.', fr: 'Appuyez sur G pour ouvrir l’arbre de progression.' },
    'gui.arffornia.loading.memory': { en: 'Memory', fr: 'Mémoire' },
    'gui.arffornia.loading.pip.java': { en: 'Java', fr: 'Java' },
    'gui.arffornia.loading.pip.mods': { en: 'Mods', fr: 'Mods' },
    'gui.arffornia.loading.pip.content': { en: 'Content', fr: 'Contenu' },
    'gui.arffornia.loading.pip.resources': { en: 'Resources', fr: 'Ressources' },
    'gui.arffornia.loading.pip.ready': { en: 'Ready', fr: 'Prêt' },
    'gui.arffornia.title.tagline': { en: 'Progression that keeps every mod worth playing.', fr: 'Une progression qui donne un rôle à chaque mod.' },
    'gui.arffornia.title.play': { en: 'Play on Arffornia', fr: 'Jouer sur Arffornia' },
    'gui.arffornia.title.play.short': { en: 'Play', fr: 'Jouer' },
    'gui.arffornia.title.server.online': { en: 'Online · %s / 200 players · %s ms', fr: 'En ligne · %s / 200 joueurs · %s ms' },
    'menu.singleplayer': { en: 'Singleplayer', fr: 'Solo' },
    'menu.multiplayer': { en: 'Multiplayer', fr: 'Multijoueur' },
    'fml.menu.mods': { en: 'Mods', fr: 'Mods' },
    'menu.options': { en: 'Options', fr: 'Options' },
    'menu.quit': { en: 'Quit Game', fr: 'Quitter le jeu' },
    'gui.arffornia.title.progress': { en: 'Your progress', fr: 'Votre progression' },
    'gui.arffornia.title.tier': { en: 'Tier %s · %s', fr: 'Palier %s · %s' },
    'gui.arffornia.tier.2': { en: 'Part Assembly', fr: 'Assemblage de pièces' },
    'gui.arffornia.title.next': { en: 'Next delivery: %s Reinforced Plates', fr: 'Prochaine livraison${NB}: %s plaques renforcées' },
    'gui.arffornia.title.news': { en: 'News', fr: 'Actualités' },
    'gui.arffornia.title.news.date': { en: 'Oct 28', fr: '28 oct.' },
    'gui.arffornia.title.news.headline': { en: 'The Foundry arrives in Tier 3', fr: 'La Fonderie arrive au palier 3' },
    'gui.arffornia.title.news.body': { en: 'First multiblock: steel, invar and bronze alloys.', fr: `Premier multibloc${NB}: alliages d’acier, d’invar et de bronze.` },
    'gui.arffornia.title.version': { en: 'Arffornia 1.0.25 · Minecraft 1.21.1 · NeoForge 21.1.172 · 331 mods', fr: 'Arffornia 1.0.25 · Minecraft 1.21.1 · NeoForge 21.1.172 · 331 mods' },
    'gui.arffornia.loading.dyk.label': { en: 'Did you know?', fr: `Le saviez-vous${NB}?` },
    'gui.arffornia.machine.miner': { en: 'Miner', fr: 'Foreuse' },
    'gui.arffornia.machine.smelter': { en: 'Smelter', fr: 'Fonderie simple' },
    'gui.arffornia.machine.constructor': { en: 'Constructor', fr: 'Constructeur' },
    'gui.arffornia.machine.foundry': { en: 'Foundry', fr: 'Fonderie' },
    'gui.arffornia.machine.elevator': { en: 'Space Elevator', fr: 'Ascenseur spatial' },
    'gui.arffornia.loading.dyk.miner': { en: 'A miner on an ore node never runs dry. Build the line around it, not the other way round.', fr: 'Une foreuse sur un filon ne s’épuise jamais. Construisez la ligne autour d’elle.' },
    'gui.arffornia.loading.dyk.smelter': { en: 'Smelters stop when their output is full. A belt out is worth more than a faster smelter.', fr: 'Une fonderie s’arrête quand sa sortie est pleine. Un convoyeur vaut mieux qu’une fonderie plus rapide.' },
    'gui.arffornia.loading.dyk.constructor': { en: 'Constructors press ingots into plates and rods, the parts every tier asks for.', fr: 'Le constructeur presse les lingots en plaques et en tiges, les pièces de chaque palier.' },
    'gui.arffornia.loading.dyk.foundry': { en: 'The Foundry is your first multiblock: steel, invar and bronze, from tier 3.', fr: `La Fonderie est votre premier multibloc${NB}: acier, invar et bronze, dès le palier 3.` },
    'gui.arffornia.loading.dyk.elevator': { en: 'Each Space Elevator delivery unlocks the next tier. Press G to see what it needs.', fr: 'Chaque livraison à l’ascenseur spatial débloque le palier suivant. Appuyez sur G pour voir ce qu’il faut.' },
    'title.credits': { en: 'Copyright Mojang AB. Do not distribute!', fr: 'Copyright Mojang AB. Do not distribute!' },
  };
  I18N['gui.arffornia.title.next'].fr = `Prochaine livraison${NB}: %s plaques renforcées`;
  function tr(key, ...args) {
    if (SHOW_KEYS) return key;
    const e = I18N[key]; let s = e ? e[LANG] : key; args.forEach((a) => { s = s.replace('%s', a); }); return s;
  }

  const MODS = ['Applied Energistics 2', 'Create', 'Mekanism', 'Immersive Engineering', 'Powah', 'XNet', 'Extreme Reactors', 'Refined Storage', 'Mystical Agriculture', 'Ender IO', 'Oritech', 'Ars Nouveau', 'Sophisticated Storage', 'Farmer’s Delight', 'Hostile Neural Networks', 'FramedBlocks', 'Just Enough Items (JEI)', 'Modular Routers', 'Project Red', 'CC: Tweaked', 'RFTools Base', 'Iron Furnaces', 'Industrial Foregoing', 'PneumaticCraft', 'Arffornia'];
  const TOTAL_MODS = 331;

  // ------------------------------------------------------------ loading timeline (a 14 s compressed boot)
  const STAGES = [
    { key: 'boot', t0: 0.0, t1: 1.4, p0: 0, p1: 4, pip: 0 },
    { key: 'discovery', t0: 1.4, t1: 2.8, p0: 4, p1: 12, pip: 1 },
    { key: 'mods', t0: 2.8, t1: 7.6, p0: 12, p1: 56, pip: 1 },
    { key: 'registries', t0: 7.6, t1: 9.0, p0: 56, p1: 68, pip: 2 },
    { key: 'resources', t0: 9.0, t1: 12.6, p0: 68, p1: 99, pip: 3 },
    { key: 'ready', t0: 12.6, t1: 1e9, p0: 100, p1: 100, pip: 4 },
  ];
  const pctAt = (t) => { const st = STAGES.find((x) => t < x.t1) || STAGES[STAGES.length - 1]; return st.key === 'ready' ? 100 : A.lerp(st.p0, st.p1, A.clamp((t - st.t0) / (st.t1 - st.t0), 0, 1)); };
  const timeAt = (p) => { for (const st of STAGES) { if (p <= st.p1 && st.p1 > st.p0) return st.t0 + ((p - st.p0) / (st.p1 - st.p0)) * (st.t1 - st.t0); } return 12.6; };
  // the factory powers on machine by machine as loading progresses; the elevator launches at 100 %
  const POWER_AT = { miner: 1, smelter: 11, constructor: 26, foundry: 42, assembler: 58, elevator: 76 };
  const T_ON = {}; Object.keys(POWER_AT).forEach((k) => { T_ON[k] = timeAt(POWER_AT[k]); });
  function loadingTimeline(t) {
    const pct = pctAt(t); const t0 = T_ON.miner; const bt = Math.max(0, t - t0) + 0.0;
    const mt = {}, pw = {}, flash = {};
    Object.keys(POWER_AT).forEach((k) => {
      const on = T_ON[k]; mt[k] = t >= on ? bt : Math.max(0, on - t0); pw[k] = A.smooth(on - 0.05, on + 0.45, t);
      flash[k] = t >= on ? Math.exp(-(t - on) * 3.2) : 0;
    });
    const launch = t >= 12.6 ? Math.sin(Math.PI * A.clamp((t - 12.6) / 1.6, 0, 1)) : 0; void pct;
    return { bt, mt, pw, flash, launch };
  }
  function loadState(t) {
    const st = STAGES.find((s) => t < s.t1) || STAGES[STAGES.length - 1];
    const k = A.clamp((t - st.t0) / (st.t1 - st.t0), 0, 1);
    const pct = st.key === 'ready' ? 100 : A.lerp(st.p0, st.p1, k);
    let detail = '';
    if (st.key === 'boot') detail = 'Java 21.0.8 · ModLauncher 11';
    else if (st.key === 'discovery') detail = tr('gui.arffornia.loading.detail.found', Math.round(TOTAL_MODS * A.easeOut(k)));
    else if (st.key === 'mods') { const n = Math.max(1, Math.round(TOTAL_MODS * k)); detail = `${n} / ${TOTAL_MODS} · ${MODS[Math.floor(t * 4.2) % MODS.length]}`; }
    else if (st.key === 'registries') detail = tr('gui.arffornia.loading.detail.registries');
    else if (st.key === 'resources') detail = tr('gui.arffornia.loading.detail.atlas', Math.min(7, 1 + Math.floor(k * 7)));
    else detail = tr('gui.arffornia.loading.detail.ready');
    const phase = t < 7.6 ? 'early window (FML provider)' : 'loading overlay (resource reload)';
    return { st, k, pct, detail, phase };
  }

  // ------------------------------------------------------------ DOM helpers
  const $ = (sel) => document.querySelector(sel);
  function el(tag, cls, html) { const e = document.createElement(tag); if (cls) e.className = cls; if (html !== undefined) e.innerHTML = html; return e; }
  // round 4b (Brian): the brand logo is the crafting table (profile/brand/crafting-table.png, the same file
  // as Crafting_Table.png on the website and the launcher), not the drawn iso cube (A.drawEmblem, kept unused)
  const LOGO = new URL('../../../../profile/brand/crafting-table.png', document.baseURI).href;
  function emblem(size, th) {
    const im = el('img', 'emblem'); im.src = LOGO; im.alt = ''; im.width = size; im.height = size;
    im.style.width = size + 'px'; im.style.height = size + 'px'; im.style.filter = 'drop-shadow(0 3px 8px rgba(0,0,0,.45))';
    return im;
  }
  const diamond = '<i class="dia"></i>';

  // ------------------------------------------------------------ views
  const V = {};

  V['loading-a'] = {
    theme: 'night', cam: { cx: 12.6, cy: 2.2, cz: 2.4, scale: 1 / 22, fx: 0.53, fy: 0.405, /* round 4: 25 px lower, the miner's roof cleared the stage tracker */ timeline: (t) => loadingTimeline(t) },
    build(root, th) {
      root.innerHTML = `
        <div class="la-top">
          <div class="pips"></div>
          <div class="tip"><b></b><span></span></div>
        </div>
        <div class="la-bottom">
          <div class="brand"><div class="em"></div><div class="stack"><div class="word">ARFFORNIA</div><div class="sub"></div></div></div>
          <div class="status">
            <div class="row"><div><div class="stage"></div><div class="detail"></div></div><div class="pct"><span></span><small>%</small></div></div>
            <div class="bar"><i class="fill"></i><i class="head"></i></div>
            <div class="meta"><span class="mem"></span><span>Minecraft 1.21.1 · NeoForge 21.1.172</span><span class="moj">Mojang Studios</span></div>
          </div>
        </div>
        <div class="dyk"><canvas></canvas><span class="name"></span><div class="txt"><div class="lab"><span></span><span class="dots"></span></div><p></p></div></div>
        <div class="phase"></div>`;
      $('.em').appendChild(emblem(58, th));
      DYK.forEach(() => { const i = el('i'); i.appendChild(el('b')); $('.dyk .dots').appendChild(i); }); $('.sub').textContent = tr('gui.arffornia.brand.tagline');
      const pips = $('.pips'); ['java', 'mods', 'content', 'resources', 'ready'].forEach((k, i) => { if (i) pips.appendChild(el('i', 'link')); const p = el('div', 'pip'); p.innerHTML = `${diamond}<span>${tr('gui.arffornia.loading.pip.' + k)}</span>`; pips.appendChild(p); });
    },
    frame(t) { hudLoading(t); hudDyk(t, th); },
  };

  // round 4: "Did you know?" card. Each tip comes with a close-up of the machine it talks about,
  // drawn by the same engine at its own clock, so the card never repeats the big scene's framing.
  const DYK = [
    { m: 'miner', at: [0.3, 2.5, 2], z: 1.3, k: 'miner' },
    { m: 'smelter', at: [5.5, 2.5, 2], z: 1.2, k: 'smelter' },
    { m: 'constructor', at: [10.5, 2.5, 2], z: 1.2, k: 'constructor' },
    { m: 'foundry', at: [11.2, -2.9, 3], z: 1.2, k: 'foundry' },
    { m: 'elevator', at: [22.5, 2.0, 3], z: 4.0, k: 'elevator' },
  ];
  const DYK_PERIOD = Number(qs.get('dyk') || 4.6); // in game: 8 s per tip (spec 007 round 4); shortened for the 14 s clip
  function hudDyk(t, th) {
    const card = $('.dyk'); if (!card) return;
    const n = Math.floor(t / DYK_PERIOD) % DYK.length, k = A.fract(t / DYK_PERIOD), d = DYK[n];
    const a = A.smooth(0, 0.07, k) * (1 - A.smooth(0.94, 1, k));
    const cv = card.querySelector('canvas'); const dpr = window.devicePixelRatio || 1; const w = 320, h = 136;
    if (cv.width !== w * dpr) { cv.width = w * dpr; cv.height = h * dpr; }
    const ctx = cv.getContext('2d');
    const tall = d.m === 'elevator';
    A.renderScene(ctx, w, h, dpr, th, 20 + t, { cx: d.at[0] + d.at[2] / 2, cy: d.at[1] + d.at[2] / 2, cz: d.z, scale: (tall ? 1 / 10.5 : 1 / 4.1) * (1 + 0.05 * k), fx: 0.5, fy: tall ? 0.52 : 0.7, silhouettes: false, drift: false, only: d.m });
    // review: a vignette so the machine reads as a close-up, not a crop of the big scene
    { const g = ctx.createRadialGradient(cv.width / 2, cv.height * 0.55, cv.height * 0.25, cv.width / 2, cv.height * 0.55, cv.width * 0.62); g.addColorStop(0, 'rgba(10,16,20,0)'); g.addColorStop(1, 'rgba(10,16,20,0.85)'); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = g; ctx.fillRect(0, 0, cv.width, cv.height); }
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = `rgba(10,16,20,${(1 - a).toFixed(3)})`; ctx.fillRect(0, 0, cv.width, cv.height);
    card.querySelector('.name').textContent = tr('gui.arffornia.machine.' + d.k);
    card.querySelector('.lab span').textContent = tr('gui.arffornia.loading.dyk.label');
    const p = card.querySelector('p'); p.textContent = tr('gui.arffornia.loading.dyk.' + d.k); p.style.opacity = a.toFixed(3);
    card.querySelectorAll('.dots i').forEach((dot, i) => { dot.classList.toggle('done', i < n); dot.classList.toggle('on', i === n); dot.querySelector('b').style.width = (i === n ? k * 100 : 0) + '%'; });
    card.style.opacity = A.smooth(0.3, 0.9, t).toFixed(3);
  }

  V['loading-b'] = {
    theme: 'maquette', cam: { cx: 12.6, cy: 2.0, cz: 2.4, scale: 1 / 22.5, fx: 0.5, fy: 0.41, timeline: (t) => loadingTimeline(t) },
    build(root, th) {
      root.innerHTML = `
        <div class="lb-tilt top"></div><div class="lb-tilt bottom"></div>
        <div class="lb-brand"><div class="em"></div><div class="word">ARFFORNIA</div><div class="sub"></div></div>
        <div class="lb-card">
          <div class="pips"></div>
          <div class="row"><div><div class="stage"></div><div class="detail"></div></div><div class="pct"><span></span><small>%</small></div></div>
          <div class="bar"><i class="fill"></i><i class="head"></i></div>
          <div class="tip"><b></b><span></span></div>
        </div>
        <div class="lb-meta"><span class="mem"></span><span>Minecraft 1.21.1 · NeoForge 21.1.172 · Mojang Studios</span></div>
        <div class="phase"></div>`;
      $('.em').appendChild(emblem(52, th)); $('.sub').textContent = tr('gui.arffornia.brand.tagline');
      const pips = $('.pips'); ['java', 'mods', 'content', 'resources', 'ready'].forEach((k, i) => { if (i) pips.appendChild(el('i', 'link')); const p = el('div', 'pip'); p.innerHTML = `${diamond}<span>${tr('gui.arffornia.loading.pip.' + k)}</span>`; pips.appendChild(p); });
    },
    frame(t) { hudLoading(t); },
  };

  function hudLoading(t) {
    const s = loadState(t);
    $('.stage').textContent = tr('gui.arffornia.loading.stage.' + s.st.key);
    $('.detail').textContent = s.detail;
    $('.pct span').textContent = Math.floor(s.pct);
    $('.bar .fill').style.width = s.pct + '%';
    $('.bar .fill').style.backgroundPosition = `${(t * 34) % 34}px 0`;
    $('.bar .head').style.left = s.pct + '%';
    $('.bar .head').style.opacity = s.st.key === 'ready' ? 0 : 1;
    const tipN = 1 + (Math.floor(t / 5) % 3); const tipK = A.fract(t / 5); const tipA = A.smooth(0, 0.08, tipK) * (1 - A.smooth(0.92, 1, tipK));
    $('.tip b').textContent = tr('gui.arffornia.loading.tip.label').toUpperCase(); $('.tip span').textContent = tr('gui.arffornia.loading.tip.' + tipN);
    $('.tip').style.opacity = tipA.toFixed(3); $('.tip').style.transform = `translateY(${(1 - tipA) * 6}px)`;
    const mem = (1.1 + Math.min(1, t / 12) * 3.4 + 0.15 * Math.sin(t * 1.7)).toFixed(1);
    $('.mem').textContent = `${tr('gui.arffornia.loading.memory')} ${mem} / 8.0 GB`;
    document.querySelectorAll('.pip').forEach((p, i) => {
      p.classList.toggle('done', i < s.st.pip || s.st.key === 'ready'); p.classList.toggle('active', i === s.st.pip && s.st.key !== 'ready');
      p.style.setProperty('--pulse', (0.55 + 0.45 * Math.sin(t * 5)).toFixed(3));
    });
    document.querySelectorAll('.pips .link').forEach((l, i) => l.classList.toggle('done', i < s.st.pip || s.st.key === 'ready'));
    const ph = $('.phase'); if (ph) ph.textContent = DEBUG ? s.phase : '';
    // end of the boot: fade the world a touch brighter
    document.body.style.setProperty('--ready', A.smooth(12.6, 13.4, t).toFixed(3));
    document.body.classList.toggle('ready', s.st.key === 'ready');
  }

  // ------------------------------------------------------------ title screens
  const MENU = ['menu.singleplayer', 'menu.multiplayer', 'fml.menu.mods', 'menu.options', 'menu.quit'];
  // scripted cursor path: [time, x, y] in 0..1 screen units
  const CURSOR_A = [[0, 0.62, 0.78], [1.2, 0.62, 0.78], [2.6, 0.2, 0.37], [5.2, 0.2, 0.37], [6.4, 0.15, 0.54], [7.6, 0.15, 0.54], [8.6, 0.16, 0.608], [10.5, 0.16, 0.608]];
  const CURSOR_B = [[0, 0.75, 0.55], [1.2, 0.75, 0.55], [2.6, 0.5, 0.86], [5.2, 0.5, 0.86], [6.6, 0.645, 0.86], [8.0, 0.645, 0.86], [9.2, 0.355, 0.86], [10.5, 0.355, 0.86]];
  function cursorAt(path, t) {
    const T = t % 10.5; for (let i = 1; i < path.length; i++) { if (T <= path[i][0]) { const a = path[i - 1], b = path[i]; const k = A.easeInOut((T - a[0]) / (b[0] - a[0] || 1)); return [A.lerp(a[1], b[1], k), A.lerp(a[2], b[2], k)]; } }
    const l = path[path.length - 1]; return [l[1], l[2]];
  }
  function hoverUpdate(t, path) {
    const [cx, cy] = cursorAt(path, t); const W = innerWidth, H = innerHeight; const px = cx * W, py = cy * H;
    const cur = $('.cursor'); cur.style.transform = `translate(${px}px, ${py}px)`;
    document.querySelectorAll('[data-hover]').forEach((b) => {
      const r = b.getBoundingClientRect(); const inside = px >= r.left && px <= r.right && py >= r.top && py <= r.bottom;
      const prev = parseFloat(b.dataset.h || '0'); // deterministic: hover amount from distance to the time the cursor entered is not tracked; use a smooth step on inside
      void prev; b.style.setProperty('--h', inside ? '1' : '0'); b.classList.toggle('hover', inside);
    });
  }

  V['title-a'] = {
    theme: 'night', cam: { cx: 12.8, cy: 2.2, cz: 2.4, scale: 1 / 20, fx: 0.655, fy: 0.45 },
    build(root, th) {
      root.innerHTML = `
        <aside class="ta-panel">
          <div class="brand"><div class="em"></div><div><div class="word">ARFFORNIA</div><div class="sub"></div></div></div>
          <p class="tagline"></p>
          <button class="play" data-hover><span class="ico">▶</span><span class="lbl"></span><span class="srv"><i></i><em></em></span></button>
          <nav class="menu"></nav>
          <div class="foot"></div>
        </aside>
        <section class="ta-card prog"><div class="eyebrow"></div><div class="tier"></div><div class="graph"></div><div class="pbar"><i></i></div><div class="next"></div></section>
        <section class="ta-card news"><div class="eyebrow"><span></span><time></time></div><h3></h3><p></p></section>
        <div class="credits"></div>
        <div class="cursor"></div>`;
      $('.em').appendChild(emblem(54, th)); $('.sub').textContent = tr('gui.arffornia.brand.tagline'); $('.tagline').textContent = tr('gui.arffornia.title.tagline');
      $('.play .lbl').textContent = tr('gui.arffornia.title.play');
      const m = $('.menu'); MENU.forEach((k) => { const b = el('button', 'item'); b.dataset.hover = ''; b.innerHTML = `<i class="tick"></i><span>${tr(k)}</span><b>›</b>`; m.appendChild(b); });
      $('.foot').textContent = tr('gui.arffornia.title.version'); $('.credits').textContent = tr('title.credits');
      $('.prog .eyebrow').textContent = tr('gui.arffornia.title.progress'); $('.prog .tier').textContent = tr('gui.arffornia.title.tier', 2, tr('gui.arffornia.tier.2'));
      const g = $('.prog .graph'); for (let i = 0; i < 10; i++) { if (i) g.appendChild(el('i', 'link' + (i <= 2 ? ' done' : ''))); g.appendChild(el('b', i < 2 ? 'done' : i === 2 ? 'active' : '')); }
      $('.news .eyebrow span').textContent = tr('gui.arffornia.title.news'); $('.news time').textContent = tr('gui.arffornia.title.news.date');
      $('.news h3').textContent = tr('gui.arffornia.title.news.headline'); $('.news p').textContent = tr('gui.arffornia.title.news.body');
    },
    frame(t) {
      const players = 42 + Math.round(2 * Math.sin(t * 0.3)); $('.srv em').textContent = tr('gui.arffornia.title.server.online', players, 18);
      $('.srv i').style.opacity = (0.55 + 0.45 * Math.sin(t * 3)).toFixed(2);
      const p = 64 + 3 * A.smooth(3, 9, t); $('.pbar i').style.width = p + '%'; $('.next').textContent = tr('gui.arffornia.title.next', 200 - Math.round(p * 2));
      document.querySelectorAll('.graph b.active').forEach((b) => b.style.setProperty('--pulse', (0.55 + 0.45 * Math.sin(t * 4)).toFixed(2)));
      hoverUpdate(t, CURSOR_A);
      const intro = A.easeOut(t / 1.1); document.body.style.setProperty('--intro', intro.toFixed(3));
    },
  };

  V['title-b'] = {
    theme: 'maquette', cam: { cx: 12.6, cy: 2.0, cz: 2.0, scale: 1 / 23, fx: 0.5, fy: 0.5 },
    build(root, th) {
      root.innerHTML = `
        <div class="lb-tilt top"></div><div class="lb-tilt bottom"></div>
        <header class="tb-hero"><div class="em"></div><div class="word">ARFFORNIA</div><p class="tagline"></p></header>
        <div class="tb-chip srv"><i></i><span></span></div>
        <div class="tb-chip news"><b></b><span></span></div>
        <nav class="tb-dock">
          <button class="side" data-hover data-k="menu.singleplayer"><span class="glyph">◆</span><span class="l"></span></button>
          <button class="side" data-hover data-k="menu.multiplayer"><span class="glyph">◇◇</span><span class="l"></span></button>
          <button class="play" data-hover><span class="ico">▶</span><span class="l"></span></button>
          <button class="side" data-hover data-k="fml.menu.mods"><span class="glyph">▦</span><span class="l"></span></button>
          <button class="side" data-hover data-k="menu.options"><span class="glyph">⚙</span><span class="l"></span></button>
        </nav>
        <button class="tb-quit" data-hover title="quit">⏻</button>
        <div class="tb-foot"><span class="ver"></span><span class="credits"></span></div>
        <div class="cursor"></div>`;
      $('.em').appendChild(emblem(64, th)); $('.tagline').textContent = tr('gui.arffornia.title.tagline');
      document.querySelectorAll('.tb-dock .side').forEach((b) => { b.querySelector('.l').textContent = tr(b.dataset.k); });
      $('.tb-dock .play .l').textContent = tr('gui.arffornia.title.play');
      $('.tb-chip.news b').textContent = tr('gui.arffornia.title.news'); $('.tb-chip.news span').textContent = tr('gui.arffornia.title.news.headline');
      $('.ver').textContent = tr('gui.arffornia.title.version'); $('.credits').textContent = tr('title.credits');
    },
    frame(t) {
      const players = 42 + Math.round(2 * Math.sin(t * 0.3)); $('.tb-chip.srv span').textContent = tr('gui.arffornia.title.server.online', players, 18);
      $('.tb-chip.srv i').style.opacity = (0.55 + 0.45 * Math.sin(t * 3)).toFixed(2);
      hoverUpdate(t, CURSOR_B);
      document.body.style.setProperty('--intro', A.easeOut(t / 1.1).toFixed(3));
    },
  };

  // ------------------------------------------------------------ boot
  const DEBUG = qs.get('debug') === '1';
  const view = V[VIEW]; const th = A.THEMES[view.theme];
  document.body.classList.add(view.theme, VIEW, 'lang-' + LANG);
  const canvas = $('#c'); const ctx = canvas.getContext('2d'); const hud = $('#hud');
  function size() { const dpr = window.devicePixelRatio || 1; canvas.width = Math.round(innerWidth * dpr); canvas.height = Math.round(innerHeight * dpr); return dpr; }
  let dpr = size(); addEventListener('resize', () => { dpr = size(); });
  window.renderFrame = function (t) {
    A.renderScene(ctx, innerWidth, innerHeight, dpr, th, t, view.cam);
    view.frame(t);
  };
  window.READY = document.fonts.ready.then(() => { view.build(hud, th); return Promise.all([...hud.querySelectorAll('img')].map((i) => i.decode().catch(() => {}))); }).then(() => { window.renderFrame(0); return true; });
  const freeze = qs.get('t');
  window.READY.then(() => {
    if (freeze !== null) { window.renderFrame(parseFloat(freeze)); document.body.classList.add('frozen'); return; }
    if (qs.get('record') === '1') return;
    const t0 = performance.now(); const loop = (now) => { window.renderFrame(((now - t0) / 1000) % (VIEW.startsWith('loading') ? 15 : 1e9)); requestAnimationFrame(loop); }; requestAnimationFrame(loop);
  });
})();
