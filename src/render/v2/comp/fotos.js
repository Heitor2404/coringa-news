/* FOTOS V2 — fotografia tratada como documento: enquadramento dirigido, recorte do conteúdo real (sem bordas de
 * scanner), varredura para panorâmicas, anotações que apontam o que a fala descreve. */
(function () {
  const { esc, hl, clamp, lerp, eo, eo5, eio, back, aparece, caber } = V2.U;

  // mostra a região `rc` = [x0,y0,x1,y1] (0–1) da foto numa janela L×A, com câmera (cx, cy, z) DENTRO da região
  function janela(div, wh, rc, L, A, cx, cy, z) {
    const [w, h] = wh, rw = (rc[2] - rc[0]) * w, rh = (rc[3] - rc[1]) * h;
    const s = Math.max(L / rw, A / rh) * z;                         // cobre a janela com a região
    let x = L / 2 - (rc[0] * w + cx * rw) * s, y = A / 2 - (rc[1] * h + cy * rh) * s;
    x = clamp(x, L - (rc[2] * w) * s, -rc[0] * w * s); y = clamp(y, A - (rc[3] * h) * s, -rc[1] * h * s);
    div.style.backgroundSize = `${w * s}px ${h * s}px`; div.style.backgroundPosition = `${x}px ${y}px`;
  }

  /* 13. foto.historica — V2.1: DOIS MOMENTOS. (1) apresentação editorial: a foto inteira, grande, com ano, procedência
   * e contexto; (2) aproximação da região relevante com câmera suave — só até onde a resolução permite (máx. 2× os
   * pixels reais). Panorâmica: (1) a faixa inteira, (2) a janela cresce e VARRE a foto. Fundo escuro de arquivo, sem
   * borrão (a V2 deixava uma mancha desfocada embaixo). Resolução insuficiente → enquadramento alternativo + aviso. */
  V2.registrar({
    id: 'foto.historica', nome: 'Fotografia histórica com enquadramento dirigido', tratamento: 'arquivo', tom: 'escuro', marca: false,
    objetivo: 'Mostrar a prova histórica inteira e legível e, depois, conduzir o olho até o detalhe que a fala cita.',
    funcoes: ['historia', 'prova', 'arquivo'],
    params: { img: 'arquivo da foto', img_wh: '[w,h]', recorte: '[x0,y0,x1,y1] do conteúdo real (acervo_v2.recorte_conteudo)', ano: 'ano', credito: 'acervo/autor ≤ 44', descricao: 'o que a foto mostra ≤ 60',
      foco: '[cx, cy] (0–1 no recorte) da região relevante', momento2: 's em que começa a aproximação (padrão 45% da cena)', anotacoes: '0–2 × {x, y, texto ≤ 22}' },
    fundo: 'próprio (arquivo escuro, sem borrão)', layout: 'moldura de 1000 px de largura; foto vertical até 760 px de altura; descrição e procedência abaixo; tudo entre 360 e 1200',
    paleta: 'papel #efe6d2, sépia leve, carimbo tijolo', animacao: 'momento 1: moldura assenta, carimbo; momento 2: aproximação (ou varredura) suave até o foco; anotação desenha',
    duracao: [3, 5, 8], limites: { descricao: 60, credito: 44, anotacoes: 2 }, legenda: 'livre',
    area_segura: 'conteúdo entre 360 e 1200', legibilidade: 'procedência 28 px mono; descrição 40 px serifa',
    rejeicao: ['ampliação além de 2× a resolução (borra)', 'recorte que corta o assunto citado', 'panorâmica exibida como faixa fina sem varredura'],
    transicao: 'mascara',
    exemplo: { params: { img: '@construcao_1913', recorte: 'auto', ano: 1913, credito: 'Library of Congress · domínio público', descricao: 'Eclusas de Gatún em construção', anotacoes: [{ x: .3, y: .55, texto: 'câmara dupla' }], foco: [.3, .5] }, dur: 6, fala: 'Em 1913, as eclusas de Gatún ainda estavam em obra.' },
  }, (p, ctx) => {
    const wh = p.img_wh || [1600, 1000], rc = p.recorte || [0, 0, 1, 1];
    const cw = (rc[2] - rc[0]) * wh[0], ch = (rc[3] - rc[1]) * wh[1], asp = cw / ch, pan = asp > 2.0, L = 1000;
    const A1 = Math.round(clamp(L / asp, 90, 760));                        // momento 1: a foto inteira
    const A2 = pan ? Math.round(clamp(ch * 2.0, A1, 560)) : A1;           // momento 2: janela (panorâmica cresce)
    const zMax = pan ? 1 : clamp((cw / L) * 2.0, 1, 1.9);                 // aproximação limitada pela resolução
    if ((!pan && zMax < 1.15) || (pan && A2 < 300)) (V2.alertas = V2.alertas || []).push(`foto.historica: resolução baixa (${Math.round(cw)}×${Math.round(ch)} px úteis) — aproximação limitada; buscar o original em resolução maior`);
    return {
      html: `<div class="abs" style="inset:0;background:radial-gradient(ellipse at 50% 42%,#2a2219 0%,#120f0b 75%)"></div>
        <div class="abs" data-deco="1" style="inset:0;opacity:.35;background-image:repeating-linear-gradient(0deg,rgba(255,240,210,.03) 0 2px,transparent 2px 5px)"></div>
        <div class="abs mold" data-g="foto" data-ocupa="1" style="left:${(1080 - L) / 2 - 14}px;padding:14px 14px 0;background:#efe6d2;box-shadow:0 40px 90px rgba(0,0,0,.7)">
          <div class="jn" style="position:relative;width:${L}px;height:${A1}px;background-image:url('${p.img}');background-repeat:no-repeat;filter:sepia(.16) contrast(1.06)">
            <svg class="anot" width="${L}" height="${A2}" style="position:absolute;left:0;top:0;overflow:visible"></svg></div>
          <div class="pr" data-g="proc" style="display:flex;justify-content:space-between;align-items:center;gap:20px;padding:12px 4px 14px;font-family:var(--f-dado);font-size:28px;color:#4a4236">
            <span style="font-weight:700">ARQUIVO${p.ano ? ' · ' + esc(p.ano) : ''}</span><span style="font-size:26px;text-align:right">${esc(p.credito || '')}</span></div></div>
        ${p.ano ? `<div class="abs carimbo" data-g="carimbo" style="right:178px;white-space:nowrap;border:5px solid #b4432f;color:#b4432f;font-family:var(--f-dado);font-weight:700;font-size:30px;letter-spacing:3px;padding:6px 14px;transform:rotate(-4deg);background:rgba(239,230,210,.95)">FOTO REAL · ${esc(p.ano)}</div>` : ''}
        ${p.descricao ? `<div class="abs ds serif" data-g="ds" data-txt="1" style="left:72px;right:150px;font-style:italic;font-size:40px;line-height:1.2;color:#efe6d2">${esc(p.descricao)}</div>` : ''}
        ${(p.anotacoes || []).slice(0, 2).map((a, i) => `<div class="abs an an${i}" data-g="an${i}" style="font-weight:800;font-size:32px;color:#0b0f17;background:var(--amarelo);padding:4px 12px;text-transform:uppercase;white-space:nowrap;opacity:0">${esc(a.texto)}</div>`).join('')}`,
      montar(el) { el._lay = null; },
      upd(tl, el, c) {
        const m2 = p.momento2 ?? c.dur * .45, k2 = eio((tl - m2) / Math.max(1, c.dur - m2 - .3));
        const A = Math.round(lerp(A1, A2, eio((tl - m2) / .8)));
        const jn = el.querySelector('.jn'), mo = el.querySelector('.mo') || el.querySelector('.mold'), ds = el.querySelector('.ds');
        jn.style.height = A + 'px'; el.querySelector('.anot').setAttribute('height', A);
        // centraliza o bloco (moldura + descrição) na área de conteúdo 360–1200
        const hMo = mo.offsetHeight, hDs = ds ? ds.offsetHeight + 20 : 0, top = clamp(360 + (840 - hMo - hDs) / 2, 360, 1200 - hMo - hDs);
        mo.style.top = top + 'px'; if (ds) ds.style.top = (top + hMo + 20) + 'px';
        const ca = el.querySelector('.carimbo'); if (ca) { ca.style.top = Math.max(V2.Z.topo + 8, top + 24) + 'px'; const kc = clamp((tl - .6) / .18), ksai = (p.anotacoes || []).length ? clamp((tl - m2 - .4) / .3) : 0; ca.style.opacity = kc * (1 - ksai); /* sai quando a anotação entra (mesma região) */ ca.style.transform = `rotate(-4deg) scale(${lerp(1.8, 1, eo(kc))})`; }
        // câmera dentro da janela: momento 1 = foto inteira; momento 2 = foco (ou varredura)
        const f = p.foco || [.5, .5];
        if (pan) janela(jn, wh, rc, L, A, tl < m2 ? .5 : lerp(.5, f[0], k2) + (k2 >= 1 ? 0 : 0), .5, tl < m2 ? 1 : 1);
        else janela(jn, wh, rc, L, A, lerp(.5, f[0], k2), lerp(.5, f[1], k2), lerp(1, zMax, k2));
        if (pan && tl >= m2) janela(jn, wh, rc, L, A, lerp(0, 1, k2), .5, 1);
        mo.style.transform = `translateY(${(1 - eo5(tl / .6)) * 40}px) rotate(${lerp(-1, -.5, eo5(tl / .6))}deg)`;
        aparece(ds, tl, .7, { dy: 12 });
        const svg = el.querySelector('.anot'); let s = '';
        (p.anotacoes || []).slice(0, 2).forEach((a, i) => {
          const bs = jn.style.backgroundSize.split(' ').map(parseFloat), bp = jn.style.backgroundPosition.split(' ').map(parseFloat);
          const px = bp[0] + (rc[0] + a.x * (rc[2] - rc[0])) * bs[0], py = bp[1] + (rc[1] + a.y * (rc[3] - rc[1])) * bs[1];
          const t0 = m2 + .6 + i * .8, ka = eo5((tl - t0) / .6), R = 58, vis = px > 10 && px < L - 10 && py > 10 && py < A - 10;
          if (tl > t0 && vis) s += `<circle cx="${px}" cy="${py}" r="${R}" fill="none" stroke="#FFD21F" stroke-width="7" stroke-dasharray="${2 * Math.PI * R}" stroke-dashoffset="${2 * Math.PI * R * (1 - ka)}"/>`;
          const an = el.querySelector('.an' + i), r = jn.getBoundingClientRect();
          an.style.left = clamp(r.left + px - an.offsetWidth / 2, 72, 920 - an.offsetWidth) + 'px'; an.style.top = clamp(r.top + py - R - 14 - an.offsetHeight, r.top + 8, r.bottom - an.offsetHeight - 8) + 'px';
          an.style.opacity = vis ? clamp((tl - t0 - .3) / .25) : 0;
        });
        svg.innerHTML = s;
      },
      textos: () => [p.descricao, ...(p.anotacoes || []).map(a => a.texto)],
    };
  });

  /* 14. foto.sequencia */
  V2.registrar({
    id: 'foto.sequencia', nome: 'Sequência de fotografias documentais', tratamento: 'documental', tom: 'escuro',
    objetivo: 'Contar um acontecimento em 2–4 imagens reais em ordem (antes, durante, depois), cada uma no seu tempo.',
    funcoes: ['sequencia', 'acontecimento', 'ritmo'],
    params: { fotos: '2–4 × {img, wh, legenda ≤ 40, de:[cx,cy,z], para:[cx,cy,z]}', titulo: 'opcional ≤ 30' },
    fundo: 'as próprias fotos (tela cheia)', layout: 'foto em tela cheia; contador 01/03 no alto à esquerda; legenda da foto em faixa em y≈1010',
    paleta: 'foto + barra de progresso segmentada amarela no alto (y 330)', animacao: 'cortes secos com micro-empurrão; câmera dirigida em cada foto; barra segmentada avança',
    duracao: [3, 5, 8], limites: { legenda: 40, fotos: 4 }, legenda: 'livre',
    area_segura: 'textos entre y 330 e 1100', legibilidade: 'legenda da foto 36 px 700 em faixa escura',
    rejeicao: ['fotos repetidas (hash perceptual igual)', 'menos de 1,2 s por foto', 'foto sem relação com o trecho da fala'],
    transicao: 'corte',
    exemplo: { params: { fotos: [{ img: '@navio_mar', legenda: 'O navio chega pelo Caribe', de: [.6, .5, 1], para: [.7, .5, 1.06] }, { img: '@camara_eclusa', legenda: 'Entra na câmara da eclusa', de: [.5, .6, 1.05], para: [.5, .45, 1.1] }, { img: '@agua_clara', legenda: 'Segue pelas eclusas novas', de: [.4, .5, 1], para: [.55, .5, 1.08] }] }, dur: 6, fala: 'O navio chega, entra na câmara e segue viagem.' },
  }, (p, ctx) => {
    const fs = (p.fotos || []).slice(0, 4), n = fs.length;
    return {
      html: fs.map((f, i) => `<div class="abs fq fq${i}" style="inset:0;display:none;overflow:hidden"><img class="fi" src="${f.img}" style="position:absolute;left:0;top:0;transform-origin:0 0"></div>`).join('') +
        `<div class="escurece-base"></div>
        <div class="abs" data-g="seg" style="left:72px;right:150px;top:340px;display:flex;gap:10px">${fs.map((f, i) => `<div style="flex:1;height:6px;background:rgba(255,255,255,.3)"><div class="sg sg${i}" style="height:100%;width:0;background:var(--amarelo)"></div></div>`).join('')}</div>
        <div class="abs ct" data-g="ct" style="left:72px;top:366px;font-family:var(--f-dado);font-weight:700;font-size:28px;letter-spacing:3px;color:#fff;text-shadow:0 2px 10px #000"></div>
        ${fs.map((f, i) => `<div class="abs lg lg${i}" data-g="lg" data-txt="1" style="left:72px;top:1010px;max-width:858px;font-weight:700;font-size:38px;line-height:1.15;color:#fff;background:rgba(7,11,18,.78);padding:12px 22px;border-left:6px solid var(--amarelo);display:none">${esc(f.legenda || '')}</div>`).join('')}`,
      upd(tl, el, c) {
        const d = c.dur / n, i = clamp(Math.floor(tl / d), 0, n - 1), tl2 = tl - i * d;
        fs.forEach((f, j) => { el.querySelector('.fq' + j).style.display = j === i ? 'block' : 'none'; el.querySelector('.lg' + j).style.display = j === i ? 'block' : 'none';
          el.querySelector('.sg' + j).style.width = (j < i ? 100 : j === i ? clamp(tl2 / d) * 100 : 0) + '%'; });
        const f = fs[i], im = el.querySelector(`.fq${i} .fi`), wh = f.wh || [1600, 1000], de = f.de || [.5, .5, 1], pa = f.para || [.5, .5, 1.08];
        const k = clamp(tl2 / d), e = k * .6 + eio(k) * .4, cm = V2.camera(wh, lerp(de[0], pa[0], e), lerp(de[1], pa[1], e), lerp(de[2], pa[2], e) + .04 * (1 - eo5(tl2 / .3)), 1080, 1920);
        im.style.width = wh[0] + 'px'; im.style.height = wh[1] + 'px'; im.style.transform = `translate(${cm.x}px,${cm.y}px) scale(${cm.s})`;
        el.querySelector('.ct').textContent = `${String(i + 1).padStart(2, '0')} / ${String(n).padStart(2, '0')}`;
        aparece(el.querySelector('.lg' + i), tl2, .2, { dx: -24, dy: 0 });
      },
      textos: () => fs.map(f => f.legenda),
    };
  });

  /* 8. comparacao.antes_depois */
  V2.registrar({
    id: 'comparacao.antes_depois', nome: 'Comparação antes/depois', tratamento: 'documental', tom: 'escuro',
    objetivo: 'Mostrar a mudança no MESMO lugar/objeto entre dois momentos (obra × pronto, cheio × seco).',
    funcoes: ['antes_depois', 'mudanca', 'transformacao'],
    params: { img_antes: 'foto 1', img_depois: 'foto 2 (mesmo assunto, enquadramento parecido)', rotulo_antes: '≤ 18 ("1913")', rotulo_depois: '≤ 18 ("HOJE")', titulo: '≤ 36 (opcional)' },
    fundo: 'próprio', layout: 'janela 1080×780 em y 330–1110; divisória vertical com alça; selos ANTES/DEPOIS nos cantos de cima; título acima (opcional)',
    paleta: 'antes em sépia/PB, depois em cor; divisória branca; selos amarelo/branco', animacao: 'abre no ANTES; a divisória varre da direita para a esquerda revelando o DEPOIS; para no meio por um instante e completa',
    duracao: [3, 4.5, 6], limites: { rotulo: 18, titulo: 36 }, legenda: 'livre',
    area_segura: 'y 330–1110', legibilidade: 'selos 30 px mono 700',
    rejeicao: ['fotos de lugares diferentes apresentadas como antes/depois', 'datas sem fonte'],
    transicao: 'mascara',
    exemplo: { params: { img_antes: '@ancon_1914', img_depois: '@agua_clara', rotulo_antes: '1914', rotulo_depois: '2016', titulo: 'Eclusas: *1914* × *2016*' }, dur: 5, fala: 'Das eclusas de 1914 às novas, de 2016.' },
  }, (p) => {
    const T = p.titulo ? 440 : 340, A = 1110 - T;
    const ph = (img, cls, f) => `<div class="abs ${cls}" style="left:0;top:${T}px;width:1080px;height:${A}px;background:url('${img}') center/cover;${f}"></div>`;
    return {
      html: `<div class="abs" style="inset:0;background:#070b12"></div>
        ${p.titulo ? `<div class="abs tt manchete" data-g="tt" data-txt="1" style="left:72px;right:150px;top:345px;font-size:58px">${hl(p.titulo)}</div>` : ''}
        ${ph(p.img_antes, 'pa', 'filter:sepia(.5) grayscale(.4) contrast(1.05)')}${ph(p.img_depois, 'pd', '')}
        <div class="abs dv" style="top:${T}px;height:${A}px;width:6px;margin-left:-3px;background:#fff;box-shadow:0 0 30px rgba(0,0,0,.6)">
          <div data-deco="1" style="position:absolute;left:50%;top:50%;width:76px;height:76px;margin:-38px 0 0 -38px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:34px;color:#0b0f17">⇆</div></div>
        <div class="abs sa" data-g="sa" style="left:40px;top:${T + 28}px;font-family:var(--f-dado);font-weight:700;font-size:30px;letter-spacing:3px;background:#efe6d2;color:#2a2318;padding:8px 16px">ANTES · ${esc(p.rotulo_antes || '')}</div>
        <div class="abs sd" data-g="sd" style="right:160px;top:${T + 28}px;font-family:var(--f-dado);font-weight:700;font-size:30px;letter-spacing:3px;background:var(--amarelo);color:#0b0f17;padding:8px 16px">DEPOIS · ${esc(p.rotulo_depois || '')}</div>`,
      upd(tl, el, c) {
        // divisória: 100% (só antes) → 50% (pausa) → 0% (só depois)
        const d = c.dur, a = eio(clamp((tl - .8) / (d * .3))), b = eio(clamp((tl - .8 - d * .3 - .6) / (d * .25)));
        const x = 1080 * (1 - .5 * a - .5 * b);
        el.querySelector('.pd').style.clipPath = `inset(0 0 0 ${x}px)`;
        const dv = el.querySelector('.dv'); dv.style.left = x + 'px'; dv.style.opacity = x > 4 && x < 1076 ? 1 : 0;
        el.querySelector('.sa').style.opacity = x > 420 ? 1 : 0; el.querySelector('.sd').style.opacity = x < 640 ? clamp((640 - x) / 60) : 0;
        aparece(el.querySelector('.tt'), tl, .05, { dy: 14 });
      },
      textos: () => [p.titulo, p.rotulo_antes, p.rotulo_depois],
    };
  });
})();

