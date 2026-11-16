/* DOCUMENTAL V3 — composições guiadas pelo contrato de direção (src/v2/diretor.py).
 *
 * doc.plano   — a FOTO é a cena: câmera dirigida entre enquadramentos (coordenadas da própria foto), anotações no estilo
 *               Vox ancoradas em regiões que a visão localizou (círculo, contorno, foco, seta, rótulo) e que acompanham a
 *               câmera, tratamento de cor para dar unidade a fontes diferentes, selo de função documental (REGISTRO,
 *               CONTEXTO, DOCUMENTO, ESQUEMA, RECONSTRUÇÃO) e crédito. Nada de cartão grande cobrindo a foto.
 * doc.eclusa  — mecanismo em corte longitudinal, pensado para o quadro vertical: três degraus reais (câmaras em
 *               sequência), câmera que acompanha o navio, comportas que só abrem com os níveis iguais, água que vem do
 *               lago pelo aqueduto (gravidade) e rótulos presos aos objetos. Rotulado como ESQUEMA.
 *
 * Padrões vindos do catálogo HyperFrames (Apache-2.0, heygen-com/hyperframes): círculo desenhado à mão em dois traços
 * (hw-callout-circle), foco com máscara esfumada (yt-feather-highlight), granulação/vinheta de tratamento
 * (grain-overlay, vignette). Reescritos aqui para o tempo do palco V2 (seek determinístico, sem CDN, sem CSS global). */
