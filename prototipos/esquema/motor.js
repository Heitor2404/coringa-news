/* MOTOR DE ESQUEMA — protótipo isolado (Etapa 3, 13/11/2026). NÃO está ligado ao template principal.
 *
 * Um esquema é um JSON (spec) com:
 *   elementos  [{id, tipo, x, y, ...parâmetros do tipo, props:{nome: número | [[t, valor, easing?], ...]}}]
 *   rotulos    [{texto, alvo:[x,y], pos:[x,y], de, ate}]            — sempre legíveis (não escalam com o elemento)
 *   passos     [{de, ate, titulo, fala, destaque:[ids]}]            — sincronia com a narração; destaque escurece o resto
 * O tempo é a única entrada: seek(t) desenha o quadro t do zero (determinístico, como o template atual).
 * Tipos desconhecidos são REJEITADOS (validar) — nada é desenhado "mais ou menos".
 */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const W = 1080, H = 1920;
  const ZONA = { topo: 270, diagramaFim: 1150, legendaFim: 1480, margem: 50, direita: 930 };
  const COR = { y: '#FFD21F', bg: '#05080f', mut: '#9aa6bb', linha: 'rgba(255,255,255,.14)', txt: '#eef2f8',
                nervo: '#7f9bc4', azul: '#5b9bff' };

  // ───────────── utilidades ─────────────
  const el = (tag, at = {}, pai) => { const n = document.createElementNS(NS, tag); for (const k in at) n.setAttribute(k, at[k]); if (pai) pai.appendChild(n); return n; };
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, k) => a + (b - a) * k;
  const EASE = {
    linear: k => k,
    suave: k => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2,
    saida: k => 1 - Math.pow(1 - k, 3),
    entrada: k => k * k * k,
    mola: k => { const c1 = 1.2, c3 = c1 + 1; return 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); },
  };
  function trilha(tr, t, def) {
    if (tr === undefined) return def;
    if (typeof tr === 'number') return tr;
    if (!tr.length) return def;
    if (t <= tr[0][0]) return tr[0][1];
    for (let i = 1; i < tr.length; i++) {
      const [t1, v1, e] = tr[i], [t0, v0] = tr[i - 1];
      if (t <= t1) { const k = t1 === t0 ? 1 : (t - t0) / (t1 - t0); return lerp(v0, v1, (EASE[e || 'suave'] || EASE.suave)(k)); }
    }
    return tr[tr.length - 1][1];
  }
  function semente(s) { let a = s >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function hex(c) { c = c.replace('#', ''); return [0, 2, 4].map(i => parseInt(c.substr(i, 2), 16)); }
  function mistura(a, b, k) { const A = hex(a), B = hex(b); return 'rgb(' + A.map((v, i) => Math.round(lerp(v, B[i], clamp(k)))).join(',') + ')'; }
  // curva suave por pontos (Catmull-Rom → Bézier)
  function curva(p, fechar = false) {
    if (p.length < 2) return '';
    let d = `M${p[0][0]},${p[0][1]}`;
    const n = p.length, P = i => fechar ? p[(i + n) % n] : p[Math.max(0, Math.min(n - 1, i))];
    const fim = fechar ? n : n - 1;
    for (let i = 0; i < fim; i++) {
      const p0 = P(i - 1), p1 = P(i), p2 = P(i + 1), p3 = P(i + 2);
      d += ` C${p1[0] + (p2[0] - p0[0]) / 6},${p1[1] + (p2[1] - p0[1]) / 6} ${p2[0] - (p3[0] - p1[0]) / 6},${p2[1] - (p3[1] - p1[1]) / 6} ${p2[0]},${p2[1]}`;
    }
    return d + (fechar ? 'Z' : '');
  }
  const reta = p => p.map((q, i) => (i ? 'L' : 'M') + q[0] + ',' + q[1]).join(' ');
  function texto(pai, s, at, base) {           // *palavra* = destaque amarelo
    const n = el('text', at, pai);
    String(s).split(/(\*[^*]+\*)/).forEach(parte => {
      if (!parte) return;
      const h = parte.startsWith('*');
      const sp = el('tspan', h ? { fill: COR.y } : {}, n); sp.textContent = h ? parte.slice(1, -1) : parte;
    });
    return n;
  }

  // ───────────── primitivas ─────────────
  // cada uma: criar(g, e, ctx) → estado; desenhar(estado, e, P, t). P = props avaliadas no tempo t.
  const PRIM = {};

  /* CROMATÓFORO (v2, 13/11): saco elástico de pigmento com 12–20 músculos radiais (cada um um feixe de fibras), presos
     em pontos do tecido; o nervo chega num ponto ("entrada") e se RAMIFICA pelos dois lados até cada músculo.
     abertura 0→1: os músculos encurtam e puxam a borda do saco (o pigmento se espalha num disco de borda irregular).
     sinal 0→1: o impulso corre pelos ramos e acende cada terminal; ativo: músculos em contração.
     Bordas orgânicas por deslocamento de ruído (filtro "org"); vizinhos desfocados dão profundidade de tecido. */
  PRIM.cromatoforo = {
    props: { abertura: 0, sinal: 0, ativo: 0, nervos: 1 },
    criar(g, e, ctx) {
      const r = semente(e.semente || 7), n = e.musculos || 16, s = {}, A = e.ancora || 205;
      s.A = A; s.ent = (e.entrada ?? -90) * Math.PI / 180;
      s.ang = Array.from({ length: n }, (_, i) => (i / n) * Math.PI * 2 + (r() - .5) * .22);
      s.Ai = s.ang.map(() => A * (.84 + r() * .2));
      s.fase = [r() * 6, r() * 6, r() * 6, r() * 6];
      // tecido: textura + vizinhos desfocados (outros cromatóforos fora de foco)
      if (e.lente) {
        el('circle', { r: A + 44, fill: '#0a0d14', stroke: 'rgba(255,255,255,.55)', 'stroke-width': 3 }, g);
        el('circle', { r: A + 52, fill: 'none', stroke: 'rgba(5,8,15,.9)', 'stroke-width': 10 }, g);
      }
      const clipT = el('clipPath', { id: ctx.uid('ct') }, ctx.defs); el('circle', { r: A + (e.lente ? 43 : 150) }, clipT);
      const tec = el('g', { 'clip-path': `url(#${clipT.id})` }, g);
      const tg = el('radialGradient', { id: ctx.uid('tec') }, ctx.defs);
      [['0%', '#4a3a31', .75], ['65%', '#2c2220', .55], ['100%', '#130f10', 0]].forEach(([o, c, a]) => el('stop', { offset: o, 'stop-color': c, 'stop-opacity': a }, tg));
      el('circle', { r: A + 150, fill: `url(#${tg.id})` }, tec);
      el('circle', { r: A + 150, fill: 'url(#' + ctx.celulas + ')', opacity: .5 }, tec);
      s.viz = [];
      const nv = e.vizinhos ?? 7;
      for (let i = 0; i < nv; i++) {
        const a = r() * Math.PI * 2, d = A * (1.1 + r() * .3), rv = 8 + r() * 12;
        const c = el('circle', { cx: Math.cos(a) * d, cy: Math.sin(a) * d, fill: ['#6a2a18', '#8a5a22', '#3e1c12'][i % 3], filter: 'url(#desfoque)', opacity: .55 }, tec);
        s.viz.push({ c, rv, k: .35 + r() * .5 });
      }
      s.halo = el('circle', { r: A + 40, fill: `url(#${ctx.halo})`, opacity: .45 }, g);
      // nervo ramificado: dois ramos a partir da entrada, contornando o saco em raio irregular
      const Rb = th => A * 1.03 + 7 * Math.sin(3 * th + s.fase[3]) + 4 * Math.sin(7 * th);
      s.ramos = [1, -1].map(sg => {
        const pts = [];
        for (let k = 0; k <= 40; k++) { const th = s.ent + sg * k / 40 * Math.PI * .97; pts.push([Math.cos(th) * Rb(th), Math.sin(th) * Rb(th)]); }
        const d = curva(pts);
        const base = el('path', { d, fill: 'none', stroke: COR.nervo, 'stroke-width': 1.8, 'stroke-linecap': 'round', opacity: .3 }, g);
        const luz = el('path', { d, fill: 'none', stroke: COR.y, 'stroke-width': 4, 'stroke-linecap': 'round', filter: `url(#${ctx.glow})` }, g);
        return { base, luz, L: base.getTotalLength() };
      });
      s.Rb = Rb;
      // músculos: feixes de 3 fibras
      s.mus = s.ang.map(() => ({ f: [0, 1, 2].map(() => el('path', { fill: `url(#${ctx.musc})`, stroke: 'rgba(255,190,180,.18)', 'stroke-width': .8 }, g)),
                                 estr: el('path', { fill: 'none', stroke: 'rgba(255,225,220,.35)', 'stroke-width': 1.2, 'stroke-dasharray': '1.5 4' }, g) }));
      s.ter = s.ang.map(() => el('path', { fill: 'none', stroke: COR.nervo, 'stroke-width': 1.8, 'stroke-linecap': 'round' }, g));
      s.terPt = s.ang.map(() => el('circle', { r: 3.5, fill: COR.nervo }, g));
      s.anc = s.ang.map((a, i) => el('circle', { cx: Math.cos(a) * s.Ai[i], cy: Math.sin(a) * s.Ai[i], r: 3.2, fill: '#4a4f60', opacity: .8 }, g));
      // saco (com borda orgânica)
      const gr = el('radialGradient', { id: ctx.uid('pig'), cx: '46%', cy: '44%', r: '60%' }, ctx.defs);
      s.st = [el('stop', { offset: '0%' }, gr), el('stop', { offset: '78%' }, gr), el('stop', { offset: '100%' }, gr)];
      const org = el('g', { filter: 'url(#org)' }, g);
      s.saco = el('path', { fill: `url(#${gr.id})`, class: 'saco' }, org);
      s.gran = Array.from({ length: e.granulos || 90 }, () => ({ rho: Math.sqrt(r()) * .9, phi: r() * Math.PI * 2, sz: 1.4 + r() * 2.6,
        n: el('circle', { fill: r() > .5 ? '#2a0904' : '#4a1408' }, org) }));
      s.borda = el('path', { fill: 'none', stroke: 'rgba(40,8,4,.55)', 'stroke-width': 3 }, org);
      s.brilho = el('ellipse', { fill: 'rgba(255,235,220,.13)', filter: 'url(#desfoque)' }, g);
      return s;
    },
    desenhar(s, e, P) {
      const r0 = e.r0 || 20, r1 = e.r1 || 108, A = s.A, k = clamp(P.abertura), at = clamp(P.ativo);
      const R = lerp(r0, r1, EASE.saida(k));
      const f = s.fase;
      const borda = a => R * (1 + .08 * Math.sin(3 * a + f[0]) * (.5 + k) + .05 * Math.sin(5 * a + f[1]) * (.4 + k)
                                + .035 * Math.sin(9 * a + f[2]) * k + .02 * Math.sin(14 * a + f[0]) * k);
      const pts = []; for (let i = 0; i < 64; i++) { const a = i / 64 * Math.PI * 2; const b = borda(a); pts.push([Math.cos(a) * b, Math.sin(a) * b]); }
      const d = curva(pts, true); s.saco.setAttribute('d', d); s.borda.setAttribute('d', d);
      const pig = e.pigmento || ['#3c0e08', '#5e1a0e', '#2a0804'], aberto = e.pigmento_aberto || ['#b04a26', '#933620', '#5a1a0e'];
      s.st.forEach((st, i) => st.setAttribute('stop-color', mistura(pig[i], aberto[i], k)));
      s.borda.setAttribute('opacity', lerp(.4, .9, k));
      s.gran.forEach(q => { const b = borda(q.phi) * q.rho; q.n.setAttribute('cx', Math.cos(q.phi) * b); q.n.setAttribute('cy', Math.sin(q.phi) * b);
        q.n.setAttribute('r', q.sz * lerp(.6, 1, k)); q.n.setAttribute('opacity', lerp(.25, .7, k)); });
      s.brilho.setAttribute('cx', -R * .3); s.brilho.setAttribute('cy', -R * .34); s.brilho.setAttribute('rx', R * .38); s.brilho.setAttribute('ry', R * .2);
      s.viz.forEach(v => v.c.setAttribute('r', v.rv * (1 + 1.4 * k * v.k)));
      const corM0 = mistura('#6b2c40', '#ff9a86', at), corM1 = mistura('#40182a', '#d4566a', at);
      PRIM.cromatoforo._g = PRIM.cromatoforo._g || {};
      const sg = clamp(P.sinal), alcance = sg * Math.PI * .97;
      s.ang.forEach((a, i) => {
        const c = Math.cos(a), sn = Math.sin(a), b = borda(a) * .97, Ai = s.Ai[i];
        const x0 = c * b, y0 = sn * b, x1 = c * (Ai - 3), y1 = sn * (Ai - 3), comp = Ai - b;
        const larg = lerp(4, 13, k) * (1 + .2 * at) * clamp(comp / 60, .55, 1.35), ond = (1 - k) * 8 * (i % 2 ? 1 : -1);
        const px = -sn, py = c;
        s.mus[i].f.forEach((fp, j) => {
          const off = (j - 1) * larg * .62, w = larg * .42;
          const mx = (x0 + x1) / 2 - sn * ond + px * off, my = (y0 + y1) / 2 + c * ond + py * off;
          const ax = x0 + px * off * .35, ay = y0 + py * off * .35, bx = x1 + px * off * .2, by = y1 + py * off * .2;
          fp.setAttribute('d', `M${ax},${ay} Q${mx + px * w},${my + py * w} ${bx},${by} Q${mx - px * w},${my - py * w} ${ax},${ay}Z`);
          fp.setAttribute('fill', j === 1 ? corM0 : corM1);
        });
        const mx = (x0 + x1) / 2 - sn * ond, my = (y0 + y1) / 2 + c * ond;
        s.mus[i].estr.setAttribute('d', `M${x0},${y0} Q${mx},${my} ${x1},${y1}`);
        // terminal: do ramo até o meio do músculo; acende quando o impulso passa por esse ângulo
        const dist = Math.abs(((a - s.ent) % (2 * Math.PI) + 3 * Math.PI) % (2 * Math.PI) - Math.PI);
        const aceso = clamp((alcance - dist + .25) / .25);
        const Rb = s.Rb(a), tx = c * Rb, ty = sn * Rb;
        const qx = x0 + (x1 - x0) * .72 - sn * ond * .5, qy = y0 + (y1 - y0) * .72 + c * ond * .5;
        s.ter[i].setAttribute('d', `M${tx},${ty} Q${c * (Ai + 2) + px * 8},${sn * (Ai + 2) + py * 8} ${qx},${qy}`);
        const cor = mistura('#7f9bc4', '#FFD21F', aceso);
        s.ter[i].setAttribute('stroke', cor); s.ter[i].setAttribute('opacity', P.nervos);
        s.terPt[i].setAttribute('cx', qx); s.terPt[i].setAttribute('cy', qy); s.terPt[i].setAttribute('fill', cor);
        s.terPt[i].setAttribute('opacity', P.nervos); s.terPt[i].setAttribute('r', 3 + 2.5 * aceso * (1 - at * .5));
      });
      s.ramos.forEach(rm => { const seg = rm.L * .28, pos = rm.L * sg;      // impulso = trecho de luz que corre (não acende o anel todo)
        rm.luz.setAttribute('stroke-dasharray', sg < 1 ? `0 ${Math.max(0, pos - seg)} ${Math.min(seg, pos)} ${rm.L}` : `${rm.L} 0`);
        rm.luz.setAttribute('opacity', sg <= 0 ? 0 : sg < 1 ? 1 : .18); rm.base.setAttribute('opacity', .3 * P.nervos);
        rm.luz.style.display = P.nervos > .05 ? '' : 'none'; });
    },
  };

  /* PELE: trecho de pele com centenas de cromatóforos (amarelos, vermelhos, marrons) sobre a base clara.
     abertura: todos; onda (0→1): abertura que se espalha do centro (ox, oy em fração) — a cor muda em toda a pele. */
  PRIM.pele = {
    props: { abertura: 0, onda: 0, fecha: 0 },
    criar(g, e, ctx) {
      const r = semente(e.semente || 3), w = e.w, h = e.h, s = { w, h, pts: [] };
      const clip = el('clipPath', { id: ctx.uid('clip') }, ctx.defs);
      el('rect', { x: -w / 2, y: -h / 2, width: w, height: h, rx: e.raio || 36 }, clip);
      const base = el('linearGradient', { id: ctx.uid('base'), x1: 0, y1: 0, x2: 0, y2: 1 }, ctx.defs);
      const bc = e.base || ['#d9c7ad', '#b8a48a'];
      el('stop', { offset: '0%', 'stop-color': bc[0] }, base); el('stop', { offset: '100%', 'stop-color': bc[1] }, base);
      const gg = el('g', { 'clip-path': `url(#${clip.id})` }, g);
      el('rect', { x: -w / 2, y: -h / 2, width: w, height: h, fill: `url(#${base.id})` }, gg);
      s.cam = el('g', { filter: e.organico === false ? '' : 'url(#org)' }, gg);
      const n = e.n || Math.round(w * h / 1500), cores = e.cores || ['#c99a2e', '#a8432a', '#5a2a1a', '#7a3220'];
      const fixos = e.fixos || [];                 // posições garantidas (para um rótulo apontar para um cromatóforo real)
      for (let i = 0; i < n + fixos.length; i++) {
        const f = fixos[i - n], x = f ? f[0] : (r() - .5) * w, y = f ? f[1] : (r() - .5) * h, c = f ? cores[1] : cores[Math.floor(r() * cores.length)];
        s.pts.push({ x, y, d: 0, rmax: (e.rmax || 13) * (.7 + r() * .6), o: el('circle', { cx: x, cy: y, fill: c }, s.cam), j: r() });
      }
      const ox = (e.ox ?? .5) - .5, oy = (e.oy ?? .5) - .5;
      const dm = Math.hypot(w, h) * .62;
      s.pts.forEach(p => p.d = Math.hypot(p.x - ox * w, p.y - oy * h) / dm);
      el('rect', { x: -w / 2, y: -h / 2, width: w, height: h, fill: 'url(#' + ctx.grao + ')', opacity: .35 }, gg);
      el('rect', { x: -w / 2 + 1, y: -h / 2 + 1, width: w - 2, height: h - 2, rx: e.raio || 36, fill: 'none', stroke: 'rgba(255,255,255,.22)', 'stroke-width': 2 }, g);
      s.frente = el('circle', { fill: 'none', stroke: 'rgba(255,210,31,.0)', 'stroke-width': 3 }, gg);
      s.o = [ox * w, oy * h, dm];
      return s;
    },
    desenhar(s, e, P) {
      const banda = .18;
      s.pts.forEach(p => {
        const w = clamp((P.onda * (1 + banda) - p.d) / banda);
        const k = EASE.saida(clamp(Math.max(P.abertura, w) - p.j * .08)) * (1 - clamp(P.fecha));   // fecha: relaxam todos
        p.o.setAttribute('r', lerp(1.6, p.rmax, k)); p.o.setAttribute('opacity', lerp(.9, .82, k));
      });
      const fr = P.onda > 0 && P.onda < 1;
      s.frente.setAttribute('cx', s.o[0]); s.frente.setAttribute('cy', s.o[1]); s.frente.setAttribute('r', Math.max(0, P.onda * s.o[2]));
      s.frente.setAttribute('stroke', fr ? `rgba(255,210,31,${.5 * (1 - P.onda)})` : 'rgba(0,0,0,0)');
    },
  };

  /* NEURÔNIO: corpo celular com dendritos; aceso = disparando. A saída do axônio fica em (0, +raio). */
  PRIM.neuronio = {
    props: { aceso: 0 },
    criar(g, e, ctx) {
      const r = semente(e.semente || 11), R = e.raio || 30, s = {};
      s.halo = el('circle', { r: R * 3.2, fill: `url(#${ctx.haloY})` }, g);
      const dd = [];
      for (let i = 0; i < 7; i++) {
        const a = -Math.PI / 2 + (i - 3) * .42 + (r() - .5) * .2, L = R * (1.8 + r() * 1.2);
        const p0 = [Math.cos(a) * R * .8, Math.sin(a) * R * .8], p1 = [Math.cos(a) * L * .55 + (r() - .5) * 10, Math.sin(a) * L * .55], p2 = [Math.cos(a + (r() - .5) * .5) * L, Math.sin(a) * L];
        dd.push(curva([p0, p1, p2]));
        if (r() > .35) { const b = a + (r() > .5 ? .5 : -.5); dd.push(curva([p1, [p1[0] + Math.cos(b) * L * .35, p1[1] + Math.sin(b) * L * .35]])); }
      }
      s.dend = el('path', { d: dd.join(' '), fill: 'none', stroke: '#8aa3c8', 'stroke-width': 3.2, 'stroke-linecap': 'round' }, g);
      const pts = []; for (let i = 0; i < 24; i++) { const a = i / 24 * Math.PI * 2; const b = R * (1 + .12 * Math.sin(3 * a + 1) + .06 * Math.sin(5 * a)); pts.push([Math.cos(a) * b, Math.sin(a) * b * .92]); }
      s.corpo = el('path', { d: curva(pts, true), stroke: 'rgba(255,255,255,.5)', 'stroke-width': 2 }, g);
      s.nucleo = el('circle', { r: R * .38, cx: -2, cy: -3, fill: 'rgba(5,8,15,.55)' }, g);
      return s;
    },
    desenhar(s, e, P) {
      const a = clamp(P.aceso);
      s.corpo.setAttribute('fill', mistura('#3c5376', '#FFD21F', a)); s.dend.setAttribute('stroke', mistura('#8aa3c8', '#ffe27a', a));
      s.halo.setAttribute('opacity', a * .9);
    },
  };

  /* NERVO: caminho (pontos) com um impulso que viaja. pulso: posição 0→1 (fora disso, apagado); aceso: caminho todo aceso. */
  PRIM.nervo = {
    props: { pulso: -1, aceso: 0 },
    criar(g, e, ctx) {
      const d = curva(e.pontos.map(p => [p[0] - e.x, p[1] - e.y]));
      const s = { base: el('path', { d, fill: 'none', stroke: COR.nervo, 'stroke-width': e.largura || 5, 'stroke-linecap': 'round', opacity: .6 }, g) };
      s.bainha = el('path', { d, fill: 'none', stroke: 'rgba(127,155,196,.18)', 'stroke-width': (e.largura || 5) + 10, 'stroke-linecap': 'round' }, g);
      g.insertBefore(s.bainha, s.base);
      s.luz = el('path', { d, fill: 'none', stroke: COR.y, 'stroke-width': (e.largura || 5) + 1, 'stroke-linecap': 'round', filter: `url(#${ctx.glow})` }, g);
      s.rastro = el('path', { d, fill: 'none', stroke: COR.y, 'stroke-width': (e.largura || 5) + 3, 'stroke-linecap': 'round', filter: `url(#${ctx.glow})` }, g);
      s.cab = el('circle', { r: (e.largura || 5) * 1.9, fill: '#fff6c8', filter: `url(#${ctx.glow})` }, g);
      s.L = s.base.getTotalLength();
      return s;
    },
    desenhar(s, e, P) {
      const L = s.L, p = P.pulso, rl = L * .22;
      s.luz.setAttribute('opacity', clamp(P.aceso)); s.luz.setAttribute('stroke-dasharray', `${L} ${L}`);
      if (p >= 0 && p <= 1) {
        const pos = p * L; s.rastro.setAttribute('stroke-dasharray', `0 ${Math.max(0, pos - rl)} ${Math.min(rl, pos)} ${L}`);
        s.rastro.setAttribute('opacity', 1);
        const q = s.base.getPointAtLength(pos); s.cab.setAttribute('cx', q.x); s.cab.setAttribute('cy', q.y); s.cab.setAttribute('opacity', 1);
      } else { s.rastro.setAttribute('opacity', 0); s.cab.setAttribute('opacity', 0); }
    },
  };

  /* RAIO de luz: polilinha; onda=true desenha a oscilação (comprimento de onda "lambda" em px). desenho 0→1 revela. */
  PRIM.raio = {
    props: { desenho: 1 },
    criar(g, e, ctx) {
      const pts = e.pontos.map(p => [p[0] - e.x, p[1] - e.y]);
      let d = reta(pts);
      if (e.onda) {
        const amostra = []; let acum = 0;
        for (let i = 1; i < pts.length; i++) {
          const [x0, y0] = pts[i - 1], [x1, y1] = pts[i], L = Math.hypot(x1 - x0, y1 - y0), ux = (x1 - x0) / L, uy = (y1 - y0) / L;
          for (let s2 = 0; s2 <= L; s2 += 3) { const o = Math.sin((acum + s2) / (e.lambda || 40) * Math.PI * 2) * (e.amplitude || 9);
            amostra.push([x0 + ux * s2 - uy * o, y0 + uy * s2 + ux * o]); }
          acum += L;
        }
        d = reta(amostra.map(p => [+p[0].toFixed(1), +p[1].toFixed(1)]));
      }
      const s = { halo: el('path', { d, fill: 'none', stroke: e.cor || '#fff', 'stroke-width': (e.largura || 4) + 8, opacity: .16, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, g) };
      s.p = el('path', { d, fill: 'none', stroke: e.cor || '#fff', 'stroke-width': e.largura || 4, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, g);
      s.L = s.p.getTotalLength();
      if (e.ponta) s.ponta = el('path', { d: 'M0,0 L-18,-9 L-14,0 L-18,9Z', fill: e.cor || '#fff' }, g);
      return s;
    },
    desenhar(s, e, P) {
      const k = clamp(P.desenho), da = `${s.L * k} ${s.L}`;
      s.p.setAttribute('stroke-dasharray', da); s.halo.setAttribute('stroke-dasharray', da);
      if (s.ponta) {
        const pos = Math.max(1, s.L * k), q = s.p.getPointAtLength(pos), q0 = s.p.getPointAtLength(Math.max(0, pos - 6));
        s.ponta.setAttribute('transform', `translate(${q.x},${q.y}) rotate(${Math.atan2(q.y - q0.y, q.x - q0.x) * 180 / Math.PI})`);
        s.ponta.setAttribute('opacity', k > .02 ? 1 : 0);
      }
    },
  };

  /* MOLÉCULA (N₂/O₂ esquemática): dois átomos; brilho = sendo atingida (espalha a luz). */
  PRIM.molecula = {
    props: { brilho: 0, oscila: 0, agita: 0 },
    criar(g, e, ctx) {
      const r = e.raio || 11, a = (e.angulo || 0) * Math.PI / 180, s = {};
      s.halo = el('circle', { r: r * 3.4, fill: `url(#${e.quente ? ctx.haloQ : ctx.haloB})` }, g);
      s.gir = el('g', {}, g);
      if (e.agua) {                       // H₂O: oxigênio (polo −) e dois hidrogênios (polo +) a 104,5°
        const h = 104.5 / 2 * Math.PI / 180, L = r * 1.55;
        [[-Math.sin(h) * L, Math.cos(h) * L], [Math.sin(h) * L, Math.cos(h) * L]].forEach(([x, y]) => {
          el('line', { x1: 0, y1: 0, x2: x, y2: y, stroke: 'rgba(255,255,255,.55)', 'stroke-width': 4 }, s.gir);
          el('circle', { cx: x, cy: y, r: r * .62, fill: '#e9eef6' }, s.gir); });
        s.at = [el('circle', { r, fill: '#e2574c' }, s.gir)];
        // polos indicados pela cor (O vermelho = −, H claro = +) e pelo rótulo: sinal desenhado giraria junto e viraria "×"
        s.agua = true;
      } else {
        const dx = Math.cos(a) * r * .8, dy = Math.sin(a) * r * .8;
        el('line', { x1: -dx, y1: -dy, x2: dx, y2: dy, stroke: 'rgba(255,255,255,.5)', 'stroke-width': 3 }, s.gir);
        s.at = [el('circle', { cx: -dx, cy: -dy, r, fill: '#c9d6ea' }, s.gir), el('circle', { cx: dx, cy: dy, r, fill: '#c9d6ea' }, s.gir)];
      }
      return s;
    },
    desenhar(s, e, P, t) {
      s.halo.setAttribute('opacity', clamp(P.brilho));
      if (!s.agua) s.at.forEach(a => a.setAttribute('fill', mistura('#9fb0c8', '#e6f0ff', P.brilho)));
      // segue o campo: o mesmo seno do PRIM.campo no x da molécula (freq em ciclos/s da ANIMAÇÃO, não a real)
      const xr = (e.x - (e.campo_x0 || 0)) / (e.campo_lambda || 1e9);
      const f = e.estacionaria ? Math.cos(2 * Math.PI * xr) * Math.cos(2 * Math.PI * (e.freq || 0) * t) : Math.sin(2 * Math.PI * (xr - (e.freq || 0) * t));
      const ag = P.agita, jx = ag * Math.sin(t * 7.3 + e.x * .13), jy = ag * Math.cos(t * 8.9 + e.y * .11);   // agitação = calor
      s.gir.setAttribute('transform', `translate(${jx},${jy}) rotate(${(e.angulo_base || 0) + P.oscila * f + ag * .8 * Math.sin(t * 11 + e.x)})`);
    },
  };

  /* CAMPO elétrico de uma onda: setas verticais ao longo de x cujo tamanho/sentido seguem sin(2π(x/λ − f·t)). */
  PRIM.campo = {
    props: { amplitude: 1 },
    criar(g, e) {
      const s = { s: [] }, n = e.n || 13;
      el('line', { x1: -e.w / 2, y1: 0, x2: e.w / 2, y2: 0, stroke: 'rgba(255,255,255,.18)', 'stroke-width': 2, 'stroke-dasharray': '4 8' }, g);
      for (let i = 0; i < n; i++) { const x = -e.w / 2 + e.w * i / (n - 1);
        s.s.push({ x, l: el('line', { x1: x, y1: 0, x2: x, y2: 0, stroke: e.cor || '#ffb347', 'stroke-width': 4, 'stroke-linecap': 'round' }, g),
                   p: el('path', { d: 'M0,0 L-9,-14 L9,-14Z', fill: e.cor || '#ffb347' }, g) }); }
      return s;
    },
    desenhar(s, e, P, t) {
      s.s.forEach(q => {
        const xr = (q.x + e.x - (e.campo_x0 ?? e.x - e.w / 2)) / e.lambda;
        const v = (e.estacionaria ? Math.cos(2 * Math.PI * xr) * Math.cos(2 * Math.PI * (e.freq || 0) * t)      // onda parada entre paredes
                                  : Math.sin(2 * Math.PI * (xr - (e.freq || 0) * t))) * (e.altura || 90) * P.amplitude;
        q.l.setAttribute('y2', -v); q.p.setAttribute('transform', `translate(${q.x},${-v}) rotate(${v >= 0 ? 180 : 0})`);
        q.p.setAttribute('opacity', Math.abs(v) > 14 ? 1 : 0); q.l.setAttribute('opacity', .35 + .65 * Math.abs(v) / (e.altura || 90)); q.l.setAttribute('stroke-width', e.espessura || 4);
      });
    },
  };

  /* OBSERVADOR: olho estilizado (quem vê o resultado). */
  PRIM.olho = {
    props: { cor: 0 },
    criar(g, e) {
      const r = e.raio || 34, s = {};
      el('path', { d: `M${-r * 1.8},0 Q0,${-r * 1.3} ${r * 1.8},0 Q0,${r * 1.3} ${-r * 1.8},0Z`, fill: '#0b1220', stroke: 'rgba(255,255,255,.7)', 'stroke-width': 3 }, g);
      s.iris = el('circle', { r: r * .62 }, g); el('circle', { r: r * .26, fill: '#05080f' }, g); el('circle', { cx: -r * .18, cy: -r * .2, r: r * .1, fill: '#fff' }, g);
      return s;
    },
    desenhar(s, e, P) { s.iris.setAttribute('fill', mistura('#6d7a8f', '#5b9bff', P.cor)); },
  };

  /* ESPALHAMENTO: luz reemitida em várias direções a partir de um ponto (n raios ondulados curtos). */
  PRIM.espalhamento = {
    props: { progresso: 0 },
    criar(g, e, ctx) {
      const n = e.n || 8, s = { r: [] }, r = semente(e.semente || 5);
      for (let i = 0; i < n; i++) {
        const a = i / n * Math.PI * 2 + r() * .4, L = e.comprimento || 120, pts = [];
        for (let d = 0; d <= L; d += 3) { const o = Math.sin(d / (e.lambda || 22) * Math.PI * 2) * 4; pts.push([Math.cos(a) * (d + 18) - Math.sin(a) * o, Math.sin(a) * (d + 18) + Math.cos(a) * o]); }
        const p = el('path', { d: reta(pts.map(q => [+q[0].toFixed(1), +q[1].toFixed(1)])), fill: 'none', stroke: e.cor || COR.azul, 'stroke-width': 3, 'stroke-linecap': 'round' }, g);
        s.r.push({ p, L: p.getTotalLength() });
      }
      return s;
    },
    desenhar(s, e, P) {
      const k = clamp(P.progresso);
      s.r.forEach(q => { const ini = q.L * Math.max(0, k - .45) / .55, fim = q.L * Math.min(1, k / .55);
        q.p.setAttribute('stroke-dasharray', `0 ${ini} ${Math.max(0, fim - ini)} ${q.L}`); q.p.setAttribute('opacity', k >= 1 ? 0 : 1); });
    },
  };

  /* FONTE DE LUZ (sol, laser): disco com halo. */
  PRIM.fonte_luz = {
    props: { intensidade: 1 },
    criar(g, e, ctx) {
      const r = e.raio || 46, s = {};
      s.h = el('circle', { r: r * 3, fill: `url(#${ctx.haloW})` }, g);
      s.d = el('circle', { r, fill: e.cor || '#fff5d6' }, g);
      return s;
    },
    desenhar(s, e, P) { s.h.setAttribute('opacity', clamp(P.intensidade)); s.d.setAttribute('opacity', .4 + .6 * clamp(P.intensidade)); },
  };

  /* FAIXA: camada (atmosfera, céu, casca da fibra) — retângulo com gradiente entre duas cores; mistura 0→1. */
  PRIM.faixa = {
    props: { mistura: 0 },
    criar(g, e, ctx) {
      const gr = el('linearGradient', { id: ctx.uid('fx'), x1: 0, y1: 0, x2: 0, y2: 1 }, ctx.defs);
      const s = { s0: el('stop', { offset: '0%' }, gr), s1: el('stop', { offset: '100%' }, gr) };
      s.r = el('rect', { x: -e.w / 2, y: -e.h / 2, width: e.w, height: e.h, rx: e.raio || 0, fill: `url(#${gr.id})`, stroke: e.borda || 'none', 'stroke-width': 2 }, g);
      if (e.difuso) {                         // bordas de cima/baixo esfumadas (camada de ar, não caixa)
        const mg = el('linearGradient', { id: ctx.uid('mg'), x1: 0, y1: 0, x2: 0, y2: 1 }, ctx.defs);
        [[0, 0], [.22, 1], [.78, 1], [1, 0]].forEach(([o, a]) => el('stop', { offset: o, 'stop-color': '#fff', 'stop-opacity': a }, mg));
        const mk = el('mask', { id: ctx.uid('mk'), maskContentUnits: 'userSpaceOnUse' }, ctx.defs);
        el('rect', { x: -e.w / 2, y: -e.h / 2, width: e.w, height: e.h, fill: `url(#${mg.id})` }, mk);
        s.r.setAttribute('mask', `url(#${mk.id})`);
      }
      return s;
    },
    desenhar(s, e, P) {
      const [a0, a1] = e.cores0 || ['#0b1424', '#0b1424'], [b0, b1] = e.cores1 || a0 && [a0, a1];
      s.s0.setAttribute('stop-color', mistura(a0, b0, P.mistura)); s.s1.setAttribute('stop-color', mistura(a1, b1, P.mistura));
      s.r.setAttribute('fill-opacity', e.opacidade ?? 1);
    },
  };

  /* CÉU com horizonte: gradiente vertical (zênite mais escuro, horizonte mais claro — o espalhamento múltiplo clareia a
     faixa perto do horizonte) que vai da noite/escuro (dia=0) ao céu diurno (dia=1); colinas em silhueta e chão escuro
     (a legenda fica sobre o chão, sempre legível). */
  PRIM.ceu = {
    props: { dia: 0 },
    criar(g, e, ctx) {
      const hz = e.horizonte || 1060, r = semente(e.semente || 2), s = {};
      const gr = el('linearGradient', { id: ctx.uid('ceu'), x1: 0, y1: 0, x2: 0, y2: 1, gradientUnits: 'userSpaceOnUse' }, ctx.defs);
      gr.setAttribute('y1', -e.y); gr.setAttribute('y2', hz - e.y);
      s.st = [0, .55, 1].map(o => el('stop', { offset: o }, gr));
      el('rect', { x: -e.x, y: -e.y, width: W, height: hz - e.y + 4, fill: `url(#${gr.id})` }, g);
      const colina = (y0, amp, freq, fase) => {
        let d = `M${-e.x},${hz - e.y + 40}`;
        for (let x = 0; x <= W; x += 20) d += ` L${x - e.x},${(y0 - e.y) - amp * (.5 + .5 * Math.sin(x / freq + fase)) - amp * .35 * Math.sin(x / (freq * .37) + fase * 2)}`;
        return d + ` L${W - e.x},${H - e.y} L${-e.x},${H - e.y}Z`;
      };
      s.c1 = el('path', { d: colina(hz + 6, 34, 140, r() * 6) }, g);
      s.c2 = el('path', { d: colina(hz + 34, 22, 90, r() * 6), fill: '#070a10' }, g);
      return s;
    },
    desenhar(s, e, P) {
      const k = clamp(P.dia), noite = ['#03050a', '#060a14', '#0d1526'], dia = e.cores_dia || ['#1a4fa6', '#3f7fd0', '#b9d3ee'];
      s.st.forEach((st, i) => st.setAttribute('stop-color', mistura(noite[i], dia[i], k)));
      s.c1.setAttribute('fill', mistura('#0b1019', '#2a3c52', k));
    },
  };

  /* FEIXE de luz branca: as cores viajam juntas (núcleo branco); separa 0→1 mostra os componentes lado a lado, cada um
     com seu comprimento de onda (lambdas, px). desenho 0→1 revela do início ao fim. */
  PRIM.feixe = {
    props: { desenho: 1, separa: 0 },
    criar(g, e) {
      const [x0, y0] = [e.de[0] - e.x, e.de[1] - e.y], [x1, y1] = [e.para[0] - e.x, e.para[1] - e.y];
      const L = Math.hypot(x1 - x0, y1 - y0), ux = (x1 - x0) / L, uy = (y1 - y0) / L, s = { L, comp: [] };
      s.nuc = el('line', { x1: x0, y1: y0, x2: x1, y2: y1, stroke: '#fff8e6', 'stroke-width': 7, 'stroke-linecap': 'round', filter: 'url(#glow)' }, g);
      (e.cores || [['#ff6a4d', 70], ['#7be88a', 53], ['#5b9bff', 45]]).forEach(([cor, lam], k) => {
        const p = el('path', { fill: 'none', stroke: cor, 'stroke-width': 4, 'stroke-linecap': 'round' }, g);
        s.comp.push({ p, cor, lam, k, x0, y0, ux, uy });
      });
      s.nComp = s.comp.length;
      return s;
    },
    desenhar(s, e, P, t) {
      const k = clamp(P.desenho), sep = clamp(P.separa), Lv = s.L * k;
      s.nuc.setAttribute('x2', s.comp[0].x0 + s.comp[0].ux * Lv); s.nuc.setAttribute('y2', s.comp[0].y0 + s.comp[0].uy * Lv);
      s.nuc.setAttribute('opacity', (1 - sep) * (k > 0 ? 1 : 0));
      s.comp.forEach(c => {
        const off = (c.k - (s.nComp - 1) / 2) * 22 * sep, pts = [];
        for (let d = 0; d <= Lv; d += 3) {
          const o = Math.sin((d - t * 120) / c.lam * Math.PI * 2) * 9 * sep + off;
          pts.push([+(c.x0 + c.ux * d - c.uy * o).toFixed(1), +(c.y0 + c.uy * d + c.ux * o).toFixed(1)]);
        }
        c.p.setAttribute('d', pts.length > 1 ? reta(pts) : ''); c.p.setAttribute('opacity', .25 + .75 * sep);
      });
    },
  };

  /* AR: nuvem de moléculas (N₂/O₂ esquemáticas) que se agitam; espalha 0→1 é a frente de luz chegando (a partir de
     "origem"): cada molécula atingida reemite ondas curtas azuis em todas as direções e fica com um brilho azul. */
  PRIM.ar = {
    props: { espalha: 0 },
    criar(g, e, ctx) {
      const r = semente(e.semente || 6), s = { m: [] }, o = e.origem ? [e.origem[0] - e.x, e.origem[1] - e.y] : [-e.w / 2, -e.h / 2];
      let dmax = 0;
      for (let i = 0; i < (e.n || 30); i++) {
        const x = (r() - .5) * e.w, y = (r() - .5) * e.h, a = r() * Math.PI, d = Math.hypot(x - o[0], y - o[1]);
        dmax = Math.max(dmax, d);
        const gm = el('g', {}, g);
        const halo = el('circle', { r: 26, fill: `url(#${ctx.haloB})`, opacity: 0 }, gm);
        const ondas = [0, 1, 2, 3, 4, 5].map(j => el('path', { fill: 'none', stroke: '#7fb2ff', 'stroke-width': 2, 'stroke-linecap': 'round', opacity: 0 }, gm));
        const dx = Math.cos(a) * 5, dy = Math.sin(a) * 5;
        el('line', { x1: -dx, y1: -dy, x2: dx, y2: dy, stroke: 'rgba(255,255,255,.45)', 'stroke-width': 2 }, gm);
        el('circle', { cx: -dx, cy: -dy, r: 5.5, fill: '#c9d6ea' }, gm); el('circle', { cx: dx, cy: dy, r: 5.5, fill: '#c9d6ea' }, gm);
        s.m.push({ gm, halo, ondas, x, y, d, ph: r() * 6, rot: r() * 6 });
      }
      s.m.forEach(q => q.d /= dmax);
      return s;
    },
    desenhar(s, e, P, t) {
      s.m.forEach(q => {
        const jx = 3 * Math.sin(t * 1.7 + q.ph), jy = 3 * Math.cos(t * 1.3 + q.ph * 1.7);
        q.gm.setAttribute('transform', `translate(${q.x + jx},${q.y + jy}) rotate(${(t * 20 + q.rot * 57) % 360})`);
        const p = clamp((P.espalha * 1.25 - q.d) / .25);                 // 0 → 1 enquanto a onda azul sai desta molécula
        q.halo.setAttribute('opacity', p > 0 ? .35 + .4 * (1 - p) : 0);
        q.ondas.forEach((w, j) => {
          if (p <= 0 || p >= 1) { w.setAttribute('opacity', 0); return; }
          const a = j / 6 * Math.PI * 2 + q.rot, r0 = 10 + 50 * p, r1 = r0 + 22, pts = [];
          for (let rr = r0; rr <= r1; rr += 2) { const o = Math.sin(rr / 5) * 3; pts.push([+(Math.cos(a) * rr - Math.sin(a) * o).toFixed(1), +(Math.sin(a) * rr + Math.cos(a) * o).toFixed(1)]); }
          w.setAttribute('d', reta(pts)); w.setAttribute('opacity', (1 - p) * .9);
        });
      });
    },
  };

  /* PESSOA em silhueta (observador), de pé; altura em px. */
  PRIM.pessoa = {
    props: {},
    criar(g, e) {
      const h = e.altura || 80, k = h / 80;
      el('circle', { cx: 0, cy: -72 * k, r: 7 * k, fill: e.cor || '#05070b' }, g);
      el('path', { d: `M${-9 * k},${-62 * k} Q0,${-66 * k} ${9 * k},${-62 * k} L${11 * k},${-30 * k} L${7 * k},${-30 * k} L${6 * k},0 L${1.5 * k},0 L0,${-26 * k} L${-1.5 * k},0 L${-6 * k},0 L${-7 * k},${-30 * k} L${-11 * k},${-30 * k}Z`, fill: e.cor || '#05070b' }, g);
      return {};
    },
    desenhar() {},
  };

  /* FORNO DE MICRO-ONDAS em corte: carcaça, cavidade de metal (paredes refletem), magnétron com aletas, guia de onda que
     desemboca no teto da cavidade, prato giratório e uma tigela de sopa. calor 0→1 esquenta a superfície da sopa. */
  PRIM.forno = {
    props: { calor: 0 },
    criar(g, e, ctx) {
      const s = {};
      const gc = el('linearGradient', { id: ctx.uid('carc'), x1: 0, y1: 0, x2: 0, y2: 1 }, ctx.defs);
      el('stop', { offset: '0%', 'stop-color': '#323c4b' }, gc); el('stop', { offset: '100%', 'stop-color': '#1a212c' }, gc);
      el('rect', { x: -430, y: -230, width: 860, height: 460, rx: 26, fill: `url(#${gc.id})`, stroke: 'rgba(255,255,255,.22)', 'stroke-width': 2 }, g);
      const gv = el('linearGradient', { id: ctx.uid('cav'), x1: 0, y1: 0, x2: 0, y2: 1 }, ctx.defs);
      el('stop', { offset: '0%', 'stop-color': '#0d121b' }, gv); el('stop', { offset: '100%', 'stop-color': '#121a26' }, gv);
      el('rect', { x: -380, y: -150, width: 620, height: 360, rx: 8, fill: `url(#${gv.id})`, stroke: '#9fb3cc', 'stroke-width': 4 }, g);
      el('rect', { x: -372, y: -142, width: 604, height: 344, rx: 6, fill: 'none', stroke: 'rgba(159,179,204,.25)', 'stroke-width': 1.5 }, g);
      // painel + magnétron (com aletas de refrigeração e antena)
      el('rect', { x: 262, y: -205, width: 146, height: 410, rx: 12, fill: '#1d2530', stroke: 'rgba(255,255,255,.12)' }, g);
      el('rect', { x: 290, y: -190, width: 96, height: 120, rx: 10, fill: '#46505f', stroke: 'rgba(255,255,255,.35)', 'stroke-width': 1.5 }, g);
      for (let i = 0; i < 7; i++) el('line', { x1: 298, y1: -178 + i * 15, x2: 378, y2: -178 + i * 15, stroke: 'rgba(255,255,255,.18)', 'stroke-width': 2 }, g);
      el('rect', { x: 276, y: -186, width: 16, height: 26, rx: 3, fill: '#c8a050' }, g);
      // guia de onda: duto do magnétron até a abertura no teto da cavidade
      el('rect', { x: 70, y: -206, width: 210, height: 44, fill: '#0f151e', stroke: '#9fb3cc', 'stroke-width': 3 }, g);
      el('rect', { x: 73, y: -164, width: 56, height: 18, fill: '#0f151e' }, g);
      // prato e tigela
      el('ellipse', { cx: -70, cy: 188, rx: 240, ry: 14, fill: 'rgba(190,220,255,.12)', stroke: 'rgba(255,255,255,.35)', 'stroke-width': 2 }, g);
      el('path', { d: 'M-215,112 Q-205,182 -70,182 Q65,182 75,112Z', fill: '#d7dce4', stroke: '#f2f4f8', 'stroke-width': 2 }, g);
      el('path', { d: 'M-200,112 Q-190,170 -70,170 Q50,170 60,112Z', fill: '#b9c0cc' }, g);
      s.sopa = el('ellipse', { cx: -70, cy: 113, rx: 136, ry: 12 }, g);
      s.calorG = el('ellipse', { cx: -70, cy: 100, rx: 160, ry: 60, fill: `url(#${ctx.haloQ})` }, g);
      el('ellipse', { cx: -70, cy: 112, rx: 145, ry: 14, fill: 'none', stroke: '#eef1f6', 'stroke-width': 3 }, g);
      return s;
    },
    desenhar(s, e, P) {
      const k = clamp(P.calor);
      s.sopa.setAttribute('fill', mistura('#9a6a2c', '#e0782e', k)); s.calorG.setAttribute('opacity', k * .9);
    },
  };

  /* VAPOR: fiapos que sobem e se dissolvem (determinístico pelo tempo); intensidade 0→1. */
  PRIM.vapor = {
    props: { intensidade: 0 },
    criar(g, e) {
      const r = semente(e.semente || 12), s = { f: [] };
      for (let i = 0; i < (e.n || 7); i++) s.f.push({ x: (r() - .5) * (e.w || 220), ph: r(), v: .35 + r() * .25, a: 6 + r() * 8,
        p: el('path', { fill: 'none', stroke: 'rgba(235,240,248,.55)', 'stroke-width': 5, 'stroke-linecap': 'round', filter: 'url(#desfoque)' }, g) });
      return s;
    },
    desenhar(s, e, P, t) {
      const H0 = e.altura || 220;
      s.f.forEach(q => {
        const c = ((t * q.v + q.ph) % 1), y0 = -c * H0, pts = [];
        for (let k = 0; k <= 10; k++) { const yy = y0 - k * 9; pts.push([+(q.x + Math.sin((yy / 30) + q.ph * 6 + t) * q.a).toFixed(1), +yy.toFixed(1)]); }
        q.p.setAttribute('d', curva(pts)); q.p.setAttribute('opacity', clamp(P.intensidade) * Math.sin(c * Math.PI) * .9);
      });
    },
  };

  /* FIBRA ÓPTICA: núcleo de vidro (índice maior) envolto pela casca (índice menor), em corte. */
  PRIM.fibra = {
    props: {},
    criar(g, e, ctx) {
      const w = e.w, hc = e.nucleo || 90, hk = e.casca || 34;
      el('rect', { x: -w / 2, y: -hc / 2 - hk, width: w, height: hc + 2 * hk, rx: (hc + 2 * hk) / 2, fill: '#13233a', stroke: 'rgba(255,255,255,.25)', 'stroke-width': 2 }, g);
      const gr = el('linearGradient', { id: ctx.uid('nuc'), x1: 0, y1: 0, x2: 0, y2: 1 }, ctx.defs);
      el('stop', { offset: '0%', 'stop-color': '#2b4f78' }, gr); el('stop', { offset: '50%', 'stop-color': '#3d6a9c' }, gr); el('stop', { offset: '100%', 'stop-color': '#2b4f78' }, gr);
      el('rect', { x: -w / 2, y: -hc / 2, width: w, height: hc, fill: `url(#${gr.id})`, opacity: .9 }, g);
      el('line', { x1: -w / 2, y1: -hc / 2, x2: w / 2, y2: -hc / 2, stroke: 'rgba(200,230,255,.55)', 'stroke-width': 1.5 }, g);
      el('line', { x1: -w / 2, y1: hc / 2, x2: w / 2, y2: hc / 2, stroke: 'rgba(200,230,255,.55)', 'stroke-width': 1.5 }, g);
      return {};
    },
    desenhar() {},
  };

  /* FLASH: clarão de quadro inteiro (revelação), cor e intensidade a. Determinístico (sem acaso). */
  PRIM.flash = {
    props: { a: 0 },
    criar(g, e) { return { r: el('rect', { x: 0, y: 0, width: W, height: H, fill: e.cor || '#fff7d6' }, g) }; },
    desenhar(s, e, P) { s.r.setAttribute('opacity', clamp(P.a)); },
  };

  /* VÉU: escurecimento em gradiente (foco no centro ou embaixo), para destacar a cadeia na revelação. */
  PRIM.veu = {
    props: { a: 0 },
    criar(g, e, ctx) {
      const gr = el('radialGradient', { id: ctx.uid('veu'), cx: (e.cx ?? .5), cy: (e.cy ?? .5), r: e.r ?? .55 }, ctx.defs);
      el('stop', { offset: '0%', 'stop-color': '#05080f', 'stop-opacity': e.centro ?? .5 }, gr); el('stop', { offset: '100%', 'stop-color': '#05080f', 'stop-opacity': .95 }, gr);
      return { r: el('rect', { x: 0, y: 0, width: W, height: H, fill: `url(#${gr.id})` }, g) };
    },
    desenhar(s, e, P) { s.r.setAttribute('opacity', clamp(P.a)); },
  };

  /* PULSO DE DESTAQUE: anel que se expande e some (onde algo acontece). */
  PRIM.brilho = {
    props: { p: -1 },
    criar(g, e) { return { c: el('circle', { fill: 'none', stroke: e.cor || COR.y, 'stroke-width': 3 }, g) }; },
    desenhar(s, e, P) { const k = P.p; if (k < 0 || k > 1) { s.c.setAttribute('opacity', 0); return; }
      s.c.setAttribute('r', lerp(e.r0 || 10, e.r1 || 70, EASE.saida(k))); s.c.setAttribute('opacity', 1 - k); },
  };

  /* SETA curva entre dois pontos (relação causal). desenho 0→1. */
  PRIM.seta = {
    props: { desenho: 1 },
    criar(g, e, ctx) {
      const [a, b] = [e.de, e.para].map(p => [p[0] - e.x, p[1] - e.y]), cv = e.curvatura || 0;
      const mx = (a[0] + b[0]) / 2 - (b[1] - a[1]) * cv, my = (a[1] + b[1]) / 2 + (b[0] - a[0]) * cv;
      const s = { p: el('path', { d: `M${a[0]},${a[1]} Q${mx},${my} ${b[0]},${b[1]}`, fill: 'none', stroke: e.cor || COR.mut, 'stroke-width': e.largura || 3, 'stroke-linecap': 'round', 'stroke-dasharray': e.tracejada ? '8 10' : '' }, g) };
      s.L = s.p.getTotalLength(); s.ponta = el('path', { d: 'M0,0 L-16,-8 L-12,0 L-16,8Z', fill: e.cor || COR.mut }, g);
      return s;
    },
    desenhar(s, e, P) {
      const k = clamp(P.desenho); if (!e.tracejada) s.p.setAttribute('stroke-dasharray', `${s.L * k} ${s.L}`);
      const pos = Math.max(1, s.L * k), q = s.p.getPointAtLength(pos), q0 = s.p.getPointAtLength(Math.max(0, pos - 5));
      s.ponta.setAttribute('transform', `translate(${q.x},${q.y}) rotate(${Math.atan2(q.y - q0.y, q.x - q0.x) * 180 / Math.PI})`); s.ponta.setAttribute('opacity', k > .05 ? 1 : 0);
    },
  };

  /* TEXTO livre (só no clímax): estilo titulo | sub | dado; *palavra* em amarelo; linhas separadas por \n. */
  PRIM.texto = {
    props: {},
    criar(g, e) {
      const est = { titulo: { fs: 74, fw: 900, ff: 'Mont', ls: -1.5, up: true }, sub: { fs: 34, fw: 700, ff: 'Mont', ls: 0, up: false },
                    dado: { fs: 28, fw: 700, ff: 'JBM', ls: 3, up: true } }[e.estilo || 'titulo'];
      const linhas = String(e.texto).split('\n'), s = { n: [] };
      linhas.forEach((ln, i) => s.n.push(texto(g, est.up ? ln.toUpperCase() : ln, { x: 0, y: i * est.fs * 1.06, 'text-anchor': 'middle', 'font-family': est.ff,
        'font-weight': est.fw, 'font-size': est.fs, 'letter-spacing': est.ls, fill: e.cor || '#fff', 'paint-order': 'stroke', stroke: 'rgba(5,8,15,.85)', 'stroke-width': 10, 'stroke-linejoin': 'round', class: 'txt' })));
      return s;
    },
    desenhar() {},
  };

  // ───────────── validação ─────────────
  const COMUNS = ['op', 'esc', 'dx', 'dy', 'rot'];
  function validar(spec) {
    const erros = [], ids = new Set();
    if (!spec || !Array.isArray(spec.elementos)) return ['spec sem "elementos"'];
    if (!(spec.duracao > 0)) erros.push('duracao ausente');
    spec.elementos.forEach((e, i) => {
      if (!e.id) erros.push(`elemento ${i} sem id`); else if (ids.has(e.id)) erros.push(`id repetido: ${e.id}`); else ids.add(e.id);
      const pr = PRIM[e.tipo];
      if (!pr) { erros.push(`tipo desconhecido: ${e.tipo} (${e.id})`); return; }
      for (const k in (e.props || {})) if (!(k in pr.props) && !COMUNS.includes(k)) erros.push(`prop desconhecida ${k} em ${e.id}`);
      if (['nervo', 'raio'].includes(e.tipo) && !(e.pontos && e.pontos.length >= 2)) erros.push(`${e.id}: precisa de "pontos"`);
    });
    (spec.rotulos || []).forEach((r, i) => { if (!r.texto || !r.pos) erros.push(`rótulo ${i} incompleto`); });
    (spec.passos || []).forEach((p, i) => (p.destaque || []).forEach(d => { if (!ids.has(d)) erros.push(`passo ${i}: destaque ${d} não existe`); }));
    return erros;
  }

  // ───────────── montagem e seek ─────────────
  let ESTADO = null;
  function carregar(spec, opc = {}) {
    const erros = validar(spec);
    if (erros.length) throw new Error('spec inválida: ' + erros.join('; '));
    const raiz = document.getElementById('esq'); raiz.innerHTML = '';
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H }, raiz);
    const defs = el('defs', {}, svg); let n = 0;
    const ctx = { defs, uid: p => `${p}${++n}` };
    const halo = (id, c, a) => { const g = el('radialGradient', { id }, defs); el('stop', { offset: '0%', 'stop-color': c, 'stop-opacity': a }, g); el('stop', { offset: '100%', 'stop-color': c, 'stop-opacity': 0 }, g); return id; };
    ctx.halo = halo('haloR', '#ff6a4a', .18); ctx.haloY = halo('haloY', '#FFD21F', .45); ctx.haloB = halo('haloB', '#5b9bff', .6); ctx.haloW = halo('haloW', '#fff2c4', .5); ctx.haloQ = halo('haloQ', '#ff8a3d', .6);
    const f = el('filter', { id: 'glow', x: '-50%', y: '-50%', width: '200%', height: '200%' }, defs);
    el('feGaussianBlur', { stdDeviation: 5, result: 'b' }, f); const m = el('feMerge', {}, f); el('feMergeNode', { in: 'b' }, m); el('feMergeNode', { in: 'SourceGraphic' }, m);
    ctx.glow = 'glow';
    const fo = el('filter', { id: 'org', x: '-20%', y: '-20%', width: '140%', height: '140%' }, defs);
    el('feTurbulence', { type: 'fractalNoise', baseFrequency: .045, numOctaves: 2, seed: 4, result: 'tn' }, fo);
    el('feDisplacementMap', { in: 'SourceGraphic', in2: 'tn', scale: 9, xChannelSelector: 'R', yChannelSelector: 'G' }, fo);
    const fd = el('filter', { id: 'desfoque', x: '-50%', y: '-50%', width: '200%', height: '200%' }, defs); el('feGaussianBlur', { stdDeviation: 4 }, fd);
    const cel = el('pattern', { id: 'celulas', width: 46, height: 40, patternUnits: 'userSpaceOnUse' }, defs);
    el('path', { d: 'M0,20 L11,0 L35,0 L46,20 L35,40 L11,40Z', fill: 'none', stroke: 'rgba(255,220,200,.10)', 'stroke-width': 1.2, filter: 'url(#org)' }, cel);
    ctx.celulas = 'celulas';
    const gm = el('linearGradient', { id: 'musc', x1: 0, y1: 0, x2: 1, y2: 1 }, defs);
    el('stop', { offset: '0%', 'stop-color': '#fff', 'stop-opacity': .0 }, gm); el('stop', { offset: '100%', 'stop-color': '#fff', 'stop-opacity': .0 }, gm);
    ctx.musc = 'musc';
    const pat = el('pattern', { id: 'grao', width: 120, height: 120, patternUnits: 'userSpaceOnUse' }, defs);
    const fr = el('filter', { id: 'ruido' }, defs); el('feTurbulence', { type: 'fractalNoise', baseFrequency: .8, numOctaves: 2 }, fr);
    el('feColorMatrix', { values: '0 0 0 0 .2  0 0 0 0 .1  0 0 0 0 .05  0 0 0 .9 0' }, fr);
    el('rect', { width: 120, height: 120, filter: 'url(#ruido)' }, pat); ctx.grao = 'grao';
    const camada = el('g', { id: 'cena' }, svg);
    const itens = spec.elementos.map(e => { const g = el('g', { 'data-id': e.id, 'data-tipo': e.tipo }, camada); const pr = PRIM[e.tipo]; return { e, g, pr, s: pr.criar(g, e, ctx) }; });
    // rótulos: por cima, nunca escalados
    const rot = el('g', { id: 'rotulos' }, svg);
    const rotulos = (spec.rotulos || []).map(r => {
      const g = el('g', { class: 'rotulo' }, rot);
      const lado = r.lado || (!r.alvo || r.pos[0] >= r.alvo[0] ? 'dir' : 'esq');
      const fs = r.tamanho || 26, linhas = r.texto.split('\n');
      const ex = lado === 'dir' ? -14 : lado === 'esq' ? 14 : 0, ey = lado === 'centro' ? -fs - 6 : -9;
      const linha = r.alvo ? el('path', { d: `M${r.alvo[0]},${r.alvo[1]} L${r.pos[0] + ex},${r.pos[1] + ey}`, fill: 'none', stroke: 'rgba(255,255,255,.6)', 'stroke-width': 2 }, g) : null;
      const pt = r.alvo ? el('circle', { cx: r.alvo[0], cy: r.alvo[1], r: 5.5, fill: COR.y }, g) : null;
      const t = el('g', { class: 'rot-txt' }, g);
      linhas.forEach((ln, i) => texto(t, ln.toUpperCase(), { x: r.pos[0], y: r.pos[1] + i * fs * 1.22, 'text-anchor': { dir: 'start', esq: 'end', centro: 'middle' }[lado],
        'font-family': 'JBM', 'font-weight': 700, 'font-size': fs, 'letter-spacing': 2.5, fill: i ? COR.mut : COR.txt, 'paint-order': 'stroke',
        stroke: 'rgba(5,8,15,.92)', 'stroke-width': 8, 'stroke-linejoin': 'round' }));
      return { r, g, linha, pt, t, L: linha ? linha.getTotalLength() : 0 };
    });
    // cabeçalho do passo (topo da área do diagrama) e legenda de mentira (só na prévia, para julgar a convivência)
    const cab = el('g', { id: 'passo' }, svg);
    const cabN = el('text', { x: W / 2, y: 452, 'text-anchor': 'middle', 'font-family': 'JBM', 'font-weight': 700, 'font-size': 24, 'letter-spacing': 4, fill: COR.mut }, cab);
    const cabT = el('text', { x: W / 2, y: 506, 'text-anchor': 'middle', 'font-family': 'Mont', 'font-weight': 800, 'font-size': 40, 'letter-spacing': -.3, fill: '#fff' }, cab);
    const pontos = (spec.passos || []).map((_, i, a) => el('rect', { x: W / 2 - a.length * 22 + i * 44 + 6, y: 524, width: 32, height: 5, rx: 2.5 }, cab));
    const leg = el('g', { id: 'legenda', style: opc.legenda ? '' : 'display:none' }, svg);
    ESTADO = { camada, spec, itens, rotulos, cab, cabN, cabT, pontos, leg, opc, mostraCab: spec.cabecalho !== false };
    seek(0);
    return true;
  }

  function passoEm(t) { const ps = ESTADO.spec.passos || []; let k = -1; ps.forEach((p, i) => { if (t >= p.de && t < p.ate) k = i; }); return k; }

  function seek(t) {
    const S = ESTADO; if (!S) return;
    const ps = S.spec.passos || [], k = passoEm(t), P0 = ps[k];
    // destaque: elementos fora do destaque do passo escurecem (com transição de 0,35 s)
    const peso = id => {
      if (!P0 || !P0.destaque || !P0.destaque.length) return 1;
      const em = P0.destaque.includes(id), anterior = ps[k - 1], entra = clamp((t - P0.de) / .35);
      const antes = !anterior || !anterior.destaque || !anterior.destaque.length || anterior.destaque.includes(id) ? 1 : .38;
      return lerp(antes, em ? 1 : .38, entra);
    };
    if (S.spec.camera) {                            // câmera da cena (empurrão, tremor de impacto), não mexe nos rótulos
      const c = S.spec.camera, o = c.origem || [W / 2, 900];
      const esc = trilha(c.esc, t, 1), dx = trilha(c.dx, t, 0), dy = trilha(c.dy, t, 0);
      S.camada.setAttribute('transform', `translate(${o[0] + dx},${o[1] + dy}) scale(${esc}) translate(${-o[0]},${-o[1]})`);
    }
    S.itens.forEach(({ e, g, pr, s }) => {
      const P = {}; const pp = e.props || {};
      for (const nm in pr.props) P[nm] = trilha(pp[nm], t, pr.props[nm]);
      const op = trilha(pp.op, t, 1) * peso(e.id), esc = trilha(pp.esc, t, 1), dx = trilha(pp.dx, t, 0), dy = trilha(pp.dy, t, 0), rot = trilha(pp.rot, t, 0);
      g.setAttribute('transform', `translate(${e.x + dx},${e.y + dy}) scale(${esc}) rotate(${rot})`);
      g.setAttribute('opacity', op.toFixed(3)); g.style.display = op < .005 ? 'none' : '';
      pr.desenhar(s, e, P, t);                      // sempre: o quadro t não depende do quadro anterior
    });
    S.rotulos.forEach(({ r, g, linha, pt, t: tx, L }) => {
      const de = r.de ?? 0, ate = r.ate ?? 1e9, k1 = clamp((t - de) / .45), k2 = clamp((ate - t) / .3), vis = Math.min(k1, k2);
      g.setAttribute('opacity', vis.toFixed(3)); g.style.display = vis < .005 ? 'none' : '';
      if (linha) linha.setAttribute('stroke-dasharray', `${L * EASE.saida(k1)} ${L}`);
      tx.setAttribute('opacity', clamp((t - de - .2) / .3)); if (pt) pt.setAttribute('r', 5.5 * EASE.mola(k1));
    });
    if (S.mostraCab && P0) {
      const ent = clamp((t - P0.de) / .3), sai = clamp((P0.ate - t) / .25);
      S.cabN.textContent = `PASSO ${k + 1} / ${ps.length}`; S.cabT.textContent = (P0.titulo || '').toUpperCase();
      S.cab.setAttribute('opacity', Math.min(ent, sai, 1)); S.cabT.setAttribute('transform', `translate(0,${(1 - EASE.saida(ent)) * 14})`);
      S.pontos.forEach((p, i) => p.setAttribute('fill', i === k ? COR.y : i < k ? 'rgba(255,210,31,.45)' : 'rgba(255,255,255,.2)'));
    } else S.cab.setAttribute('opacity', 0);
    if (S.opc.legenda) {
      S.leg.innerHTML = '';
      const fala = P0 ? P0.fala : '';
      if (fala) {
        const palavras = [];
        fala.split(/(\*[^*]+\*)/).forEach(p => { if (!p) return; const h = p.startsWith('*'), cola = !h && !/^\s/.test(p) && palavras.length;
          p.replace(/\*/g, '').split(' ').forEach((w, i) => { if (!w) return; if (i === 0 && cola) palavras[palavras.length - 1] += w; else palavras.push(h ? `*${w}*` : w); }); });
        const linhas = []; let ln = '';
        palavras.forEach(w => { const c = (ln + ' ' + w).trim(); if (c.replace(/\*/g, '').length > 19 && ln) { linhas.push(ln); ln = w; } else ln = c; }); if (ln) linhas.push(ln);
        linhas.slice(0, 4).forEach((l, i) => texto(S.leg, l.toUpperCase(), { x: W / 2, y: 1240 + i * 80, 'text-anchor': 'middle', 'font-family': 'Mont', 'font-weight': 900,
          'font-size': 76, 'letter-spacing': -1, fill: '#fff', 'paint-order': 'stroke', stroke: '#000', 'stroke-width': 12, 'stroke-linejoin': 'round', class: 'leg-txt' }));
      }
    }
  }

  // medidas para os testes: caixas dos rótulos e dos textos
  function medir() {
    const cx = n => { const b = n.getBoundingClientRect(); return { x: b.x, y: b.y, w: b.width, h: b.height,
      fs: parseFloat(n.getAttribute('font-size')) * (n.getScreenCTM() ? n.getScreenCTM().a : 1), txt: n.textContent }; };
    return {
      rotulos: [...document.querySelectorAll('#rotulos g.rotulo')].filter(g => g.style.display !== 'none' && +g.getAttribute('opacity') > .5)
        .flatMap(g => [...g.querySelectorAll('text')].map(cx)),
      textos: [...document.querySelectorAll('#cena text.txt')].filter(n => n.closest('g[data-id]').style.display !== 'none').map(cx),
    };
  }

  window.ESQUEMA = { carregar, seek, validar, medir, tipos: () => Object.keys(PRIM), ZONA };
  window.seek = seek;
})();
