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

  /* CROMATÓFORO: saco elástico de pigmento com músculos radiais presos em pontos fixos; terminais nervosos em anel.
     abertura 0→1: os músculos ENCURTAM e puxam a borda do saco para fora (o pigmento se espalha num disco).
     sinal 0→1: o impulso percorre o anel nervoso e acende cada terminal; ativo: músculos em contração (brilho). */
  PRIM.cromatoforo = {
    props: { abertura: 0, sinal: 0, ativo: 0, nervos: 1 },
    criar(g, e, ctx) {
      const r = semente(e.semente || 7), n = e.musculos || 14, s = {};
      s.ang = Array.from({ length: n }, (_, i) => (i / n) * Math.PI * 2 + (r() - .5) * .18);
      s.fase = [r() * 6, r() * 6, r() * 6];
      const A = e.ancora || 205;
      const gr = el('radialGradient', { id: ctx.uid('pig'), cx: '45%', cy: '42%', r: '62%' }, ctx.defs);
      s.st = [el('stop', { offset: '0%' }, gr), el('stop', { offset: '70%' }, gr), el('stop', { offset: '100%' }, gr)];
      const gm = el('linearGradient', { id: ctx.uid('mus'), x1: 0, y1: 0, x2: 1, y2: 0 }, ctx.defs);
      s.sm = [el('stop', { offset: '0%' }, gm), el('stop', { offset: '100%' }, gm)];
      if (e.lente) {                          // recorte "lupa" sobre outra cena (clímax): disco escuro com aro
        el('circle', { r: A + 44, fill: '#080c16', stroke: 'rgba(255,255,255,.55)', 'stroke-width': 3 }, g);
        el('circle', { r: A + 52, fill: 'none', stroke: 'rgba(5,8,15,.9)', 'stroke-width': 10 }, g);
      }
      const tg = el('radialGradient', { id: ctx.uid('tec') }, ctx.defs);
      [['0%', '#3a2f2a', .55], ['70%', '#241d1c', .35], ['100%', '#140f10', 0]].forEach(([o, c, a]) => el('stop', { offset: o, 'stop-color': c, 'stop-opacity': a }, tg));
      s.tecido = el('circle', { r: A + 70, fill: `url(#${tg.id})` }, g);
      s.halo = el('circle', { r: A + 60, fill: `url(#${ctx.halo})`, opacity: .55 }, g);
      s.anel = el('circle', { r: A + 22, fill: 'none', stroke: COR.nervo, 'stroke-width': 2, opacity: .35 }, g);
      const ent = e.entrada ?? -90;
      s.anelLuz = [1, -1].map(sg => el('circle', { r: A + 22, fill: 'none', stroke: COR.y, 'stroke-width': 5, 'stroke-linecap': 'round', filter: `url(#${ctx.glow})`, transform: `rotate(${ent}) scale(1,${sg})` }, g));
      s.ent = ent * Math.PI / 180;
      s.mus = s.ang.map(() => el('path', { fill: `url(#${gm.id})`, stroke: 'rgba(255,200,190,.25)', 'stroke-width': 1 }, g));
      s.ter = s.ang.map(() => el('path', { fill: 'none', stroke: COR.nervo, 'stroke-width': 2.2, 'stroke-linecap': 'round' }, g));
      s.terPt = s.ang.map(() => el('circle', { r: 4.5, fill: COR.nervo }, g));
      s.Ai = s.ang.map(() => A * (.86 + r() * .16));
      s.anc = s.ang.map((a, i) => el('circle', { cx: Math.cos(a) * s.Ai[i], cy: Math.sin(a) * s.Ai[i], r: 4, fill: '#3a4256', stroke: 'rgba(255,255,255,.3)', 'stroke-width': 1 }, g));
      s.saco = el('path', { fill: `url(#${gr.id})`, stroke: 'rgba(255,215,190,.55)', 'stroke-width': 2 }, g);
      s.gran = Array.from({ length: e.granulos || 46 }, () => ({ rho: Math.sqrt(r()) * .86, phi: r() * Math.PI * 2, sz: 2 + r() * 2.2,
        n: el('circle', { fill: '#2a0a06' }, g) }));
      s.brilho = el('ellipse', { fill: 'rgba(255,255,255,.18)' }, g);
      s.A = A;
      return s;
    },
    desenhar(s, e, P) {
      const r0 = e.r0 || 20, r1 = e.r1 || 108, A = s.A, k = clamp(P.abertura);
      const R = lerp(r0, r1, k);
      const borda = a => R * (1 + .07 * Math.sin(3 * a + s.fase[0]) * (0.4 + k) + .045 * Math.sin(5 * a + s.fase[1]) * (0.3 + k) + .03 * Math.sin(8 * a + s.fase[2]) * k);
      const pts = []; for (let i = 0; i < 48; i++) { const a = i / 48 * Math.PI * 2; const b = borda(a); pts.push([Math.cos(a) * b, Math.sin(a) * b]); }
      s.saco.setAttribute('d', curva(pts, true));
      const pig = e.pigmento || ['#4a130c', '#7a2516', '#2c0905'], aberto = e.pigmento_aberto || ['#b5532f', '#9a3a22', '#5c1d12'];
      s.st.forEach((st, i) => st.setAttribute('stop-color', mistura(pig[i], aberto[i], k)));
      s.saco.setAttribute('fill-opacity', lerp(1, .92, k));
      s.gran.forEach(q => { const b = borda(q.phi) * q.rho; q.n.setAttribute('cx', Math.cos(q.phi) * b); q.n.setAttribute('cy', Math.sin(q.phi) * b);
        q.n.setAttribute('r', q.sz * lerp(.75, 1, k)); q.n.setAttribute('opacity', lerp(.35, .8, k)); });
      s.brilho.setAttribute('cx', -R * .28); s.brilho.setAttribute('cy', -R * .32); s.brilho.setAttribute('rx', R * .32); s.brilho.setAttribute('ry', R * .16);
      const at = clamp(P.ativo);
      s.sm[0].setAttribute('stop-color', mistura('#6e2f45', '#ff8f7a', at)); s.sm[1].setAttribute('stop-color', mistura('#4d2236', '#d9566a', at));
      s.ang.forEach((a, i) => {          // fuso muscular entre a borda do saco e a âncora
        const c = Math.cos(a), sn = Math.sin(a), b = borda(a) * .96;
        const Ai = s.Ai[i], x0 = c * b, y0 = sn * b, x1 = c * (Ai - 4), y1 = sn * (Ai - 4);
        const comp = Ai - b, larg = lerp(3.5, 12, k) * (1 + .25 * at) * clamp(comp / 60, .5, 1.4);
        const ond = (1 - k) * 7 * (i % 2 ? 1 : -1);                 // relaxado: fibra frouxa, levemente ondulada
        const mx = (x0 + x1) / 2 - sn * ond, my = (y0 + y1) / 2 + c * ond, px = -sn * larg, py = c * larg;
        s.mus[i].setAttribute('d', `M${x0},${y0} Q${mx + px},${my + py} ${x1},${y1} Q${mx - px},${my - py} ${x0},${y0}Z`);
        // terminal: do anel (A+22) até o meio do músculo
        const tx = c * (A + 22), ty = sn * (A + 22);
        let dist = Math.abs(((a - s.ent) % (2 * Math.PI) + 3 * Math.PI) % (2 * Math.PI) - Math.PI);   // 0..π a partir da entrada
        const aceso = clamp((P.sinal * Math.PI - dist + .3) / .3);
        s.ter[i].setAttribute('d', `M${tx},${ty} Q${c * (A + 4) + px * .6},${sn * (A + 4) + py * .6} ${mx + px * .3},${my + py * .3}`);
        s.ter[i].setAttribute('stroke', mistura('#7f9bc4', '#FFD21F', aceso)); s.ter[i].setAttribute('opacity', P.nervos);
        s.terPt[i].setAttribute('cx', mx + px * .3); s.terPt[i].setAttribute('cy', my + py * .3);
        s.terPt[i].setAttribute('fill', mistura('#7f9bc4', '#FFD21F', aceso)); s.terPt[i].setAttribute('opacity', P.nervos);
        s.terPt[i].setAttribute('r', 4 + 3 * aceso * (1 - at * .5));
      });
      const L = 2 * Math.PI * (A + 22), sg = clamp(P.sinal);
      s.anelLuz.forEach(n => { n.setAttribute('stroke-dasharray', `${L / 2 * sg} ${L}`); n.setAttribute('opacity', sg <= 0 ? 0 : sg < 1 ? 1 : .25 + .5 * at);
        n.style.display = P.nervos > .05 ? '' : 'none'; });
      s.anel.setAttribute('opacity', .55 * P.nervos);
    },
  };

  /* PELE: trecho de pele com centenas de cromatóforos (amarelos, vermelhos, marrons) sobre a base clara.
     abertura: todos; onda (0→1): abertura que se espalha do centro (ox, oy em fração) — a cor muda em toda a pele. */
  PRIM.pele = {
    props: { abertura: 0, onda: 0 },
    criar(g, e, ctx) {
      const r = semente(e.semente || 3), w = e.w, h = e.h, s = { w, h, pts: [] };
      const clip = el('clipPath', { id: ctx.uid('clip') }, ctx.defs);
      el('rect', { x: -w / 2, y: -h / 2, width: w, height: h, rx: e.raio || 36 }, clip);
      const base = el('linearGradient', { id: ctx.uid('base'), x1: 0, y1: 0, x2: 0, y2: 1 }, ctx.defs);
      el('stop', { offset: '0%', 'stop-color': '#d9c7ad' }, base); el('stop', { offset: '100%', 'stop-color': '#b8a48a' }, base);
      const gg = el('g', { 'clip-path': `url(#${clip.id})` }, g);
      el('rect', { x: -w / 2, y: -h / 2, width: w, height: h, fill: `url(#${base.id})` }, gg);
      s.cam = el('g', {}, gg);
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
        const k = EASE.saida(clamp(Math.max(P.abertura, w) - p.j * .08));
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
    props: { brilho: 0, oscila: 0 },
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
      const ph = 2 * Math.PI * ((e.x - (e.campo_x0 || 0)) / (e.campo_lambda || 1e9) - (e.freq || 0) * t);
      s.gir.setAttribute('transform', `rotate(${(e.angulo_base || 0) + P.oscila * Math.sin(ph)})`);
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
        const v = Math.sin(2 * Math.PI * ((q.x + e.x - (e.campo_x0 ?? e.x - e.w / 2)) / e.lambda - (e.freq || 0) * t)) * (e.altura || 90) * P.amplitude;
        q.l.setAttribute('y2', -v); q.p.setAttribute('transform', `translate(${q.x},${-v}) rotate(${v >= 0 ? 180 : 0})`);
        q.p.setAttribute('opacity', Math.abs(v) > 14 ? 1 : 0); q.l.setAttribute('opacity', .35 + .65 * Math.abs(v) / (e.altura || 90));
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
    ESTADO = { spec, itens, rotulos, cab, cabN, cabT, pontos, leg, opc, mostraCab: spec.cabecalho !== false };
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