(function () {
  const { esc, hl, clamp, lerp, eo, eo5, eio } = V2.U;
  const W = 1080, H = 1920, AMARELO = '#FFD21F';
  const SELO_COR = { REGISTRO: '#3FD0E0', CONTEXTO: '#FFD21F', DOCUMENTO: '#F2E6C9', ESQUEMA: '#7FE3F0', 'RECONSTRUÇÃO': '#FF8A5C', 'REPRESENTAÇÃO HISTÓRICA': '#F2E6C9' };
  const TRAT = {
    atual: 'saturate(.84) contrast(1.07) brightness(.95) sepia(.05)',
    arquivo: 'contrast(1.08) brightness(.97)',
    gravura: 'contrast(1.06) brightness(.98)',
    satelite: 'saturate(.9) contrast(1.05)',
  };
  // granulação determinística: ruído fixo (gerado uma vez por página) deslocado pelo número do quadro
  let RUIDO = null;
  function ruido() {
    if (RUIDO) return RUIDO;
    const c = document.createElement('canvas'); c.width = c.height = 256;
    const g = c.getContext('2d'), im = g.createImageData(256, 256);
    let s = 1234567;
    for (let i = 0; i < im.data.length; i += 4) { s = (s * 1103515245 + 12345) & 0x7fffffff; const v = 128 + ((s >> 8) % 90) - 45; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; }
    g.putImageData(im, 0, 0); RUIDO = c.toDataURL('image/png'); return RUIDO;
  }
  const selo = (p) => p && p.funcao ? `<div class="abs dp-selo" data-g="selo" style="left:60px;top:345px;max-width:880px;display:flex;align-items:center;gap:14px;font-family:var(--f-dado);font-weight:700;font-size:28px;letter-spacing:2px;text-transform:uppercase;color:#fff;text-shadow:0 2px 10px rgba(0,0,0,.85)">
      <span style="padding:5px 12px;border:2px solid ${SELO_COR[p.funcao] || '#fff'};color:${SELO_COR[p.funcao] || '#fff'};background:rgba(8,10,14,.55)">${esc(p.funcao)}</span><span class="tx">${esc(p.texto || '')}</span></div>` : '';
  const credito = (c) => c ? `<div class="abs dp-cred" data-g="credito" data-opcional="1" style="right:60px;top:1132px;max-width:680px;text-align:right;font-family:var(--f-dado);font-size:26px;color:rgba(255,255,255,.62);text-shadow:0 1px 6px #000">${esc(c)}</div>` : '';

  // câmera: quadros-chave [{t, caixa:[x,y,w,h] (0–1 da imagem)}] → {cx, cy, w, h} em pixels da imagem no instante tl
  /* Câmera do doc.plano (Plano Mestre §4). Cada enquadramento-chave vira um ESTADO {ls: log da escala, cx, cy: ponto
   * da imagem no centro de composição}. Entre chaves: escala em log e centro em linha reta (sem desvio de percurso), e a
   * posição é LIMITADA a cada quadro ao que o layout permite: em 'cobrir' a escala nunca fica abaixo da que cobre o
   * quadro e a imagem nunca descobre a borda — nem nas pontas nem NO MEIO do caminho. 'integral' (documento/mapa inteiro) pode deixar margem, de
   * propósito, sobre um fundo próprio. A caixa da direção cabe em 1080×1540 centrada em y 760 (o assunto fica acima
   * da legenda), como antes. */
  const FIT_H = 1540, CY = 760, SMAX = 1.8, BARRA = 1140;
  // limites verticais da posição (ty) para uma escala s. 'cobrir': a imagem cobre de 0 a H. 'integral': o topo nunca
  // deixa vão (ou a imagem cabe inteira) e a borda de baixo fica entre a linha da legenda (BARRA) e H: a sobra, se
  // houver, é uma barra escura de legenda embaixo — nunca em cima nem no meio do quadro.
  function faixaY(s, ih, layout) {
    if (layout !== 'integral') return [Math.min(0, H - ih * s), Math.max(0, H - ih * s)];
    return [BARRA - ih * s, Math.max(0, H - ih * s)];
  }
  function estadoCam(k, iw, ih, layout) {
    const b = { x: k.caixa[0] * iw, y: k.caixa[1] * ih, w: k.caixa[2] * iw, h: k.caixa[3] * ih };
    const bcx = b.x + b.w / 2, bcy = b.y + b.h / 2;
    const nat = Math.max(W / iw, H / ih), teto = Math.max(nat, SMAX);
    const sb = Math.min(W / b.w, FIT_H / b.h);
    // integral: nunca amplia além de SMAX (prefere margem a imagem macia); cobrir: nunca abaixo da escala que cobre
    let s = layout === 'integral' ? Math.min(sb, SMAX) : clamp(sb, nat, teto);
    // integral quase cobrindo: margem pequena parece acidente → cobre, se o assunto continuar perto do lugar dele
    if (layout === 'integral' && s < nat && s >= .82 * nat && nat <= SMAX * 1.12 && Math.abs(clamp(CY - bcy * nat, H - ih * nat, 0) + bcy * nat - CY) < 250) s = nat;
    let tx = W / 2 - bcx * s, ty = CY - bcy * s;
    // integral: prefere a composição limpa (cobrindo, ou inteira dentro do quadro) se o assunto andar < 250 px por isso
    if (layout === 'integral') { const tc = clamp(ty, Math.min(0, H - ih * s), Math.max(0, H - ih * s)); if (Math.abs(tc - ty) < 250) ty = tc; }
    const dx = W - iw * s, [lo, hi] = faixaY(s, ih, layout);
    tx = clamp(tx, Math.min(0, dx), Math.max(0, dx)); ty = clamp(ty, lo, hi);
    // imagem menor que o quadro nos dois eixos (foto pequena): fica parada, centrada e encostada no topo — mover um
    // "cartão" pela tela não é movimento de câmera
    if (layout === 'integral' && iw * s < W && ih * s < H) { tx = dx / 2; ty = clamp(0, lo, hi); }
    // estado = escala (log) + ponto da imagem que fica no centro de composição (W/2, CY): o centro anda em linha reta
    return { t: +k.t || 0, ease: k.ease, ls: Math.log(s), cx: (W / 2 - tx) / s, cy: (CY - ty) / s };
  }
  function limitar(s, cx, cy, iw, ih, layout) {      // posição dentro do que o layout permite para esta escala
    const dx = W - iw * s, [lo, hi] = faixaY(s, ih, layout);
    if (layout === 'integral' && iw * s < W && ih * s < H) return { s, tx: dx / 2, ty: clamp(0, lo, hi) };
    return { s, tx: clamp(W / 2 - cx * s, Math.min(0, dx), Math.max(0, dx)), ty: clamp(CY - cy * s, lo, hi) };
  }
  function camEm(cam, tl, iw, ih, layout) {
    const ks = (cam && cam.length ? cam : [{ t: 0, caixa: [0, 0, 1, 1] }]).map(k => estadoCam(k, iw, ih, layout));
    let a = ks[0], b = ks[0], k = 1;
    for (let i = 0; i < ks.length - 1; i++) if (tl >= ks[i].t) { a = ks[i]; b = ks[i + 1]; k = clamp((tl - a.t) / Math.max(.01, b.t - a.t)); }
    if (tl >= ks[ks.length - 1].t) { a = b = ks[ks.length - 1]; k = 1; }
    // seno in-out: pico de velocidade 1,57× a média (o cúbico dava 3×: arranque e freada bruscos)
    const e = (b.ease === 'linear' ? k : (1 - Math.cos(Math.PI * k)) / 2);
    return limitar(Math.exp(lerp(a.ls, b.ls, e)), lerp(a.cx, b.cx, e), lerp(a.cy, b.cy, e), iw, ih, layout);
  }

  // anotações: desenho em SVG de tela (traço constante) + rótulo HTML posicionado fora da região, dentro da área segura
  function anotSVG(a, i) {
    const cor = a.cor || AMARELO;
    switch (a.tipo) {
      case 'foco': return `<g class="an an${i}" data-tipo="foco"><defs><mask id="mk${i}_${a._id}"><rect width="1080" height="1920" fill="#fff"/><ellipse class="buraco" fill="#000" filter="url(#fe${i}_${a._id})"/></mask>
          <filter id="fe${i}_${a._id}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="38"/></filter></defs>
          <rect width="1080" height="1920" fill="rgba(6,8,12,.62)" mask="url(#mk${i}_${a._id})"/></g>`;
      case 'contorno': return `<g class="an an${i}" data-tipo="contorno"><rect class="t1" rx="18" fill="none" stroke="${cor}" stroke-width="7" pathLength="1" stroke-dasharray="1 1"/></g>`;
      case 'seta': return `<g class="an an${i}" data-tipo="seta"><path class="t1" fill="none" stroke="${cor}" stroke-width="9" stroke-linecap="round" pathLength="1" stroke-dasharray="1 1"/><path class="ponta" fill="${cor}"/></g>`;
      case 'ponto': return `<g class="an an${i}" data-tipo="ponto"><line class="t1" stroke="${cor}" stroke-width="5"/><circle class="c1" r="16" fill="${cor}" stroke="#0b0f17" stroke-width="5"/><circle class="c2" r="16" fill="none" stroke="${cor}" stroke-width="5"/></g>`;
      case 'trajeto': return `<g class="an an${i}" data-tipo="trajeto"><path class="t1" fill="none" stroke="${cor}" stroke-width="12" stroke-linecap="round" stroke-dasharray="2 26" opacity=".95"/><path class="t2" fill="none" stroke="${cor}" stroke-width="5" stroke-linecap="round" pathLength="1" stroke-dasharray="1 1"/><path class="ponta" fill="${cor}"/></g>`;
      default: return `<g class="an an${i}" data-tipo="circulo"><path class="t1" fill="none" stroke="${cor}" stroke-width="8" stroke-linecap="round" pathLength="1" stroke-dasharray="1 1"/>
          <path class="t2" fill="none" stroke="${cor}" stroke-width="4" stroke-linecap="round" pathLength="1" stroke-dasharray="1 1" opacity=".55"/></g>`;
    }
  }
  // elipse "à mão": começa um pouco antes do topo e passa do ponto de partida (dois traços levemente diferentes)
  function elipseMao(cx, cy, rx, ry, giro, ex) {
    const n = 40, pts = [];
    for (let k = 0; k <= n; k++) { const a = -Math.PI / 2 - .35 + giro + k / n * (Math.PI * 2 + .5); const r = 1 + ex * Math.sin(a * 3 + giro * 5); pts.push([cx + Math.cos(a) * rx * r, cy + Math.sin(a) * ry * r]); }
    return 'M' + pts.map(p => p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' L');
  }
  function pontaSeta(x0, y0, x1, y1, tam = 30) {
    const a = Math.atan2(y1 - y0, x1 - x0), p = (d, s) => [x1 - Math.cos(a + s) * d, y1 - Math.sin(a + s) * d];
    const [l, r] = [p(tam, .45), p(tam, -.45)];
    return `M${x1} ${y1} L${l[0]} ${l[1]} L${r[0]} ${r[1]} Z`;
  }

  V2.registrar({
    id: 'doc.plano', nome: 'Plano documental dirigido (foto + câmera + anotação)', tratamento: 'documental', tom: 'escuro',
    objetivo: 'Fazer a fotografia explicar: o espectador olha para onde a narração aponta, no momento em que ela aponta.',
    funcoes: ['lugar', 'pessoa', 'objeto', 'ambiente', 'documento', 'evento_historico', 'contexto'],
    params: { img: 'arquivo da foto', wh: '[largura, altura] em pixels', cam: '[{t, caixa:[x,y,w,h] 0–1}] enquadramentos-chave (da direção)',
      layout: "'cobrir' (padrão: foto/vídeo cobre o quadro, sem borda, sem encolher) | 'integral' (documento/mapa inteiro com margem intencional)",
      anot: '[{tipo: circulo|contorno|foco|seta|trajeto, caixa | de/para, t0, t1, texto ≤ 34, lado}] — caixa da VISÃO, nunca adivinhada',
      avanco: 'opcional {etapas: [{t, centro: [x, y] (fração da imagem), raio (fração da diagonal), dur}]} — revela a imagem em cor, em etapas, a partir de um ponto (propagação, expansão, inundação); o resto fica cinza. Só sobre mapa/registro que JÁ mostra a área final; selo diz ESQUEMA se a ordem é aproximada',
      tratamento: 'atual | arquivo | gravura | satelite', selo: '{funcao, texto ≤ 44}', credito: '≤ 70', entrada: 'dissolve | corte' },
    fundo: "próprio: 'cobrir' não mostra fundo; 'integral' usa mesa escura com sombra (composição intencional, não sobra acidental)",
    layout: 'foto ocupa o quadro; selo y 300; anotações e rótulos entre y 330 e 1140; legenda 1180–1440 livre',
    paleta: 'a da foto (tratamento de cor comum); anotações amarelas', animacao: 'câmera entre enquadramentos-chave com aceleração suave; anotação desenha no tempo da palavra',
    duracao: [2, 4.5, 9], limites: { texto: 34, selo: 44 }, legenda: 'livre',
    area_segura: 'rótulos x 60–1020, y 330–1140', legibilidade: 'rótulo 34 px 900 com fundo escuro',
    rejeicao: ['anotação sem caixa localizada pela visão', 'ampliação acima de 1,8× os pixels da foto', 'foto IA ou sem crédito'],
    transicao: 'dissolve',
    exemplo: { params: { img: '@lago_navios', wh: [1600, 1067], cam: [{ t: 0, caixa: [0, 0, 1, 1] }, { t: 3, caixa: [.3, .3, .4, .4] }], anot: [{ tipo: 'circulo', caixa: [.4, .4, .2, .2], t0: 1.5, texto: 'NAVIO' }], selo: { funcao: 'CONTEXTO', texto: 'LAGO GATÚN, 2000' } }, dur: 4, fala: 'No meio do caminho há um lago.' },
  }, (p, ctx) => {
    const [iw, ih] = p.wh || [1600, 900], LAY = p.layout === 'integral' ? 'integral' : 'cobrir', anot = (p.anot || []).map((a, k) => ({ ...a, _id: ctx.i + '_' + k }));
    // fundo próprio e intencional: 'integral' = mesa escura (documento/mapa inteiro, com margem de propósito);
    // 'cobrir' = a foto cobre o quadro inteiro, então o fundo nunca aparece (não há mais cópia desfocada da foto)
    const fundo = LAY === 'integral' ? 'background:radial-gradient(ellipse 90% 60% at 50% 40%, #23262c 0%, #121418 60%, #0a0b0d 100%)' : 'background:#0b0c0e';
    return {
      html: `<div class="abs dp-bg" data-layout="${LAY}" style="inset:0;${fundo}"></div>
        <div class="abs dp-mundo" data-ocupa="1" data-layout="${LAY}" style="left:0;top:0;width:${iw}px;height:${ih}px;transform-origin:0 0;${LAY === 'integral' ? 'box-shadow:0 18px 70px rgba(0,0,0,.7),0 0 0 1px rgba(255,255,255,.06)' : ''}">
          <img src="${(p.avanco && p.avanco.base) || p.img}" style="display:block;width:${iw}px;height:${ih}px;filter:${p.avanco && !p.avanco.base ? 'grayscale(1) brightness(.62) contrast(.9)' : (TRAT[p.tratamento] || TRAT.atual)}">
          ${p.avanco ? `<img class="dp-avanco" src="${p.img}" style="position:absolute;left:0;top:0;width:${iw}px;height:${ih}px;filter:${TRAT[p.tratamento] || TRAT.atual} saturate(1.25);clip-path:circle(0px at 0 0)">
          <div class="dp-frente" style="position:absolute;left:0;top:0;border-radius:50%;border:${Math.round(4 * iw / 1080)}px solid #ff7a1a;box-shadow:0 0 ${Math.round(28 * iw / 1080)}px #ff5a00;opacity:0"></div>` : ''}</div>
        <div class="abs dp-grao" style="inset:0;opacity:.075;mix-blend-mode:overlay;background-image:url(${ruido()});background-size:256px 256px"></div>
        <div class="abs" style="inset:0;background:radial-gradient(ellipse 85% 70% at 50% 42%, transparent 55%, rgba(0,0,0,.5) 100%)"></div>
        <div class="abs" style="left:0;right:0;top:0;height:420px;background:linear-gradient(rgba(0,0,0,.55),transparent)"></div>
        <svg class="abs dp-an" style="left:0;top:0;overflow:visible" width="1080" height="1920" viewBox="0 0 1080 1920">${anot.map(anotSVG).join('')}</svg>
        ${anot.map((a, i) => a.texto ? `<div class="abs dp-rot dr${i}" data-g="rotulo" data-txt="1" style="left:0;top:0;max-width:600px;padding:10px 18px;background:rgba(8,10,14,.82);border-left:6px solid ${a.cor || AMARELO};font-weight:900;font-size:34px;line-height:1.08;text-transform:uppercase;color:#fff;opacity:0">${hl(a.texto)}</div>` : '').join('')}
        ${selo(p.selo)}${credito(p.credito)}`,
      upd(tl, el) {
        const { s, tx, ty } = camEm(p.cam, tl, iw, ih, LAY);
        el.querySelector('.dp-mundo').style.transform = `translate(${tx}px,${ty}px) scale(${s})`;
        if (p.avanco) {                                       // V3.1-resgate: área revelada em etapas a partir de um ponto
          const E = p.avanco.etapas || [], D = Math.hypot(iw, ih);
          let cx = E.length ? E[0].centro[0] : .5, cy = E.length ? E[0].centro[1] : .5, r = 0;
          for (let j = 0; j < E.length; j++) {
            const e0 = j ? E[j - 1] : { t: E[0].t, centro: E[0].centro, raio: 0 }, e1 = E[j];
            const q = eio(clamp((tl - e1.t) / (+e1.dur || 1.6)));
            if (tl < e1.t) break;
            cx = e0.centro[0] + (e1.centro[0] - e0.centro[0]) * q; cy = e0.centro[1] + (e1.centro[1] - e0.centro[1]) * q;
            r = (e0.raio + (e1.raio - e0.raio) * q);
          }
          const R = r * D, X = cx * iw, Y = cy * ih;
          el.querySelector('.dp-avanco').style.clipPath = `circle(${R.toFixed(1)}px at ${X.toFixed(1)}px ${Y.toFixed(1)}px)`;
          const fr = el.querySelector('.dp-frente'); fr.style.width = fr.style.height = (2 * R).toFixed(1) + 'px';
          fr.style.transform = `translate(${(X - R).toFixed(1)}px,${(Y - R).toFixed(1)}px)`;
          // a frente (anel) só aparece ENQUANTO uma etapa avança, e some quando ela assenta: marca o movimento, não enfeita
          let qa = 0;
          for (const e1 of E) { const q = clamp((tl - e1.t) / (+e1.dur || 1.6)); if (q > 0 && q < 1) qa = Math.max(qa, Math.sin(Math.PI * q)); }
          fr.style.opacity = R > 2 ? .85 * qa : 0;
        }
        const P = (nx, ny) => [tx + nx * iw * s, ty + ny * ih * s];
        const e = el.querySelector('.dp-selo'); if (e) { e.style.opacity = clamp(tl / .4); }
        anot.forEach((a, i) => {
          const g = el.querySelector('.an' + i), r = el.querySelector('.dr' + i);
          const t0 = +a.t0 || 0, t1 = a.t1 == null ? 1e9 : +a.t1;
          const k = clamp((tl - t0) / (+a.desenho || .7)), sai = 1 - clamp((tl - t1) / .35);
          const vis = tl >= t0 && sai > 0;
          if (g) g.style.opacity = vis ? sai : 0;
          if (!vis) { if (r) r.style.opacity = 0; return; }
          let caixa = null;
          if (a.caixa) { const [x0, y0] = P(a.caixa[0], a.caixa[1]), [x1, y1] = P(a.caixa[0] + a.caixa[2], a.caixa[1] + a.caixa[3]); caixa = { x0, y0, x1, y1, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, w: x1 - x0, h: y1 - y0 }; }
          if (a.tipo === 'foco' && caixa) {
            const b = g.querySelector('.buraco'); b.setAttribute('cx', caixa.cx); b.setAttribute('cy', caixa.cy); b.setAttribute('rx', caixa.w * .62 + 40); b.setAttribute('ry', caixa.h * .62 + 40);
            g.style.opacity = (vis ? sai : 0) * eo(k);
          } else if (a.tipo === 'contorno' && caixa) {
            const t = g.querySelector('.t1'), m = 14;
            t.setAttribute('x', caixa.x0 - m); t.setAttribute('y', caixa.y0 - m); t.setAttribute('width', caixa.w + 2 * m); t.setAttribute('height', caixa.h + 2 * m); t.setAttribute('stroke-dashoffset', 1 - eo(k));
          } else if ((a.tipo === 'seta' || a.tipo === 'trajeto') && a.de && a.para) {
            const [x0, y0] = P(a.de[0], a.de[1]), [x1, y1] = P(a.para[0], a.para[1]);
            const mx = (x0 + x1) / 2 + (a.curva || 0) * (y1 - y0), my = (y0 + y1) / 2 - (a.curva || 0) * (x1 - x0);
            const d = `M${x0} ${y0} Q${mx} ${my} ${x1} ${y1}`;
            g.querySelectorAll('.t1,.t2').forEach(t => { t.setAttribute('d', d); });
            const t1e = g.querySelector(a.tipo === 'trajeto' ? '.t2' : '.t1'); t1e.setAttribute('stroke-dashoffset', 1 - eo(k));
            if (a.tipo === 'trajeto') g.querySelector('.t1').setAttribute('stroke-dashoffset', -tl * 60);
            const q = eo(k), bx = (1 - q) * (1 - q) * x0 + 2 * (1 - q) * q * mx + q * q * x1, by = (1 - q) * (1 - q) * y0 + 2 * (1 - q) * q * my + q * q * y1;
            const q2 = Math.max(0, q - .03), ax = (1 - q2) * (1 - q2) * x0 + 2 * (1 - q2) * q2 * mx + q2 * q2 * x1, ay = (1 - q2) * (1 - q2) * y0 + 2 * (1 - q2) * q2 * my + q2 * q2 * y1;
            g.querySelector('.ponta').setAttribute('d', k > .05 ? pontaSeta(ax, ay, bx, by, 34) : '');
            caixa = { x0: Math.min(x0, x1), y0: Math.min(y0, y1), x1: Math.max(x0, x1), y1: Math.max(y0, y1), cx: x1, cy: y1, w: Math.abs(x1 - x0), h: Math.abs(y1 - y0) };
          } else if (a.tipo === 'ponto' && caixa) {
            const c1 = g.querySelector('.c1'), c2 = g.querySelector('.c2'), q = eo5(k);
            c1.setAttribute('cx', caixa.cx); c1.setAttribute('cy', caixa.cy); c1.setAttribute('r', 16 * q);
            const ph = ((tl - t0) % 1.4) / 1.4; c2.setAttribute('cx', caixa.cx); c2.setAttribute('cy', caixa.cy); c2.setAttribute('r', 16 + ph * 46); c2.setAttribute('opacity', (1 - ph) * q);
            caixa = { x0: caixa.cx - 10, x1: caixa.cx + 10, y0: caixa.cy - 10, y1: caixa.cy + 10, cx: caixa.cx, cy: caixa.cy, w: 20, h: 20, ponto: 1 };
          } else if (caixa) {
            const rx = caixa.w / 2 * 1.12 + 22, ry = caixa.h / 2 * 1.12 + 22;
            g.querySelector('.t1').setAttribute('d', elipseMao(caixa.cx, caixa.cy, rx, ry, 0, .02)); g.querySelector('.t1').setAttribute('stroke-dashoffset', 1 - eo(k));
            g.querySelector('.t2').setAttribute('d', elipseMao(caixa.cx + 3, caixa.cy - 2, rx * 1.03, ry * .98, .2, .03)); g.querySelector('.t2').setAttribute('stroke-dashoffset', 1 - eo(clamp(k * 1.15 - .15)));
          }
          if (r && caixa) {                                       // rótulo: acima, abaixo ou ao lado, sempre na área segura
            const bw = r.offsetWidth, bh = r.offsetHeight, gap = 34;
            const cand = a.lado === 'abaixo' ? [[caixa.cx - bw / 2, caixa.y1 + gap]] : a.lado === 'acima' ? [[caixa.cx - bw / 2, caixa.y0 - gap - bh]] : [];
            cand.push([caixa.cx - bw / 2, caixa.y0 - gap - bh], [caixa.cx - bw / 2, caixa.y1 + gap], [caixa.x1 + gap, caixa.cy - bh / 2], [caixa.x0 - gap - bw, caixa.cy - bh / 2]);
            const ok = ([x, y]) => x >= 60 && x + bw <= 1020 && y >= 400 && y + bh <= 1140;
            let [x, y] = cand.find(ok) || cand[0];
            x = clamp(x, 60, 1020 - bw); y = clamp(y, 400, 1140 - bh);
            r.style.transform = `translate(${x}px,${y + (1 - eo5(clamp((tl - t0 - .25) / .4))) * 16}px)`;
            if (caixa.ponto) { const ln = g.querySelector('.t1'); const lx = clamp(caixa.cx, x, x + bw), ly = y + bh / 2 < caixa.cy ? y + bh : y;
              ln.setAttribute('x1', caixa.cx); ln.setAttribute('y1', caixa.cy); ln.setAttribute('x2', lx); ln.setAttribute('y2', ly); ln.setAttribute('opacity', clamp((tl - t0 - .2) / .3)); }
            r.style.opacity = clamp((tl - t0 - .25) / .3) * sai;
          }
        });
      },
      textos: () => anot.map(a => a.texto).filter(Boolean).concat(p.selo ? [p.selo.texto] : []),
    };
  });

  /* doc.eclusa — escada de câmaras em corte, para o quadro vertical */
  V2.registrar({
    id: 'doc.eclusa', nome: 'Eclusa em degraus (esquema dirigido)', tratamento: 'ciencia', tom: 'escuro',
    objetivo: 'Mostrar a sequência física: o navio entra no nível baixo, a comporta fecha, a água do lago desce por gravidade e enche a câmara, o navio sobe junto, os níveis igualam, a comporta abre e ele passa ao degrau seguinte, até o lago.',
    funcoes: ['mecanismo', 'eclusa', 'elevacao_vertical', 'agua_subindo'],
    params: { degraus: 'nº de câmaras que somam o desnível (dos fatos)', desnivel_m: 'desnível total (dos fatos)', alto: 'nome do nível alto ≤ 18', baixo: 'nome do nível baixo ≤ 18',
      tempos: '{entra, fecha, enche, boia, degraus, outro_lado}: segundos (na cena) em que a FALA chega a cada passo', outro_lado: 'bool: mostrar os degraus de descida do outro lado' },
    fundo: 'próprio (prancheta técnica)', layout: 'corte no terço de cima e no meio (y 330–1150); rótulos presos aos objetos; legenda livre',
    paleta: 'água ciano; concreto cinza-azulado; comportas amarelas; navio branco/vermelho', animacao: 'câmera acompanha o navio; recua para mostrar os degraus',
    duracao: [6, 12, 20], limites: { nome: 18 }, legenda: 'livre', area_segura: 'rótulos x 60–1020, y 330–1140', legibilidade: 'rótulos 32 px 900',
    rejeicao: ['nº de degraus ou desnível que não estão nos fatos'], transicao: 'dissolve',
    problemas_conhecidos: ['corte simplificado: as comportas de duas folhas aparecem de lado (abrir = girar para fora do plano)'],
    exemplo: { params: { degraus: 3, desnivel_m: 26, alto: 'LAGO GATÚN', baixo: 'MAR', tempos: { entra: 0, fecha: 3, enche: 4.5, boia: 8, degraus: 10.5, outro_lado: 13.5 } }, dur: 16, fala: 'O navio entra, a comporta fecha, a água desce do lago e ele sobe.' },
  }, (p, ctx) => {
    const N = Math.max(1, Math.min(4, +p.degraus || 3)), D = +p.desnivel_m || 26;
    const T = Object.assign({ entra: 0, fecha: 3, enche: 4.5, boia: 8.5, degraus: 10.5, outro_lado: 13.5 }, p.tempos || {});
    // mundo: x para a direita (sobe), y para baixo. 1 degrau = DH unidades.
    const DH = 230, Y0 = 1000, CW = 640, X0 = 520, GT = 38;
    const xs = Array.from({ length: N + 1 }, (_, k) => X0 + k * CW);            // comportas
    const nivel = k => Y0 - k * DH;                                              // nível do degrau k (0 = baixo)
    const piso = k => nivel(k) + 190;
    const XL = xs[N], FIM = XL + 900;                                            // lago
    const id = ctx.i;
    const navio = `<g class="nav"><path d="M-200 -24 H200 L176 44 H-184 Z" fill="#f2f5fa" stroke="#0b0f17" stroke-width="5"/><path d="M-192 18 H192 L176 44 H-184 Z" fill="#c4302b"/>
      <rect x="70" y="-112" width="104" height="88" fill="#f7f9fc" stroke="#0b0f17" stroke-width="5"/><rect x="82" y="-100" width="80" height="16" fill="#22313f"/>
      ${[-170, -128, -86, -44, -2, 40].map((x, k) => `<rect x="${x}" y="-62" width="38" height="38" fill="${['#f0b429', '#3a86c8', '#e05a3a', '#f0b429', '#4caf7a', '#3a86c8'][k]}" stroke="#0b0f17" stroke-width="3"/>`).join('')}</g>`;
    // concreto em degraus + aqueduto dentro do maciço (do lago até o piso das câmaras)
    let mac = `M-2000 ${piso(0) + 260} H${FIM + 3000} V${piso(0) + 900} H-2000 Z`;
    let concreto = '';
    for (let k = 0; k < N; k++) concreto += `<rect x="${xs[k]}" y="${piso(k)}" width="${CW}" height="${piso(0) + 300 - piso(k)}" fill="url(#cc${id})"/>`;
    concreto += `<rect x="${XL}" y="${nivel(N) + 170}" width="${FIM + 3000 - XL}" height="${piso(0) + 300 - nivel(N) - 170}" fill="url(#rc${id})"/>`;
    const aq = `M${XL + 220} ${nivel(N) + 120} V${piso(0) + 120} H${xs[0] + 80}`;
    const saidas = Array.from({ length: N }, (_, k) => `<rect x="${xs[k] + CW / 2 - 18}" y="${piso(k)}" width="36" height="${piso(0) + 120 - piso(k)}" fill="#07141a"/>`).join('');
    const parede = k => `<rect x="${xs[k] - 18}" y="${nivel(Math.min(N, k + 1)) - 70}" width="36" height="${piso(Math.max(0, k - 1 < 0 ? 0 : k - 1)) - nivel(Math.min(N, k + 1)) + 70}" fill="#5d7387"/>`;
    const html = `<div class="abs" style="inset:0;background:radial-gradient(ellipse at 50% 30%, #12303a, #071018 70%)"></div><div class="grade"></div>
      <div class="abs de-selo" data-g="selo" style="left:60px;top:345px;display:flex;gap:14px;align-items:center;font-family:var(--f-dado);font-weight:700;font-size:28px;letter-spacing:2px;color:#fff">
        <span style="padding:5px 12px;border:2px solid #7FE3F0;color:#7FE3F0;background:rgba(8,10,14,.55)">ESQUEMA</span><span>ECLUSA · CORTE SIMPLIFICADO</span></div>
      <svg class="abs de-cv" data-ocupa="1" style="left:0;top:0;overflow:visible" width="1080" height="1920" viewBox="0 0 1080 1920">
        <defs><linearGradient id="ag${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4fd8e8" stop-opacity=".8"/><stop offset="1" stop-color="#0c6676" stop-opacity=".95"/></linearGradient>
          <pattern id="cc${id}" width="40" height="40" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="40" height="40" fill="#3a5062"/><line x1="0" y1="0" x2="0" y2="40" stroke="#445d71" stroke-width="14"/></pattern>
          <pattern id="rc${id}" width="70" height="46" patternUnits="userSpaceOnUse"><rect width="70" height="46" fill="#1f2c34"/><circle cx="16" cy="13" r="6" fill="#283842"/><circle cx="50" cy="31" r="8" fill="#283842"/></pattern></defs>
        <g class="mundo">
          <path d="${mac}" fill="url(#rc${id})"/>
          <rect x="-2000" y="${Y0}" width="${xs[0] + 2000}" height="${piso(0) + 300 - Y0}" fill="url(#ag${id})"/>
          <rect class="lago" x="${XL}" y="${nivel(N)}" width="${FIM + 3000 - XL}" height="170" fill="url(#ag${id})"/>
          ${Array.from({ length: N }, (_, k) => `<rect class="agua agua${k}" x="${xs[k]}" width="${CW}" fill="url(#ag${id})"/><path class="sup sup${k}" fill="none" stroke="#d6fbff" stroke-width="4"/>`).join('')}
          ${concreto}
          <path d="${aq}" fill="none" stroke="#07141a" stroke-width="54" stroke-linejoin="round"/>${saidas}
          <path class="fluxo" d="${aq}" fill="none" stroke="#e8fdff" stroke-width="10" stroke-linecap="round" stroke-dasharray="8 40" opacity="0"/>
          ${Array.from({ length: N }, (_, k) => `<path class="jato jato${k}" fill="none" stroke="#e8fdff" stroke-width="7" stroke-linecap="round" opacity="0"/>`).join('')}
          <g class="nv">${navio}</g>
          ${xs.map((x, k) => `<g class="cp cp${k}"><rect class="fo" x="${x - GT / 2}" y="${nivel(Math.min(N, k)) - 60}" width="${GT}" height="${(k === 0 ? piso(0) : piso(k - 1)) - nivel(Math.min(N, k)) + 60}" fill="${AMARELO}" stroke="#0b0f17" stroke-width="4"/></g>`).join('')}
          <g class="outro" opacity="0">${Array.from({ length: N }, (_, k) => `<rect x="${FIM + 200 + k * CW}" y="${nivel(N - k - 1)}" width="${CW}" height="${piso(N - k - 1) - nivel(N - k - 1)}" fill="url(#ag${id})" opacity=".45" stroke="#7FE3F0" stroke-width="4" stroke-dasharray="18 12"/>`).join('')}</g>
        </g>
        <g class="regua" opacity="0"><line class="rl" stroke="${AMARELO}" stroke-width="6"/><line class="rt" stroke="${AMARELO}" stroke-width="6"/><line class="rb" stroke="${AMARELO}" stroke-width="6"/></g>
      </svg>
      ${['r-comporta', 'r-agua', 'r-gravidade', 'r-nivel', 'r-degrau', 'r-lago', 'r-baixo', 'r-outro'].map(c => `<div class="abs de-rot ${c}" data-g="rotulo" data-txt="1" style="left:0;top:0;max-width:560px;padding:9px 16px;background:rgba(8,10,14,.84);border-left:6px solid ${AMARELO};font-weight:900;font-size:32px;line-height:1.08;text-transform:uppercase;color:#fff;opacity:0"></div>`).join('')}`;
    // ---- estado físico em função do tempo ----
    const XN = k => xs[k] + CW / 2 + 40;                                         // posição do navio na câmara k
    function estado(tl) {
      const L = Array.from({ length: N }, (_, k) => nivel(k + 1));               // câmaras começam cheias no próprio nível...
      L[0] = nivel(0);                                                            // ...a primeira começa no nível baixo (comporta aberta)
      for (let k = 1; k < N; k++) L[k] = nivel(k);                               // cada câmara k espera o navio no nível do degrau anterior
      const G = Array(N + 1).fill(0); G[0] = 1;                                   // aberta = 1
      let nx = xs[0] - 520, cam = 0, fluxo = 0, jato = -1;
      // degrau 1 em tempo real (falas), demais acelerados no trecho "degraus"
      const passo = (k, a, b, c, d, e) => {                                       // k: câmara; a entra; b fecha; c enche até d; e sai
        if (tl >= a) nx = lerp(k === 0 ? xs[0] - 520 : XN(k - 1), XN(k), eio((tl - a) / Math.max(.4, b - a)));
        if (k > 0 && tl >= a) G[k] = 1;
        if (tl >= b) G[k] = 1 - eio((tl - b) / .9);
        if (tl >= c) { const q = clamp((tl - c) / Math.max(.5, d - c)); L[k] = lerp(nivel(k), nivel(k + 1), 1 - Math.pow(1 - q, 1.8)); if (q < 1) { fluxo = 1; jato = k; } cam = k; }
        if (tl >= d) { G[k + 1] = eio((tl - d) / .9); }
        if (tl >= e && k + 1 < N) { /* o próximo passo move o navio */ }
      };
      const t1 = Math.max(T.degraus, T.boia + 2.6), t2 = Math.max(t1 + 1.6, (T.outro_lado ?? (T.degraus + 3)) + .6);
      passo(0, T.entra, T.fecha, T.enche, T.boia, T.boia + .9);
      if (tl >= T.boia + .9) { nx = lerp(XN(0), XN(1), eio((tl - T.boia - .9) / 1.6)); }
      if (N > 1) {
        const r = (t2 - t1) / (N - 1 + .4);                                       // degraus seguintes, acelerados
        for (let k = 1; k < N; k++) {
          const a = t1 + (k - 1) * r;
          if (tl >= a) { G[k] = 1 - eio((tl - a) / (r * .25)); }
          if (tl >= a + r * .2) { const q = clamp((tl - a - r * .2) / (r * .5)); L[k] = lerp(nivel(k), nivel(k + 1), 1 - Math.pow(1 - q, 1.8)); if (q < 1) { fluxo = 1; jato = k; } }
          if (tl >= a + r * .7) G[k + 1] = eio((tl - a - r * .7) / (r * .15));
          if (tl >= a + r * .8) nx = lerp(XN(k), k + 1 < N ? XN(k + 1) : XL + 420, eio((tl - a - r * .8) / (r * .45)));
        }
      }
      let k = 0; for (let j = 0; j < N; j++) if (nx > xs[j]) k = j;
      const ny = nx > XL ? nivel(N) : (nx < xs[0] ? nivel(0) : L[k]);
      return { L, G, nx, ny, fluxo, jato, k };
    }
    function camera(tl, st) {                                                     // centro/largura do mundo visível
      // perto: segue o navio na horizontal, mas NÃO sobe com ele (a câmara fica parada para a subida ser visível)
      const kk = Math.min(N - 1, st.k), meio = (nivel(kk) + nivel(kk + 1)) / 2 + 10;
      let perto = { cx: st.nx + 40, cy: st.nx < xs[0] ? nivel(0) - 20 : meio, w: 1060 };
      // "a água desce do lago": a câmera vai até a tomada d'água no lago e volta para a câmara (segue o caminho da água)
      const ida = eio((tl - T.enche) / 1.1) * (1 - eio((tl - T.enche - 2.1) / 1.1));
      const tomada = { cx: (xs[0] + CW / 2 + XL + 220) / 2, cy: (nivel(N) + piso(0)) / 2, w: XL + 220 - xs[0] + 260 };
      perto = { cx: lerp(perto.cx, tomada.cx, ida), cy: lerp(perto.cy, tomada.cy, ida), w: Math.exp(lerp(Math.log(perto.w), Math.log(tomada.w), ida)) };
      const geral = { cx: (xs[0] - 300 + XL + 500) / 2, cy: nivel(N / 2) + 60, w: XL + 800 - xs[0] + 500 };
      const tudo = { cx: (xs[0] - 300 + FIM + 200 + N * CW) / 2, cy: nivel(N / 2) + 60, w: FIM + 200 + N * CW - xs[0] + 600 };
      const z1 = eio((tl - T.degraus + .3) / 1.6), z2 = p.outro_lado === false ? 0 : eio((tl - (T.outro_lado ?? 1e9)) / 1.6);
      const a = { cx: lerp(perto.cx, geral.cx, z1), cy: lerp(perto.cy, geral.cy, z1), w: Math.exp(lerp(Math.log(perto.w), Math.log(geral.w), z1)) };
      return { cx: lerp(a.cx, tudo.cx, z2), cy: lerp(a.cy, tudo.cy, z2), w: Math.exp(lerp(Math.log(a.w), Math.log(tudo.w), z2)) };
    }
    return {
      html,
      upd(tl, el) {
        const st = estado(tl), c = camera(tl, st), s = 1080 / c.w, CY = 700;
        const tx = 540 - c.cx * s, ty = CY - c.cy * s;
        el.querySelector('.mundo').setAttribute('transform', `translate(${tx} ${ty}) scale(${s})`);
        const P = (x, y) => [tx + x * s, ty + y * s];
        for (let k = 0; k < N; k++) {
          const a = el.querySelector('.agua' + k); a.setAttribute('y', st.L[k]); a.setAttribute('height', piso(k) - st.L[k]);
          el.querySelector('.sup' + k).setAttribute('d', `M${xs[k]} ${st.L[k]} H${xs[k] + CW}`);
          const j = el.querySelector('.jato' + k), on = st.jato === k;
          j.setAttribute('opacity', on ? .9 : 0);
          if (on) { const x = xs[k] + CW / 2, ph = (tl * 3) % 1; j.setAttribute('d', `M${x - 40} ${piso(k) - 10} q 40 ${-60 - ph * 40} 80 0 M${x - 80} ${piso(k) - 30} q 80 ${-90 - ph * 30} 160 0`); }
        }
        const fl = el.querySelector('.fluxo'); fl.setAttribute('opacity', st.fluxo ? .95 : 0); fl.setAttribute('stroke-dashoffset', -tl * 220);
        for (let k = 0; k <= N; k++) { const g = el.querySelector('.cp' + k + ' .fo'); const o = st.G[k]; g.setAttribute('width', lerp(GT, 6, o)); g.setAttribute('x', xs[k] - lerp(GT, 6, o) / 2); g.setAttribute('opacity', lerp(1, .35, o)); }
        el.querySelector('.nv').setAttribute('transform', `translate(${st.nx} ${st.ny})`);
        el.querySelector('.outro').setAttribute('opacity', p.outro_lado === false ? 0 : eio((tl - (T.outro_lado ?? 1e9) - .4) / 1));
        // régua do degrau atual (do nível baixo ao nível de cima da câmara do navio)
        const k = Math.min(N - 1, st.k), [rx, ry0] = P(xs[k] + CW - 70, nivel(k)), [, ry1] = P(0, nivel(k + 1)), [, ryw] = P(0, st.L[k]);
        const rg = el.querySelector('.regua'), on = tl > T.enche - .2 && tl < T.degraus + .2;
        rg.setAttribute('opacity', on ? 1 : 0);
        rg.querySelector('.rl').setAttribute('x1', rx); rg.querySelector('.rl').setAttribute('x2', rx); rg.querySelector('.rl').setAttribute('y1', ry0); rg.querySelector('.rl').setAttribute('y2', ry1);
        rg.querySelector('.rt').setAttribute('x1', rx - 22); rg.querySelector('.rt').setAttribute('x2', rx + 22); rg.querySelector('.rt').setAttribute('y1', ry1); rg.querySelector('.rt').setAttribute('y2', ry1);
        rg.querySelector('.rb').setAttribute('x1', rx - 22); rg.querySelector('.rb').setAttribute('x2', rx + 22); rg.querySelector('.rb').setAttribute('y1', ryw); rg.querySelector('.rb').setAttribute('y2', ryw);
        // rótulos presos aos objetos
        const rot = (cls, txt, x, y, t0, t1, lado = 'acima') => {
          const r = el.querySelector('.' + cls); if (r.dataset.t !== txt) { r.innerHTML = hl(txt); r.dataset.t = txt; }
          const vis = tl >= t0 && tl < t1, bw = r.offsetWidth, bh = r.offsetHeight;
          let X = x - bw / 2, Y = lado === 'acima' ? y - bh - 30 : y + 30;
          X = clamp(X, 60, 1020 - bw); Y = clamp(Y, 400, 1140 - bh);
          r.style.transform = `translate(${X}px,${Y}px)`; r.style.opacity = vis ? clamp((tl - t0) / .3) * (1 - clamp((tl - t1 + .3) / .3)) : 0;
        };
        const [gx, gy] = P(xs[0], nivel(1) - 60);
        rot('r-comporta', 'Comporta fecha', gx, gy, T.fecha, T.enche + .4);
        const [ax, ay] = P(XL + 220, nivel(N) + 120);
        rot('r-gravidade', 'Água do lago desce por *gravidade*', Math.max(ax, 600), ay, T.enche, T.boia, 'abaixo');
        const [wx, wy] = P(xs[0] + CW / 2, piso(0) - 40);
        rot('r-agua', 'Enche a câmara', wx, wy, T.enche + 1.2, T.boia, 'abaixo');
        const [nx2, ny2] = P(xs[Math.min(N, 1)], nivel(1) + 40);
        rot('r-nivel', 'Níveis iguais: comporta abre', nx2, ny2, T.boia, T.degraus - .2, 'abaixo');
        rot('r-degrau', `${N} degraus · ${D} m`, 540, 1120, T.degraus + .8, T.outro_lado ?? 1e9, 'acima');
        const [lx, ly] = P(XL + 450, nivel(N));
        rot('r-lago', `${p.alto || 'Lago'} · +${D} m`, lx, ly, T.degraus + .8, 1e9);
        const [bx, by] = P(xs[0] - 260, Y0);
        rot('r-baixo', `${p.baixo || 'Mar'} · 0 m`, bx, by, T.degraus + .8, 1e9, 'abaixo');
        const [ox, oy] = P(FIM + 200 + N * CW / 2, nivel(N / 2));
        rot('r-outro', `E ${N} para descer`, ox, oy + 120, (T.outro_lado ?? 1e9) + .6, 1e9, 'abaixo');
        el.querySelector('.de-selo').style.opacity = clamp(tl / .4);
      },
      textos: () => ['Comporta fecha', 'Água do lago desce por gravidade', 'Enche a câmara', 'Níveis iguais: comporta abre'],
    };
  });
  /* doc.molde — como se faz um molde por cavidade: corpo coberto → decompõe → vazio → gesso injetado → escavação */
  V2.registrar({
    id: 'doc.molde', nome: 'Molde por cavidade (esquema)', tratamento: 'ciencia', tom: 'escuro',
    objetivo: 'Mostrar a sequência física: o material endurece em volta, o que estava dentro some e deixa um vazio, o vazio é preenchido e a escavação revela a forma.',
    funcoes: ['mecanismo', 'transformacao', 'molde'],
    params: { tempos: '{decompoe, vazio, gesso, escava}: segundos (na cena) pela fala', rotulos: '{camada, vazio, gesso, molde} ≤ 34' },
    fundo: 'próprio', layout: 'corte da camada de cinza y 400–1130; rótulos presos ao corte', paleta: 'cinza vulcânica marrom-acinzentada; gesso branco; vazio preto',
    animacao: 'corpo some → vazio → gesso sobe dentro do vazio → camadas caem', duracao: [4, 6, 10], limites: { rotulo: 34 }, legenda: 'livre',
    area_segura: 'y 340–1140', legibilidade: 'rótulos 32 px 900', rejeicao: ['usar para algo que não foi moldado por cavidade'], transicao: 'dissolve',
    exemplo: { params: { tempos: { decompoe: .5, vazio: 1.8, gesso: 3, escava: 5 } }, dur: 7, fala: 'A carne se decompôs na cinza dura e injetaram gesso nos vazios.' },
  }, (p, ctx) => {
    const T = Object.assign({ decompoe: .4, vazio: 1.8, gesso: 3.2, escava: 5.2 }, p.tempos || {});
    const R = Object.assign({ camada: 'Cinza endurecida', vazio: 'O corpo some: fica um vazio', gesso: 'Gesso líquido no vazio', molde: 'A forma exata da vítima' }, p.rotulos || {});
    const id = ctx.i;
    // silhueta agachada, braços cobrindo o rosto (genérica, sem identidade): cápsulas e elipses num único caminho
    const cap = (x1, y1, x2, y2, r) => { const a = Math.atan2(y2 - y1, x2 - x1), nx = -Math.sin(a) * r, ny = Math.cos(a) * r;
      return `M${x1 + nx} ${y1 + ny} L${x2 + nx} ${y2 + ny} A${r} ${r} 0 0 0 ${x2 - nx} ${y2 - ny} L${x1 - nx} ${y1 - ny} A${r} ${r} 0 0 0 ${x1 + nx} ${y1 + ny} Z`; };
    const elip = (cx, cy, rx, ry) => `M${cx - rx} ${cy} a${rx} ${ry} 0 1 0 ${2 * rx} 0 a${rx} ${ry} 0 1 0 ${-2 * rx} 0 Z`;
    const corpo = [elip(512, 700, 44, 50), cap(560, 760, 650, 880, 64), cap(545, 745, 600, 780, 40),
      cap(575, 760, 500, 690, 26), cap(500, 690, 470, 735, 22), cap(600, 770, 520, 725, 24),
      cap(650, 880, 545, 850, 40), cap(545, 850, 585, 975, 33), cap(585, 975, 520, 990, 22),
      cap(660, 895, 575, 905, 36), cap(575, 905, 640, 990, 30), cap(640, 990, 580, 1000, 20)].join(' ');
    const html = `<div class="abs" style="inset:0;background:radial-gradient(ellipse at 50% 35%, #2a2622, #0d0c0b 75%)"></div>
      <div class="abs dm-selo" data-g="selo" style="left:60px;top:345px;display:flex;gap:14px;align-items:center;font-family:var(--f-dado);font-weight:700;font-size:28px;letter-spacing:2px;color:#fff">
        <span style="padding:5px 12px;border:2px solid #7FE3F0;color:#7FE3F0;background:rgba(8,10,14,.55)">ESQUEMA</span><span>COMO O MOLDE É FEITO</span></div>
      <svg class="abs" data-ocupa="1" style="left:0;top:0" width="1080" height="1920" viewBox="0 0 1080 1920">
        <defs><pattern id="cz${id}" width="80" height="26" patternUnits="userSpaceOnUse"><rect width="80" height="26" fill="#6a6158"/><path d="M0 18 q20 -6 40 0 t40 0" stroke="#574f47" stroke-width="5" fill="none"/><circle cx="18" cy="8" r="3" fill="#7d736a"/><circle cx="58" cy="11" r="2" fill="#4b443d"/></pattern>
          <clipPath id="cp${id}"><path d="${corpo}"/></clipPath>
          <linearGradient id="gs${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#e7e2d8"/></linearGradient></defs>
        <g class="cinza"><rect x="0" y="470" width="1080" height="660" fill="url(#cz${id})"/>
          ${[540, 640, 760, 900, 1020].map(y => `<line x1="0" x2="1080" y1="${y}" y2="${y}" stroke="#4b443d" stroke-width="3" opacity=".7"/>`).join('')}
          <rect x="0" y="456" width="1080" height="16" fill="#8a8077"/></g>
        <g transform="translate(540 800) scale(1.65) translate(-590 -810)">
        <path class="vazio" d="${corpo}" fill-rule="nonzero" fill="#060505" opacity="0"/>
        <path class="carne" d="${corpo}" fill="#8c5a43"/>
        <g clip-path="url(#cp${id})"><rect class="gesso" x="300" width="500" fill="url(#gs${id})"/></g>
        <path class="molde" d="${corpo}" fill="url(#gs${id})" opacity="0"/>
        <g class="tubo" opacity="0"><rect x="600" y="430" width="26" height="210" fill="#cfd8dc" stroke="#0b0f17" stroke-width="4"/><path d="M570 430 h86 l-20 -60 h-46 z" fill="#cfd8dc" stroke="#0b0f17" stroke-width="4"/>
          <rect class="jorro" x="604" y="430" width="18" fill="#fff"/></g>
        </g>
      </svg>
      ${['dm-a', 'dm-b', 'dm-c', 'dm-d'].map(c => `<div class="abs dm-rot ${c}" data-g="rotulo" data-txt="1" style="left:0;top:0;max-width:600px;padding:9px 16px;background:rgba(8,10,14,.84);border-left:6px solid ${AMARELO};font-weight:900;font-size:32px;line-height:1.08;text-transform:uppercase;color:#fff;opacity:0"></div>`).join('')}`;
    return {
      html,
      upd(tl, el) {
        const k1 = eio((tl - T.decompoe) / Math.max(.4, T.vazio - T.decompoe));
        el.querySelector('.carne').setAttribute('opacity', 1 - k1);
        el.querySelector('.vazio').setAttribute('opacity', k1);
        const kt = clamp((tl - T.gesso + .4) / .4) * (1 - clamp((tl - T.escava + .2) / .4));
        el.querySelector('.tubo').setAttribute('opacity', kt);
        const kg = eo((tl - T.gesso) / Math.max(.6, T.escava - T.gesso - .2)), topo = lerp(1140, 600, kg);
        const g = el.querySelector('.gesso'); g.setAttribute('y', topo); g.setAttribute('height', 1140 - topo);
        const j = el.querySelector('.jorro'); j.setAttribute('height', kt ? lerp(0, 200, clamp((tl - T.gesso) / .3)) : 0);
        const ke = eio((tl - T.escava) / 1.2);
        el.querySelector('.cinza').setAttribute('transform', `translate(0 ${ke * 760})`); el.querySelector('.cinza').setAttribute('opacity', 1 - ke * .9);
        el.querySelector('.vazio').setAttribute('opacity', k1 * (1 - ke));
        el.querySelector('.molde').setAttribute('opacity', ke);
        const rot = (cls, txt, x, y, t0, t1) => { const r = el.querySelector('.' + cls); if (r.dataset.t !== txt) { r.innerHTML = hl(txt); r.dataset.t = txt; }
          const bw = r.offsetWidth; r.style.transform = `translate(${clamp(x - bw / 2, 60, 1020 - bw)}px,${y}px)`; r.style.opacity = tl >= t0 && tl < t1 ? clamp((tl - t0) / .3) * (1 - clamp((tl - t1 + .3) / .3)) : 0; };
        rot('dm-a', R.camada, 540, 400, 0, T.vazio);
        rot('dm-b', R.vazio, 540, 400, T.vazio - .3, T.gesso + .2);
        rot('dm-c', R.gesso, 540, 400, T.gesso, T.escava + .2);
        rot('dm-d', R.molde, 540, 400, T.escava + .3, 1e9);
        el.querySelector('.dm-selo').style.opacity = clamp(tl / .4);
      },
      textos: () => Object.values(R),
    };
  });
})();
