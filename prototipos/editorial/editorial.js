/* COMPONENTES EDITORIAIS DO CORINGA — protótipo isolado (Etapa 3, frente B, 13/11/2026). Não ligado ao template.
 *
 * Cinco componentes, todos com o mesmo contrato do template atual: carregar(spec) monta; seek(t) desenha o quadro t do
 * zero (determinístico). Sem GSAP e sem mapas raster: a coreografia de referência veio dos componentes Apache-2.0 do
 * HyperFrames (titlecard-lockup, headline-slam + editorial-flash-overlay, nyc-paris-flight/north-korea-locked-down,
 * vox-annotate + lt-kicker-name, logo-brand-close) — reescrita aqui, nada copiado (ver NOTICE.md).
 *
 * spec = { componente, duracao, fundo: {tipo: 'imagem'|'oceano'|'escuro', src}, props: {...} }
 */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg', W = 1080, H = 1920, Y = '#FFD21F';
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, k) => a + (b - a) * k;
  const E = {
    saida: k => 1 - Math.pow(1 - k, 3), suave: k => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2,
    expo: k => k >= 1 ? 1 : 1 - Math.pow(2, -10 * k), mola: k => { const c1 = 1.5, c3 = c1 + 1; return 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); },
  };
  const fase = (t, a, d, e = 'saida') => E[e](clamp((t - a) / d));          // 0→1 entre a e a+d
  const h = (tag, at = {}, pai, html) => { const n = document.createElement(tag); for (const k in at) n.setAttribute(k, at[k]); if (html != null) n.innerHTML = html; if (pai) pai.appendChild(n); return n; };
  const s = (tag, at = {}, pai) => { const n = document.createElementNS(NS, tag); for (const k in at) n.setAttribute(k, at[k]); if (pai) pai.appendChild(n); return n; };
  const marcar = txt => String(txt).replace(/\*([^*]+)\*/g, '<em>$1</em>').replace(/\n/g, '<br>');   // *palavra* = destaque
  function semente(x) { let a = x >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function caber(n, maxW, maxFs, minFs) {               // maior corpo que cabe na largura (determinístico)
    // mede a largura do CONTEÚDO (Range sobre o texto), não a da caixa
    n.style.whiteSpace = 'nowrap';
    const larg = () => { const r = document.createRange(); r.selectNodeContents(n); return r.getBoundingClientRect().width; };
    let fs = maxFs; n.style.fontSize = fs + 'px';
    while (fs > minFs && larg() > maxW) { fs -= 2; n.style.fontSize = fs + 'px'; }
    return fs;
  }
  // traço "à mão": círculo de 1,15 volta com irregularidade (vox-annotate/north-korea usam o mesmo gesto)
  function rabisco(cx, cy, rx, ry, seed) {
    const r = semente(seed), pts = [], n = 46;
    for (let i = 0; i <= n; i++) { const a = -2.2 + i / n * Math.PI * 2 * 1.15, j = 1 + (r() - .5) * .07 + .05 * Math.sin(i * .5);
      pts.push(`${(cx + Math.cos(a) * rx * j).toFixed(1)},${(cy + Math.sin(a) * ry * j * (1 + i / n * .08)).toFixed(1)}`); }
    return 'M' + pts.join(' L');
  }

  const mistura2 = k => `rgb(${Math.round(lerp(22, 44, k))},${Math.round(lerp(32, 42, k))},${Math.round(lerp(46, 40, k))})`;   // país do destino: um tom mais quente
  // ───────────── fundos ─────────────
  const FUNDO = {
    imagem(raiz, f) {
      const img = h('div', { class: 'fundo-img' }, raiz); img.style.backgroundImage = `url(${f.src})`;
      return t => { const k = t / (f.dur || 8); img.style.transform = `scale(${lerp(f.esc0 ?? 1.04, f.esc1 ?? 1.12, k)}) translate(${lerp(0, f.pan ?? -14, k)}px,0)`;
        img.style.filter = `blur(${f.blur ? f.blur(t) : 0}px) brightness(${f.brilho ? f.brilho(t) : 1})`; };
    },
    oceano(raiz, f) {                                   // B-roll gerado: água funda, raios de luz e partículas em suspensão
      const sv = s('svg', { viewBox: `0 0 ${W} ${H}`, class: 'fundo-svg' }, raiz), r = semente(f.semente || 3);
      const d = s('defs', {}, sv), g = s('linearGradient', { id: 'agua', x1: 0, y1: 0, x2: 0, y2: 1 }, d);
      [['0%', '#0f4a66'], ['35%', '#08283f'], ['100%', '#020810']].forEach(([o, c]) => s('stop', { offset: o, 'stop-color': c }, g));
      const fb = s('filter', { id: 'fb', x: '-50%', y: '-50%', width: '200%', height: '200%' }, d); s('feGaussianBlur', { stdDeviation: 22 }, fb);
      const fp = s('filter', { id: 'fp' }, d); s('feGaussianBlur', { stdDeviation: 1.6 }, fp);
      s('rect', { width: W, height: H, fill: 'url(#agua)' }, sv);
      const raios = Array.from({ length: 7 }, (_, i) => ({ x: 80 + i * 150 + r() * 60, w: 50 + r() * 90, ph: r() * 6,
        n: s('polygon', { fill: 'rgba(170,225,255,.10)', filter: 'url(#fb)' }, sv) }));
      const part = Array.from({ length: 110 }, () => ({ x: r() * W, y: r() * H, z: .3 + r() * .7, ph: r() * 6,
        n: s('circle', { fill: 'rgba(200,230,255,.55)', filter: 'url(#fp)' }, sv) }));
      return t => {
        raios.forEach(q => { const sw = Math.sin(t * .35 + q.ph) * 40; q.n.setAttribute('points', `${q.x},-40 ${q.x + q.w},-40 ${q.x + q.w * 2.6 + sw},1500 ${q.x - q.w * .8 + sw},1500`);
          q.n.setAttribute('opacity', .55 + .45 * Math.sin(t * .6 + q.ph)); });
        part.forEach(q => { const y = ((q.y - t * 14 * q.z) % H + H) % H; q.n.setAttribute('cx', q.x + Math.sin(t * .4 + q.ph) * 10 * q.z);
          q.n.setAttribute('cy', y); q.n.setAttribute('r', 1 + 2.4 * q.z); q.n.setAttribute('opacity', .25 + .5 * q.z); });
        sv.style.transform = `scale(${1.03 + t * .006})`;
      };
    },
    escuro(raiz) { h('div', { class: 'fundo-escuro' }, raiz); return () => {}; },
  };

  // ───────────── componentes ─────────────
  const C = {};

  /* 1. ABERTURA documental (ref. titlecard-lockup): kicker mono de contexto, título em máscara por linha, traço amarelo
        que se desenha e uma linha de apoio. Pensado para a 1ª imagem real do acervo. */
  C.abertura = (raiz, p) => {
    const b = h('div', { class: 'ab' }, raiz);
    const k = h('div', { class: 'ab-k' }, b, p.kicker || '');
    const tt = h('h1', { class: 'ab-t' }, b);
    const linhas = String(p.titulo).split('\n').map(l => { const m = h('span', { class: 'mask' }, tt); return h('span', { class: 'ln' }, m, marcar(l)); });
    caber(tt, 840, p.corpo || 112, 64);
    const rg = h('i', { class: 'ab-r' }, b);
    const sub = p.apoio ? h('div', { class: 'ab-s' }, b, marcar(p.apoio)) : null;
    return t => {
      const a = fase(t, .25, .5); k.style.opacity = a; k.style.transform = `translateY(${(1 - a) * 18}px)`;
      linhas.forEach((l, i) => { const q = fase(t, .5 + i * .13, .65, 'expo'); l.style.transform = `translateY(${(1 - q) * 105}%)`; });
      rg.style.transform = `scaleX(${fase(t, 1.05 + linhas.length * .1, .6, 'suave')})`;
      if (sub) { const q = fase(t, 1.4, .5); sub.style.opacity = q; sub.style.transform = `translateY(${(1 - q) * 12}px)`; }
      b.style.transform = `translateY(${-t * 4}px)`;                                  // deriva lenta, quase imperceptível
    };
  };

  /* 2. REVELAÇÃO editorial (ref. headline-slam + editorial-flash-overlay + marker-highlight): clarão curto, frase que
        "assenta" com 3 quadros de tremor, marcador desenhado na palavra-chave e um dado de apoio. Para clímax sem esquema. */
  C.revelacao = (raiz, p) => {
    const fl = h('div', { class: 'flash' }, raiz), vu = h('div', { class: 'veu' }, raiz);
    const b = h('div', { class: 'rv' }, raiz);
    const tag = h('div', { class: 'rv-tag' }, b, p.rotulo || 'A RESPOSTA');
    const fr = h('div', { class: 'rv-f' }, b, marcar(p.frase)); caber(fr, 780, p.corpo || 104, 56);
    const marc = [...fr.querySelectorAll('em')].map(em => { const m = h('i', { class: 'marca' }); em.prepend(m); return m; });
    const dd = p.dado ? h('div', { class: 'rv-d' }, b, marcar(p.dado)) : null;
    const t0 = p.em ?? .3;
    return t => {
      fl.style.opacity = t < t0 ? 0 : .55 * (1 - fase(t, t0, .45, 'saida'));
      vu.style.opacity = .25 + .5 * fase(t, t0, .3);
      const q = fase(t, t0, .24, 'saida'), tr = t > t0 + .24 && t < t0 + .34 ? [7, -6, 3][Math.floor((t - t0 - .24) / .0334) % 3] : 0;
      fr.style.transform = `translateX(${tr}px) scale(${lerp(1.34, 1, q)})`; fr.style.opacity = t < t0 ? 0 : 1;
      tag.style.opacity = fase(t, t0 + .1, .3); tag.style.transform = `translateY(${(1 - fase(t, t0 + .1, .3)) * 10}px)`;
      marc.forEach((m, i) => { const q = fase(t, t0 + .55 + i * .15, .4, 'suave'); m.style.transform = `scaleX(${q}) skewX(-8deg)`;
        m.parentElement.style.color = q > .45 ? '#05080f' : '#FFD21F'; });   // amarelo antes do marcador, escuro sobre ele
      if (dd) { const z = fase(t, t0 + 1.0, .45); dd.style.opacity = z; dd.style.transform = `translateY(${(1 - z) * 14}px)`; }
      return { blur: 6 * fase(t, t0, .3), brilho: 1 - .35 * fase(t, t0, .3) };
    };
  };

  /* 3. MAPA de rota (ref. nyc-paris-flight + north-korea-locked-down, sem imagem raster): países vetoriais (Natural Earth,
        domínio público), aproximação de câmera, arco de grande círculo que se desenha com a ponta acesa, rabisco no destino,
        etiqueta que salta e distância contada a partir das coordenadas (não digitada). */
  C.mapa = (raiz, p) => {
    const topo = window.MUNDO, paises = topojson.feature(topo, topo.objects.countries).features;
    const sv = s('svg', { viewBox: `0 0 ${W} ${H}`, class: 'mapa' }, raiz);
    const d = s('defs', {}, sv), fg = s('filter', { id: 'mglow', x: '-50%', y: '-50%', width: '200%', height: '200%' }, d);
    s('feGaussianBlur', { stdDeviation: 6, result: 'b' }, fg); const mm = s('feMerge', {}, fg); s('feMergeNode', { in: 'b' }, mm); s('feMergeNode', { in: 'SourceGraphic' }, mm);
    s('rect', { width: W, height: H, fill: '#060d18' }, sv);
    const gGrat = s('path', { fill: 'none', stroke: 'rgba(255,255,255,.05)', 'stroke-width': 1 }, sv);
    const gTerra = s('g', {}, sv);
    const nos = paises.map(f => s('path', { fill: '#16202e', stroke: '#2a3a52', 'stroke-width': 1.2 }, gTerra));
    const A = [p.origem.lon, p.origem.lat], B = [p.destino.lon, p.destino.lat];
    const destinoPais = paises.findIndex(f => d3.geoContains(f, B));
    const arco = s('path', { fill: 'none', stroke: Y, 'stroke-width': 5, 'stroke-linecap': 'round', filter: 'url(#mglow)' }, sv);
    const arcoBase = s('path', { fill: 'none', stroke: 'rgba(255,210,31,.25)', 'stroke-width': 3, 'stroke-dasharray': '2 9', 'stroke-linecap': 'round' }, sv);
    sv.insertBefore(arcoBase, arco);
    const ponta = s('circle', { r: 9, fill: '#fff6c8', filter: 'url(#mglow)' }, sv);
    const pA = s('circle', { r: 8, fill: '#fff', stroke: '#060d18', 'stroke-width': 3 }, sv);
    const pB = s('circle', { r: 10, fill: Y, stroke: '#060d18', 'stroke-width': 3 }, sv);
    const rab = s('path', { fill: 'none', stroke: '#ff4d3d', 'stroke-width': 6, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, sv);
    const lA = h('div', { class: 'mp-pin' }, raiz, p.origem.nome);
    const card = h('div', { class: 'mp-card' }, raiz, `<b>${p.destino.kicker || 'DESTINO'}</b><span>${p.destino.nome}</span>`);
    const km = Math.round(d3.geoDistance(A, B) * 6371);                       // raio médio da Terra; arredondado
    const dist = h('div', { class: 'mp-dist' }, raiz, `<span class="n">0</span><span class="u">km em linha reta</span>`);
    const tit = p.titulo ? h('div', { class: 'mp-tit' }, raiz, marcar(p.titulo)) : null;
    const interp = d3.geoInterpolate(A, B), rota = d3.range(0, 1.0001, .02).map(interp);
    // câmera: do enquadramento largo (contexto) ao enquadramento da rota
    const caixa = (pts, m) => ({ type: 'MultiPoint', coordinates: pts.map(([x, y]) => [x, y]) });
    const largo = d3.geoMercator().fitExtent([[60, 380], [1020, 1120]], p.largo ? { type: 'MultiPoint', coordinates: p.largo } : caixa([A, B]));
    const perto = d3.geoMercator().fitExtent([[170, 640], [900, 1000]], caixa(rota));
    const s0 = largo.scale(), s1 = perto.scale(), c0 = largo.invert([540, 750]), c1 = perto.invert([540, 770]);
    const grat = d3.geoGraticule10();
    p.dist_km = km;
    return t => {
      const z = fase(t, .2, 1.6, 'suave'), proj = d3.geoMercator().scale(s0 * Math.pow(s1 / s0, z)).center(d3.geoInterpolate(c0, c1)(z)).translate([540, 760]);
      const pth = d3.geoPath(proj);
      gGrat.setAttribute('d', pth(grat));
      nos.forEach((n, i) => { n.setAttribute('d', pth(paises[i]) || ''); if (i === destinoPais) n.setAttribute('fill', mistura2(fase(t, 2.6, .6))); });
      const pa = proj(A), pb = proj(B);
      pA.setAttribute('cx', pa[0]); pA.setAttribute('cy', pa[1]); pA.setAttribute('opacity', fase(t, 1.4, .3));
      lA.style.left = pa[0] + 'px'; lA.style.top = (pa[1] - 64) + 'px'; lA.style.opacity = fase(t, 1.5, .3);
      const linha = pth({ type: 'LineString', coordinates: rota });
      arco.setAttribute('d', linha); arcoBase.setAttribute('d', linha);
      const L = arco.getTotalLength(), q = fase(t, 1.8, 1.4, 'suave');
      arco.setAttribute('stroke-dasharray', `${L * q} ${L}`); arcoBase.setAttribute('opacity', fase(t, 1.6, .3));
      if (q > 0 && q < 1) { const pt = arco.getPointAtLength(L * q); ponta.setAttribute('cx', pt.x); ponta.setAttribute('cy', pt.y); ponta.setAttribute('opacity', 1); } else ponta.setAttribute('opacity', 0);
      pB.setAttribute('cx', pb[0]); pB.setAttribute('cy', pb[1]); pB.setAttribute('r', 10 * E.mola(fase(t, 3.15, .4, 'saida')));
      rab.setAttribute('d', rabisco(pb[0], pb[1], 70, 58, 11)); const RL = rab.getTotalLength(), rq = fase(t, 3.3, .6, 'suave');
      rab.setAttribute('stroke-dasharray', `${RL * rq} ${RL}`); rab.setAttribute('opacity', rq > 0 ? 1 : 0);
      const cq = fase(t, 3.55, .45), cw = card.offsetWidth, dir = pb[0] + 80 + cw <= 930;        // fora da coluna de botões
      const cx = dir ? pb[0] + 80 : (pb[0] - 80 - cw >= 50 ? pb[0] - 80 - cw : Math.max(50, Math.min(pb[0] + 80, 930 - cw)));
      card.style.left = cx + 'px'; card.style.top = (pb[1] - 52) + 'px'; card.style.transformOrigin = cx > pb[0] ? '0 50%' : '100% 50%';
      card.style.opacity = cq; card.style.transform = `scale(${lerp(.7, 1, E.mola(cq))})`;
      dist.querySelector('.n').textContent = Math.round(km * q).toLocaleString('pt-BR'); dist.style.opacity = fase(t, 1.8, .3);
      if (tit) tit.style.opacity = fase(t, .3, .5);
    };
  };

  /* 4. ETIQUETA contextual (ref. vox-annotate + lt-kicker-name): anel desenhado à mão no ponto, conector fino que se
        desenha até a etiqueta, faixa de tipo (LUGAR · PESSOA · OBJETO · DATA · ILUSTRAÇÃO), nome forte e detalhe em mono. */
  C.etiqueta = (raiz, p) => {
    const sv = s('svg', { viewBox: `0 0 ${W} ${H}`, class: 'et-svg' }, raiz);
    const [x, y] = p.alvo, R = p.raio || 70, [lx, ly] = p.ancora;
    const anel = s('path', { d: rabisco(x, y, R, R * .9, p.semente || 5), fill: 'none', stroke: Y, 'stroke-width': 5, 'stroke-linecap': 'round' }, sv);
    const ang = Math.atan2(ly - y, lx - x), ex = x + Math.cos(ang) * R, ey = y + Math.sin(ang) * R * .9;
    const con = s('path', { d: `M${ex},${ey} L${lx},${ly} L${lx + (p.lado === 'esq' ? -40 : 40)},${ly}`, fill: 'none', stroke: 'rgba(255,255,255,.85)', 'stroke-width': 2.5 }, sv);
    const pto = s('circle', { cx: lx + (p.lado === 'esq' ? -40 : 40), cy: ly, r: 5, fill: Y }, sv);
    const b = h('div', { class: 'et ' + (p.lado === 'esq' ? 'esq' : 'dir') }, raiz);
    b.style.top = (ly - 34) + 'px'; if (p.lado === 'esq') b.style.right = (W - lx + 56) + 'px'; else b.style.left = (lx + 56) + 'px';
    const tp = h('div', { class: 'et-tipo' }, b, `<span>${p.tipo}</span>`), nm = h('div', { class: 'et-nome' }, b, `<span>${marcar(p.nome)}</span>`);
    const sub = h('i', { class: 'et-sub' }, b), dt = p.detalhe ? h('div', { class: 'et-det' }, b, p.detalhe) : null;
    const AL = anel.getTotalLength(), CL = con.getTotalLength(), fim = p.dur || 4;
    return t => {
      const sai = 1 - fase(t, fim - .45, .4, 'suave');
      anel.setAttribute('stroke-dasharray', `${AL * fase(t, .15, .6, 'suave')} ${AL}`);
      con.setAttribute('stroke-dasharray', `${CL * fase(t, .55, .4, 'suave')} ${CL}`);
      pto.setAttribute('r', 5 * E.mola(fase(t, .9, .3)));
      tp.firstChild.style.transform = `translateY(${(1 - fase(t, .85, .35, 'expo')) * 110}%)`;
      nm.firstChild.style.transform = `translateY(${(1 - fase(t, .95, .45, 'expo')) * 110}%)`;
      sub.style.transform = `scaleX(${fase(t, 1.15, .45, 'suave')})`;
      if (dt) dt.style.opacity = fase(t, 1.35, .4);
      sv.style.opacity = b.style.opacity = sai;
    };
  };

  /* 5. ENCERRAMENTO (ref. logo-brand-close; sem botão de CTA — identidade, não anúncio): a resposta em uma linha,
        que sobe e dá lugar à marca letra a letra com o ponto amarelo por último, o mascote e as fontes. */
  C.encerramento = (raiz, p) => {
    const rs = h('div', { class: 'en-r' }, raiz, marcar(p.resumo)); caber(rs, 780, 66, 40);
    const mk = h('div', { class: 'en-m' }, raiz);
    const letras = [...(p.marca || 'CORINGA EXPLICA')].map(c => h('span', { class: c === ' ' ? 'esp' : '' }, mk, c === ' ' ? '&nbsp;' : c));
    const ponto = h('span', { class: 'pt' }, mk, '.'); caber(mk, 780, 92, 56);
    const rg = h('i', { class: 'en-rg' }, raiz), hd = h('div', { class: 'en-h' }, raiz, p.handle || '@coringa.explica');
    const ms = p.mascote ? h('img', { class: 'en-masc', src: p.mascote }, raiz) : null;
    const ft = p.fontes ? h('div', { class: 'en-f' }, raiz, 'FONTES · ' + p.fontes) : null;
    return t => {
      const a = fase(t, .1, .5), sobe = fase(t, 1.7, .6, 'suave');
      rs.style.opacity = a * (1 - sobe); rs.style.transform = `translateY(${(1 - a) * 16 - sobe * 60}px)`;
      letras.forEach((l, i) => { const q = fase(t, 2.0 + i * .035, .45, 'expo'); l.style.opacity = q; l.style.transform = `translateY(${(1 - q) * 40}px)`; });
      const pq = fase(t, 2.0 + letras.length * .035 + .1, .4, 'saida'); ponto.style.opacity = pq > 0 ? 1 : 0; ponto.style.transform = `translateY(${(1 - E.mola(pq)) * -60}px)`;
      rg.style.transform = `scaleX(${fase(t, 2.9, .5, 'suave')})`;
      hd.style.opacity = fase(t, 3.1, .4);
      if (ms) { const q = fase(t, 2.3, .6, 'expo'); ms.style.opacity = q; ms.style.transform = `translateY(${(1 - q) * 60}px) scale(${lerp(.9, 1, q)})`; }
      if (ft) ft.style.opacity = fase(t, 3.4, .4);
    };
  };

  // ───────────── montagem ─────────────
  let ESTADO = null;
  function carregar(spec) {
    if (!C[spec.componente]) throw new Error('componente desconhecido: ' + spec.componente);
    const raiz = document.getElementById('palco'); raiz.innerHTML = '';
    const f = Object.assign({ dur: spec.duracao }, spec.fundo || { tipo: 'escuro' });
    const camF = h('div', { class: 'camada-fundo' }, raiz), camC = h('div', { class: 'camada' }, raiz);
    const fundo = FUNDO[f.tipo](camF, f);
    const desenha = C[spec.componente](camC, Object.assign({ dur: spec.duracao }, spec.props));
    ESTADO = { spec, f, fundo, desenha };
    seek(0); return true;
  }
  function seek(t) {
    if (!ESTADO) return;
    const efeito = ESTADO.desenha(t) || {};
    if (efeito.blur != null) { ESTADO.f.blur = () => efeito.blur; ESTADO.f.brilho = () => efeito.brilho; }
    ESTADO.fundo(t);
  }
  function medir() {                       // extensão real de cada texto visível (Range), para zona segura e corpo mínimo
    const out = [], it = document.createNodeIterator(document.querySelector('#palco .camada'), NodeFilter.SHOW_TEXT);
    let n;
    while ((n = it.nextNode())) {
      if (!n.textContent.trim()) continue;
      const r = document.createRange(); r.selectNodeContents(n); const b = r.getBoundingClientRect();
      if (!b.width || !b.height) continue;
      let op = 1; for (let e = n.parentElement; e && e.id !== 'palco'; e = e.parentElement) op *= +getComputedStyle(e).opacity;
      out.push({ x: b.x, y: b.y, w: b.width, h: b.height, fs: parseFloat(getComputedStyle(n.parentElement).fontSize), op, txt: n.textContent.trim().slice(0, 30) });
    }
    return out;
  }
  window.EDITORIAL = { carregar, seek, medir, componentes: () => Object.keys(C) };
  window.seek = seek;
})();