/* video.documental — V2.1: vídeo real (arquivo local) dentro da composição editorial: corte (início/fim), enquadramento
 * (moldura para vídeo deitado, tela cheia com foco para vertical), banner/lower third por cima e legenda. Os quadros
 * são extraídos com ffmpeg na preparação (src/v2/palco.py) — nada de API externa; o seek(t) troca o quadro exato. */
(function () {
  const { esc, hl, clamp, lerp, eo, eo5, eio, aparece } = V2.U;
  V2.registrar({
    id: 'video.documental', nome: 'Vídeo de arquivo na composição', tratamento: 'documental', tom: 'escuro',
    objetivo: 'Usar filmagem real do acontecimento (arquivo, documentário, registro) com procedência, corte e enquadramento.',
    funcoes: ['video', 'acontecimento', 'arquivo'],
    params: { video: 'arquivo .mp4 local (licença conferida no acervo)', inicio: 's no clipe', fim: 's no clipe (padrão: início + duração da cena)', modo: "'auto' | 'moldura' (deitado) | 'cobrir' (vertical/tela cheia)",
      foco: '[cx, cy] para o modo cobrir', etiqueta: '"VÍDEO · 1914 · acervo" ≤ 40', lower_third: '{nome, descricao} opcional', velocidade: '0,5–1 (câmera lenta opcional)' },
    fundo: 'o próprio vídeo', layout: 'deitado: moldura 1000×562 centrada em 360–1200 com etiqueta acima e lower third abaixo; vertical: tela cheia com escurecimento só na base',
    paleta: 'escuro neutro; etiqueta amarela; sem filtro que altere o registro', animacao: 'quadro a quadro do clipe (sem interpolação); moldura assenta; lower third entra e sai',
    duracao: [2, 4, 8], limites: { etiqueta: 40 }, legenda: 'livre',
    area_segura: 'textos entre 360 e 1200', legibilidade: 'etiqueta 28 px mono',
    rejeicao: ['clipe sem licença/procedência', 'trecho que não mostra o que a fala diz', 'vídeo ampliado além de 1,6× a resolução'],
    transicao: 'corte',
    exemplo: { params: { video: '@video_teste', inicio: 0.5, etiqueta: 'VÍDEO DE TESTE (SINTÉTICO)', lower_third: { nome: 'Conjunto de Mandelbrot', descricao: 'clipe local de teste técnico' } }, dur: 4, fala: 'Este é um clipe local usado só para testar o vídeo dentro da composição.' },
  }, (p, ctx) => {
    const q = p.quadros || {}, n = +q.n || 0, fps = +q.fps || 30, wh = q.wh || [1920, 1080];
    const deitado = (p.modo || 'auto') === 'moldura' || ((p.modo || 'auto') === 'auto' && wh[0] > wh[1] * 1.1);
    const L = 1000, A = Math.round(L * wh[1] / wh[0]);
    return {
      html: deitado
        ? `<div class="abs" style="inset:0;background:radial-gradient(ellipse at 50% 45%,#1a2233 0%,#070b12 75%)"></div>
           <div class="abs vmold" data-ocupa="1" data-g="video" style="left:${(1080 - L) / 2}px;top:${Math.round(360 + (840 - A) / 2 - 40)}px;width:${L}px;height:${A}px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.6);outline:2px solid rgba(255,255,255,.2)">
             ${n ? `<img class="vq" src="${q.base}0001.jpg" style="width:100%;height:100%;object-fit:cover">` : ''}</div>
           ${p.lower_third ? `<div class="abs vlt" data-g="vlt" data-txt="1" style="left:72px;top:${Math.round(360 + (840 - A) / 2 - 40 + A + 30)}px;display:flex;align-items:stretch"><div style="width:10px;background:var(--amarelo)"></div>
             <div style="padding:12px 24px;background:rgba(9,13,22,.86)"><div style="font-weight:900;font-size:52px;text-transform:uppercase;line-height:1">${esc(p.lower_third.nome || '')}</div>
             <div style="font-family:var(--f-dado);font-weight:700;font-size:28px;color:var(--amarelo);margin-top:8px;text-transform:uppercase">${esc(p.lower_third.descricao || '')}</div></div></div>` : ''}
           ${p.etiqueta ? `<div class="abs vet" data-g="vet" style="left:${(1080 - L) / 2}px;top:${Math.round(360 + (840 - A) / 2 - 92)}px;font-family:var(--f-dado);font-weight:700;font-size:28px;letter-spacing:3px;color:#0b0f17;background:var(--amarelo);padding:6px 14px">▶ ${esc(p.etiqueta)}</div>` : ''}`
        : `${n ? `<img class="vq fundo-foto" src="${q.base}0001.jpg" style="width:${wh[0]}px;height:${wh[1]}px">` : ''}<div class="escurece-base"></div>
           ${p.etiqueta ? `<div class="abs vet" data-g="vet" style="left:72px;top:360px;font-family:var(--f-dado);font-weight:700;font-size:28px;letter-spacing:3px;color:#0b0f17;background:var(--amarelo);padding:6px 14px">▶ ${esc(p.etiqueta)}</div>` : ''}`,
      upd(tl, el, c) {
        const im = el.querySelector('.vq');
        if (!deitado && im) { const f = p.foco || [.5, .5]; const cm = V2.camera(wh, f[0], f[1], 1.0, 1080, 1920, 1.6); im.style.transform = `translate(${cm.x}px,${cm.y}px) scale(${cm.s})`; }
        const mo = el.querySelector('.vmold'); if (mo) mo.style.transform = `translateY(${(1 - eo5(tl / .5)) * 30}px)`;
        aparece(el.querySelector('.vet'), tl, .2, { dx: -20, dy: 0 });
        const lt = el.querySelector('.vlt'); if (lt) { aparece(lt, tl, .6, { dx: -40, dy: 0 }); if (tl > c.dur - .4) lt.style.opacity = V2.U.saida(tl, c.dur - .4, .3); }
        if (im && n) { const fr = 1 + Math.min(n - 1, Math.max(0, Math.floor(tl * fps * (+p.velocidade || 1)))); if (im.dataset.f != fr) { im.dataset.f = fr; im.src = q.base + String(fr).padStart(4, '0') + '.jpg'; return im.decode().catch(() => 0); } }
      },
      textos: () => [p.etiqueta],
    };
  });
})();
