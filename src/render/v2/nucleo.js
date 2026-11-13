/* CORINGA EXPLICA — NÚCLEO V2 (13/11/2026)
 * Contrato com o Python (src/v2/palco.py), igual ao motor antigo: window.DATA = {duration, meta, scenes, captions};
 * window.seek(t) (assíncrono, determinístico: o quadro depende só de t), window.READY, window.inspecionar(t).
 *
 * Cena V2: {comp:'mapa.rota', start, end, params:{...}, fundo:{img, wh, modo, de, para}, transicao, fala, legenda}
 * Composição: V2.registrar(META, construtor). META descreve a composição (objetivo, parâmetros, limites, regras de
 * legenda e de rejeição); o construtor devolve {html, montar?(el) → Promise, upd(tl, el, ctx) → Promise?, textos?()}.
 * Ninguém desenha fora do registro: a galeria, os testes e o fiscal leem o mesmo catálogo (V2.catalogo()).
 */
(function () {
  'use strict';
  const V2 = window.V2 = window.V2 || {};
  V2.comps = V2.comps || {};

  /* ---------------- utilidades de tempo e texto ---------------- */
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const eo = x => 1 - Math.pow(1 - clamp(x), 3);                 // desacelera
  const eo5 = x => 1 - Math.pow(1 - clamp(x), 5);                // desacelera forte (entrada editorial)
  const ei = x => Math.pow(clamp(x), 3);
  const eio = x => { x = clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
  const back = x => { x = clamp(x); const c = 1.6; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
  const P = (t, t0, d = .5, f = eo) => f((t - t0) / d);
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  // *palavra* = destaque; a classe muda por tratamento (texto amarelo no escuro, marca-texto no papel)
  const hl = (s, cls = 'hl') => esc(s).replace(/\*(.+?)\*/g, `<span class="${cls}">$1</span>`);
  const limpo = s => String(s ?? '').replace(/\*/g, '');
  const fmt = (n, dec = 0) => Number(n).toLocaleString('pt-BR', { minimumFractionDigits: dec, maximumFractionDigits: dec });
  const decs = v => (String(v).split(/[.,]/)[1] || '').length;
  const num = v => Number(String(v).replace(/\./g, '').replace(',', '.'));
  // palavras em máscaras (cada palavra sobe de dentro de uma janela): revelação tipográfica de edição profissional
  const palavras = (s, cls = 'pw') => { let on = false;
    return String(s ?? '').split(/\s+/).filter(Boolean).map(w => {
      if (/^[^\w]*\*/.test(w)) on = true; const h = on; if (/\*[^\w]*$/.test(w)) on = false;
      return `<span class="${cls}-m" style="display:inline-block;overflow:hidden;vertical-align:top;padding:0 .04em .06em"><span class="${cls}${h ? ' hl' : ''}" style="display:inline-block">${esc(w.replace(/\*/g, ''))}</span></span>`; }).join(' '); };
  function revelar(el, tl, t0, { passo = .06, d = .5, dy = 1.05 } = {}) {
    if (!el) return;
    el.querySelectorAll('.pw').forEach((w, i) => { const k = eo5((tl - t0 - i * passo) / d); w.style.transform = `translateY(${(1 - k) * dy * 100}%)`; });
  }
  function aparece(el, tl, t0, { d = .45, dy = 30, dx = 0, s0 = 1, f = eo } = {}) {
    if (!el) return 0; const k = f((tl - t0) / d);
    el.style.opacity = clamp((tl - t0) / (d * .5)); el.style.transform = `translate(${(1 - k) * dx}px,${(1 - k) * dy}px) scale(${lerp(s0, 1, k)})`;
    return k;
  }
  // texto que cabe: diminui a fonte até caber em largura/altura (uma vez, na montagem)
  function caber(el, { max, min = 28, larg, alt, passo = 2 } = {}) {
    if (!el) return; let f = max || parseFloat(getComputedStyle(el).fontSize); el.style.fontSize = f + 'px';
    const L = larg || el.clientWidth, A = alt || 1e9;
    while ((el.scrollWidth > L + 1 || el.offsetHeight > A) && f > min) { f -= passo; el.style.fontSize = f + 'px'; }
    return f;
  }
  V2.U = { clamp, lerp, eo, eo5, ei, eio, back, P, esc, hl, limpo, fmt, decs, num, palavras, revelar, aparece, caber };

  /* tokens da identidade (os mesmos de estilo.css): uma escala tipográfica, um ritmo, uma espessura de linha */
  V2.T = {
    fs: { display: 120, h1: 88, h2: 64, h3: 50, corpo: 40, apoio: 34, rotulo: 28, min: 26 },
    esp: { 1: 8, 2: 16, 3: 24, 4: 32, 5: 48, 6: 72 },
    linha: { fino: 3, medio: 6, forte: 10 },
    dur: { entra: .45, sai: .35, palavra: .055, permanencia_min: 1.2 },
  };
  /* ÁREAS SEGURAS por plataforma (1080×1920). 'todas' = a mais restritiva das três (padrão). conteúdo = onde o
     protagonista da cena mora; legenda = faixa da narração, abaixo do conteúdo e acima da interface. */
  const PLATAFORMAS = { reels: { topo: 250, base: 1500, direita: 940 }, tiktok: { topo: 240, base: 1470, direita: 920 },
    shorts: { topo: 280, base: 1520, direita: 940 }, todas: { topo: 280, base: 1470, direita: 930 } };
  V2.Z = Object.assign({ margem: 72, conteudo: [330, 1215], legenda: [1240, 1455] }, PLATAFORMAS[(window.DATA && window.DATA.meta && window.DATA.meta.plataforma) || 'todas'] || PLATAFORMAS.todas);
  V2.PLATAFORMAS = PLATAFORMAS;
  // saída de elementos temporários (banners): fator 1 → 0 entre t1 e t1 + d
  V2.U.saida = (tl, t1, d = .35) => 1 - eo((tl - t1) / d);

  V2.registrar = (meta, construtor) => { V2.comps[meta.id] = { meta, construtor }; };
  V2.catalogo = () => Object.values(V2.comps).map(c => c.meta);

  /* ---------------- fundo fotográfico com câmera dirigida ---------------- */
  // modo 'cobrir': a foto cobre a tela; câmera vai de `de` para `para` = [cx, cy, zoom] (centro na foto, 0–1).
  // modo 'moldura': foto inteira (deitada, panorâmica, histórica) sobre ela mesma desfocada; câmera dentro da moldura.
  // Zoom limitado pela resolução: nunca amplia a foto além de 1,5× os pixels originais (foto estourada = borrada).
  const W = 1080, H = 1920;
  function fundoHTML(sc) {
    const f = sc.fundo; if (!f || !f.img) return '';
    const modo = f.modo || 'cobrir';
    if (modo === 'moldura' || modo === 'arquivo') {
      const [w, h] = f.wh || [1600, 900], larg = 960, alt = Math.min(1000, Math.round(larg * h / w));
      const lw = alt < Math.round(larg * h / w) ? Math.round(alt * w / h) : larg;
      return `<div class="fundo-desfoque" style="background-image:url('${f.img}')"></div>
        <div class="moldura-v2 abs" data-g="foto" style="left:${(W - lw) / 2 - (modo === 'arquivo' ? 18 : 0)}px;top:${f.y || 470}px;padding:${modo === 'arquivo' ? 18 : 0}px;${modo === 'arquivo' ? 'background:#efe6d2;box-shadow:0 40px 90px rgba(0,0,0,.6)' : 'box-shadow:0 30px 80px rgba(0,0,0,.55)'}">
          <div class="janela" style="position:relative;width:${lw}px;height:${alt}px;overflow:hidden"><img class="foto-mold" src="${f.img}" style="position:absolute;left:0;top:0;width:${lw}px;height:${alt}px;transform-origin:0 0;${modo === 'arquivo' ? 'filter:sepia(.25) contrast(1.05)' : ''}"></div></div>`;
    }
    return `<img class="fundo-foto" src="${f.img}"><div class="escurece-base" style="opacity:${f.escurece ?? 1}"></div>`;
  }
  function camera(wh, cx, cy, z, vw, vh, lim = 1.5) {   // transforma a foto (w×h) para mostrar o ponto (cx,cy) no centro
    const [w, h] = wh; let s = Math.max(vw / w, vh / h) * z; s = Math.min(s, Math.max(Math.max(vw / w, vh / h), lim));
    let x = vw / 2 - cx * w * s, y = vh / 2 - cy * h * s;
    x = clamp(x, vw - w * s, 0); y = clamp(y, vh - h * s, 0);
    return { s, x, y };
  }
  function moverFundo(el, sc, tl, dur) {
    const f = sc.fundo; if (!f || !f.img) return;
    const de = f.de || [.5, .5, 1], para = f.para || [.5, .5, 1.08];
    const k = (() => { const x = clamp(tl / Math.max(.1, dur)); return x * .55 + eio(x) * .45; })();
    const cx = lerp(de[0], para[0], k), cy = lerp(de[1], para[1], k), z = lerp(de[2], para[2], k);
    const wh = f.wh || [1600, 2400];
    if ((f.modo || 'cobrir') === 'cobrir') {
      const im = el.querySelector('.fundo-foto'); if (!im) return;
      const c = camera(wh, cx, cy, z, W, H, f.lim || 1.5);
      im.style.width = wh[0] + 'px'; im.style.height = wh[1] + 'px';
      im.style.transform = `translate(${c.x}px,${c.y}px) scale(${c.s})`;
    } else {
      const im = el.querySelector('.foto-mold'), jn = el.querySelector('.janela'); if (!im || !jn) return;
      const vw = jn.clientWidth, vh = jn.clientHeight, c = camera([vw, vh], cx, cy, z, vw, vh, 3);
      im.style.transform = `translate(${c.x}px,${c.y}px) scale(${c.s})`;
      const mo = el.querySelector('.moldura-v2'); if (mo) mo.style.transform = `translateY(${lerp(14, -14, k)}px)`;
    }
  }
  V2.camera = camera;

  /* ---------------- montagem das cenas ---------------- */
  const D = window.DATA, PALCO = document.getElementById('palco');
  const cenas = [];
  const AVISOS = [];
  V2.cenas = cenas; V2.avisos = AVISOS;
  function montar() {
    (D.scenes || []).forEach((sc, i) => {
      sc.i = i;
      let c = V2.comps[sc.comp];
      if (!c) { AVISOS.push(`cena ${i}: composição desconhecida "${sc.comp}"`); c = V2.comps['foto.documental']; }
      const el = document.createElement('div'); el.className = 'cena'; el.dataset.comp = c.meta.id; el.style.zIndex = 10 + i;
      const ctx = { i, D, sc, el, V2, meta: c.meta, dur: sc.end - sc.start };
      let b;
      try { b = c.construtor(sc.params || {}, ctx) || {}; }
      catch (e) { AVISOS.push(`cena ${i} (${c.meta.id}): ${e.message}`); b = { html: '' }; }
      let base = null;
      if (sc.base && V2.comps[sc.base.comp]) {      // composição de BASE congelada (ex.: revelação sobre o mecanismo pronto)
        const cb = V2.comps[sc.base.comp], bsc = { ...sc, comp: sc.base.comp, params: sc.base.params || {}, fundo: null };
        const bctx = { i: i + 1000, D, sc: bsc, el, V2, meta: cb.meta, dur: +sc.base.dur || 8 };
        try { base = { b: cb.construtor(bsc.params, bctx) || {}, ctx: bctx, t: +sc.base.t || 0, meta: cb.meta }; } catch (e) { AVISOS.push(`base ${sc.base.comp}: ${e.message}`); }
      }
      el.innerHTML = (base ? `<div class="base-cena abs${base.meta.tratamento ? ' t-' + base.meta.tratamento : ''}" style="inset:0">${base.b.html || ''}</div><div class="abs" style="inset:0;background:rgba(5,8,14,${sc.base.escurece ?? .55})"></div>` : '') + fundoHTML(sc) + (b.html || '');
      if (c.meta.tratamento) el.classList.add('t-' + c.meta.tratamento);
      PALCO.appendChild(el);
      cenas.push({ sc, el, b, meta: c.meta, ctx, base, temKicker: !!el.querySelector('.kicker') });
    });
  }

  /* ---------------- transições editoriais ---------------- */
  // a cena que ENTRA fica por cima e se revela; a anterior continua embaixo até a entrada terminar (sem fantasma).
  const TRANS = {
    corte: { d: 0 },
    mascara: { d: .42 },   // cortina diagonal (clip-path)
    deslize: { d: .38 },   // empurra de baixo
    zoom: { d: .34 },      // entra ampliada e assenta
    flash: { d: .26 },
    preto: { d: .5 },
  };
  function entrada(c) { return TRANS[c.sc.transicao || c.meta.transicao || 'corte'] ? (c.sc.transicao || c.meta.transicao || 'corte') : 'corte'; }

  /* ---------------- legenda contextual ---------------- */
  // Regras (ordem 6 da reconstrução):
  //  - posição FIXA (faixa 1180–1440); não pula entre cenas;
  //  - a composição declara meta.legenda: 'normal' | 'integrada' (a tela já escreve a fala: gancho, revelação) |
  //    'livre' (a composição não usa a faixa da legenda; padrão);
  //  - em 'integrada' a legenda some SÓ quando o trecho é redundante com o texto da tela (≥ 60% das palavras de
  //    conteúdo já estão escritas); se a fala trouxer informação nova, a legenda fica;
  //  - número já escrito grande na tela não é repetido: trecho só com esse número + palavras já presentes some;
  //  - palavra futura aparece em branco translúcido (o bloco não "pula"), a palavra dita fica branca e a atual, amarela.
  const LEG = document.createElement('div'); LEG.id = 'legenda';
  const VAZIAS = new Set('a o as os de da do das dos e é em no na nos nas um uma uns umas que se por para pra com ao à seu sua mas ou foi era ser como mais este esta esse essa isso isto ele ela eles elas the of'.split(' '));
  const nrm = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9% ]/g, ' ').split(/\s+/).filter(w => w && !VAZIAS.has(w));
  function textoDaTela(c) {
    if (c._tela !== undefined) return c._tela;
    let tx = '';
    try { tx = (c.b.textos ? c.b.textos() : []).join(' '); } catch (e) { tx = ''; }
    if (!tx) tx = [...c.el.querySelectorAll('[data-txt]')].map(e => e.textContent).join(' ');
    return (c._tela = new Set(nrm(tx)));
  }
  function cobre(ws, c) { if (!ws.length) return 1; const tela = textoDaTela(c); return ws.filter(w => tela.has(w) || tela.has(w.replace(/s$/, ''))).length / ws.length; }
  // redundância medida na FALA DA CENA inteira (todos os blocos de legenda dentro dela) e no bloco: a fala que só repete
  // a tela some; um bloco que traz palavra nova aparece mesmo assim
  function redundante(cap, c) {
    if (c._falaCob === undefined) {
      const ws = (D.captions || []).filter(x => x.start < c.sc.end && x.end > c.sc.start).flatMap(x => nrm(x.words.map(w => w.w).join(' ')));
      c._falaCob = cobre(ws, c);
    }
    const bloco = cobre(nrm(cap.words.map(w => w.w).join(' ')), c);
    return bloco >= 0.6 || (c._falaCob >= 0.6 && bloco >= 0.34);
  }
  function legenda(t) {
    const cap = (D.captions || []).find(c => t >= c.start && t < c.end + 0.05);
    const at = cenas.find(c => t >= c.sc.start && t < c.sc.end);
    LEG.dataset.motivo = '';
    if (!cap || !at) { LEG.style.opacity = 0; LEG.dataset.motivo = 'sem fala'; return; }
    const modo = at.sc.legenda || at.meta.legenda || 'livre';
    if (modo === 'oculta') { LEG.style.opacity = 0; LEG.dataset.motivo = 'cena pediu'; return; }
    if (modo === 'integrada' && redundante(cap, at)) { LEG.style.opacity = 0; LEG.dataset.motivo = 'redundante com a tela'; return; }
    LEG.classList.toggle('claro', at.meta.tom === 'claro');
    // posição ESTÁVEL por cena (calculada na partida pela ocupação da cena, ver ocupacao())
    LEG.style.top = (at.legTop || V2.Z.legenda[0]) + 'px';
    if (LEG.dataset.k != cap.start) {
      LEG.dataset.k = cap.start;
      LEG.innerHTML = `<div class="bloco">${cap.words.map(w => `<span class="w${w.hl ? ' hl' : ''}">${esc(w.w)}</span>`).join(' ')}</div>`;
      // hierarquia: com texto principal na tela, a legenda é texto de apoio (menor); sozinha, é a voz da cena
      const f0 = at.legFonte || 66; const b = LEG.firstChild; let f = f0; b.style.fontSize = f + 'px';
      // no máximo 2 linhas; diminui pouco, nunca abaixo de 50 px; palavra longa nunca é cortada (quebra no espaço)
      while (b.offsetHeight > f0 * 1.08 * 2.05 && f > 50) { f -= 2; b.style.fontSize = f + 'px'; }
    }
    LEG.style.opacity = 1;
    const ws = LEG.querySelectorAll('.w');
    cap.words.forEach((w, i) => {
      const s0 = w.s ?? cap.start, s1 = (cap.words[i + 1] && cap.words[i + 1].s) ?? cap.end;
      const e = ws[i]; if (!e) return;
      e.classList.toggle('fut', t < s0 - 0.02);
      e.classList.toggle('ag', t >= s0 - 0.02 && t < s1 && !w.hl);
    });
    const kb = eo((t - cap.start + 0.04) / 0.18); LEG.firstChild.style.transform = `translateY(${(1 - kb) * 14}px)`;
  }

  /* ---------------- camadas fixas ---------------- */
  function camadasFixas() {
    PALCO.insertAdjacentHTML('beforeend', `<div id="preto" class="abs" style="inset:0;background:#000;opacity:0;z-index:50"></div>
      <div id="flash" class="abs" style="inset:0;background:#fff;opacity:0;z-index:51;mix-blend-mode:screen"></div>
      <div class="vinheta"></div><div class="grao"></div>
      <div id="marca"><i></i>${esc((D.meta && D.meta.marca_curta) || 'CORINGA EXPLICA')}</div>
      ${(D.scenes || []).some(s => s.ia) ? '<div id="aviso-ia">IMAGEM GERADA POR IA</div>' : ''}`);
    PALCO.appendChild(LEG);
  }

  /* ---------------- seek ---------------- */
  window.seek = async function (t) {
    const pend = []; let flash = 0, preto = 0;
    for (let i = 0; i < cenas.length; i++) {
      const c = cenas[i], a = c.sc.start, b = c.sc.end, nx = cenas[i + 1];
      const tr = entrada(c), d = TRANS[tr].d;
      const fim = nx ? b + TRANS[entrada(nx)].d + 0.001 : b + 1e9;
      const vis = (i === 0 ? t < fim : t >= a && t < fim);
      // visibility (e não display:none): o mapa (MapLibre) observa o tamanho do contêiner e encolheria para 0×0
      c.el.style.visibility = vis ? 'visible' : 'hidden';
      if (!vis) continue;
      c.el.style.opacity = 1;
      const k = d ? clamp((t - a) / d) : 1;
      c.el.style.clipPath = ''; c.el.style.transform = '';
      if (k < 1 && i > 0) {
        if (tr === 'mascara') { const e = eio(k) * 140; c.el.style.clipPath = `polygon(0 0, ${e}% 0, ${e - 40}% 100%, 0 100%)`; }
        else if (tr === 'deslize') c.el.style.transform = `translateY(${(1 - eo5(k)) * 100}%)`;
        else if (tr === 'zoom') { c.el.style.transform = `scale(${lerp(1.18, 1, eo5(k))})`; c.el.style.opacity = clamp(k * 3); }
        else if (tr === 'flash') flash = Math.max(flash, .9 * (1 - k));
        else if (tr === 'preto') { preto = Math.max(preto, 1 - k); }
      }
      if (tr === 'preto' && i > 0 && t < a && t > a - .25) preto = Math.max(preto, (t - (a - .25)) / .25);
      const tl = t - a;
      moverFundo(c.el, c.sc, tl, b - a);
      if (c.base && c.base.b.upd) { try { const r = c.base.b.upd(c.base.t, c.el.querySelector('.base-cena'), c.base.ctx); if (r && r.then) pend.push(r); } catch (e) { } }
      if (c.b.upd) { try { const r = c.b.upd(tl, c.el, c.ctx); if (r && r.then) pend.push(r); } catch (e) { AVISOS.push(`upd ${c.meta.id}: ${e.message}`); } }
    }
    flash = Math.max(flash, window.__v2flash || 0); window.__v2flash = 0;
    document.getElementById('flash').style.opacity = flash;
    document.getElementById('preto').style.opacity = preto;
    const at = cenas.find(c => t >= c.sc.start && t < c.sc.end) || cenas[cenas.length - 1];
    const mc = document.getElementById('marca');
    if (mc && at) { mc.classList.toggle('claro', at.meta.tom === 'claro'); document.querySelector('.vinheta').style.opacity = at.meta.tom === 'claro' ? 0 : 1; mc.style.opacity = (at.meta.marca === false || at.temKicker) ? 0 : 1; }
    legenda(t);
    if (pend.length) await Promise.all(pend);
  };

  /* ---------------- fiscal geométrico (sem IA) ---------------- */
  // Mesmo princípio do motor antigo, com regras da V2: texto sobre texto de outro bloco, texto fora do quadro, texto
  // importante nas zonas da interface, letra menor que 24 px, legenda encostando em painel/texto da composição.
  function opac(e) { let o = 1; for (; e && e !== document.body; e = e.parentElement) { const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden') return 0; o *= parseFloat(cs.opacity); } return o; }
  function grupo(e, raiz) { for (let x = e; x && x !== document.body; x = x.parentElement) { if (x.dataset && x.dataset.g) return x.dataset.g + '#' + (raiz ? raiz.dataset.comp : ''); if (x.id === 'legenda') return 'legenda'; if (x.id === 'marca' || x.id === 'aviso-ia') return x.id; if (raiz && x.parentElement === raiz) return x; } return null; }
  function caixas(raiz, ehCena) {
    const out = []; const w = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT); let n;
    while ((n = w.nextNode())) {
      const tx = n.textContent.trim(); if (!tx) continue; const el = n.parentElement;
      if (el.closest('[data-deco]')) continue;
      if (opac(el) < 0.85) continue;
      const g = grupo(el, ehCena ? raiz : null); if (!g) continue;
      const r = document.createRange(); r.selectNodeContents(n);
      const fs = parseFloat(getComputedStyle(el).fontSize);
      for (const q of r.getClientRects()) {
        if (q.width < 4 || q.height < 4) continue; const m = Math.min(q.height * .18, 12);
        out.push({ g, tx: tx.slice(0, 32), fs, svg: !!el.closest('svg'), opc: !!el.closest('[data-opcional]'), x0: q.left + 2, x1: q.right - 2, y0: q.top + m, y1: q.bottom - m });
      }
    }
    return out;
  }
  window.inspecionar = function (t) {
    const at = cenas.find(c => t >= c.sc.start && t < c.sc.end); if (!at) return [];
    const tl = t - at.sc.start; if (tl < 0.6 || at.sc.end - t < 0.3) return [];      // entrada/saída animadas não contam
    const bx = [...caixas(at.el, true), ...['legenda', 'marca', 'aviso-ia'].flatMap(id => { const e = document.getElementById(id); return e ? caixas(e, false) : []; })];
    const prob = []; const cruza = (a, b) => Math.min(a.x1, b.x1) - Math.max(a.x0, b.x0) > 6 && Math.min(a.y1, b.y1) - Math.max(a.y0, b.y0) > 6;
    for (let i = 0; i < bx.length; i++) for (let j = i + 1; j < bx.length; j++) {
      const a = bx[i], b = bx[j]; if (a.g === b.g) continue;
      if (cruza(a, b)) prob.push({ tipo: 'choque', grave: true, cap: a.g === 'legenda' || b.g === 'legenda', txt: `"${a.tx}" × "${b.tx}"`, cena: at.meta.id });
    }
    for (const a of bx) {
      if (a.x0 < 0 || a.x1 > W || a.y0 < 0 || a.y1 > H) prob.push({ tipo: 'fora', grave: true, txt: `"${a.tx}" sai do quadro`, cena: at.meta.id });
      else if (!a.opc && (a.y0 < V2.Z.topo || a.y1 > V2.Z.base || a.x0 > V2.Z.direita)) prob.push({ tipo: 'zona', grave: false, txt: `"${a.tx}" na área da interface`, cena: at.meta.id });
      if (a.fs < V2.T.fs.min - .5 && !a.svg) prob.push({ tipo: 'pequeno', grave: false, txt: `"${a.tx}" com ${Math.round(a.fs)}px`, cena: at.meta.id });
    }
    return prob;
  };
  window.estadoV2 = function (t) {
    const at = cenas.find(c => t >= c.sc.start && t < c.sc.end);
    return { comp: at && at.meta.id, legenda: LEG.style.opacity !== '0', motivo: LEG.dataset.motivo || '', topo: at && at.legTop, fonte: at && at.legFonte, conflitos: V2.conflitosLegenda, avisos: AVISOS.slice() };
  };

  /* ---------------- ocupação da tela → posição da legenda (por cena, estável) ---------------- */
  // Cada composição marca o PROTAGONISTA com data-ocupa (mapa, diagrama, gráfico, foto, banner). Na partida, cada cena
  // é posta no instante de maior informação (70% da duração), medimos o que está ocupado e escolhemos a faixa de
  // legenda que não encosta em nada: 1240 (padrão) → 1300 → topo (360). Sem faixa livre: fica na padrão com letra
  // reduzida e o conflito vai para V2.conflitosLegenda (o fiscal reporta).
  V2.conflitosLegenda = [];
  async function ocupacao() {
    const ALT = 66 * 1.1 * 2 + 10;
    for (const c of cenas) {
      const tl = (c.sc.end - c.sc.start) * .7, t = c.sc.start + tl;
      try { await window.seek(t); } catch (e) { }
      const rects = [...c.el.querySelectorAll('[data-ocupa],[data-txt],[data-g]')].filter(e => opac(e) > .3).map(e => e.getBoundingClientRect())
        .filter(r => r.width > 4 && r.height > 4 && r.width * r.height < 1080 * 1920 * .6);
      const livre = y => !rects.some(r => r.bottom > y + 6 && r.top < y + ALT - 6 && r.right > 90 && r.left < 930);
      const op = [V2.Z.legenda[0], V2.Z.legenda[0] + 60, 360];
      c.legTop = op.find(livre);
      if (c.legTop === undefined) { c.legTop = V2.Z.legenda[0]; V2.conflitosLegenda.push({ cena: c.sc.i, comp: c.meta.id }); }
      const principal = [...c.el.querySelectorAll('[data-txt]')].some(e => opac(e) > .5 && parseFloat(getComputedStyle(e).fontSize) >= 44);
      c.legFonte = principal ? 58 : 66;
    }
  }

  /* ---------------- partida ---------------- */
  V2.iniciar = async function () {
    montar(); camadasFixas();
    const imgs = [...document.images].map(i => i.decode ? i.decode().catch(() => 0) : 0);
    await document.fonts.ready; await Promise.all(imgs);
    const montagens = cenas.map(c => c.b.montar ? Promise.resolve().then(() => c.b.montar(c.el, c.ctx)).catch(e => AVISOS.push(`montar ${c.meta.id}: ${e.message}`)) : 0);
    const bases = cenas.filter(c => c.base && c.base.b.montar).map(c => Promise.resolve().then(() => c.base.b.montar(c.el.querySelector('.base-cena'), c.base.ctx)).catch(e => AVISOS.push(`montar base: ${e.message}`)));
    await Promise.all([document.fonts.ready, ...imgs, ...montagens, ...bases]);
    await ocupacao();
    await window.seek(0);
    window.READY = true;
  };
})();
