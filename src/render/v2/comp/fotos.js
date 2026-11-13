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

  /* 13. foto.historica */
  V2.registrar({
    id: 'foto.historica', nome: 'Fotografia histórica com enquadramento dirigido', tratamento: 'arquivo', tom: 'escuro',
    objetivo: 'Mostrar a prova histórica inteira e legível, e conduzir o olho até o detalhe que a fala cita.',
    funcoes: ['historia', 'prova', 'arquivo'],
    params: { img: 'arquivo da foto', img_wh: '[w,h]', recorte: '[x0,y0,x1,y1] do conteúdo real (acervo_v2.recorte_conteudo tira borda/cartão do scanner)', ano: 'ano ≤ 4 dígitos',
      credito: 'acervo/autor ≤ 44', descricao: 'o que a foto mostra ≤ 60 (serifa)', anotacoes: '0–2 × {x, y (0–1 no recorte), texto ≤ 22}', foco: '[cx, cy] para onde a câmera vai' },
    fundo: 'a própria foto, desfocada e sépia, cobre o fundo', layout: 'moldura de arquivo 960 px de largura centrada em y≈720; panorâmica (> 2:1) vira VARREDURA numa janela 960×520; legenda de procedência embaixo da moldura (≤ y 1110)',
    paleta: 'papel #efe6d2, sépia leve, carimbo vermelho-tijolo', animacao: 'moldura assenta; câmera desliza (varredura) ou aproxima do foco; anotação: círculo se desenha + fio + rótulo',
    duracao: [2.5, 4, 7], limites: { descricao: 60, credito: 44, anotacoes: 2 }, legenda: 'livre',
    area_segura: 'moldura entre y 360 e 1080', legibilidade: 'procedência 26 px mono; descrição 36 px serifa',
    rejeicao: ['foto ampliada além de 1,6× a resolução', 'recorte que corta pessoas/objeto citado', 'panorâmica exibida como faixa fina (era o erro do vídeo do Panamá)'],
    transicao: 'mascara',
    exemplo: { params: { img: '@construcao_1913', recorte: 'auto', ano: 1913, credito: 'Library of Congress · domínio público', descricao: 'Eclusas de Gatún em construção, vista panorâmica', anotacoes: [{ x: .3, y: .55, texto: 'câmara dupla' }], foco: [.3, .5] }, dur: 5.5, fala: 'Em 1913, as eclusas de Gatún ainda estavam em obra.' },
  }, (p, ctx) => {
    const wh = p.img_wh || [1600, 1000], rc = p.recorte || [0, 0, 1, 1];
    const asp = (rc[2] - rc[0]) * wh[0] / ((rc[3] - rc[1]) * wh[1]);
    const pan = asp > 2.0, L = 940, cropH = (rc[3] - rc[1]) * wh[1];
    // panorâmica: janela de varredura com ampliação máxima de 2× os pixels reais; se a janela ficar baixa, entra
    // uma faixa de VISÃO GERAL (a foto inteira) com um retângulo mostrando o trecho ampliado
    const A = pan ? Math.round(clamp(cropH * 2.0, 260, 560)) : Math.round(clamp(L / asp, 400, 600));
    const geral = pan && A < 460, AG = Math.round(L / asp);
    const res = Math.min(((rc[2] - rc[0]) * wh[0]) / (pan ? A * asp : L), 9);   // pixels da foto por pixel da tela
    if (pan && cropH * 2.0 < 400) (V2.alertas = V2.alertas || []).push(`foto.historica: original com só ${Math.round(cropH)} px de altura útil — buscar arquivo em resolução maior`);
    const top = 400 + (700 - A - (geral ? AG + 70 : 0)) / 2;
    return {
      html: `<div class="abs" style="inset:-60px;background:url('${p.img}') center/cover;filter:blur(36px) sepia(.6) brightness(.35)"></div>
        <div class="abs mold" data-g="foto" style="left:${(1080 - L) / 2 - 16}px;top:${top}px;padding:16px 16px 0;background:#efe6d2;box-shadow:0 40px 90px rgba(0,0,0,.65)">
          ${geral ? `<div class="vg" style="position:relative;width:${L}px;height:${AG}px;background:url('${p.img}') no-repeat;background-size:${L / (rc[2] - rc[0])}px auto;background-position:${-rc[0] * L / (rc[2] - rc[0])}px ${-rc[1] * (L / (rc[2] - rc[0])) * wh[1] / wh[0]}px;filter:sepia(.18)"><div class="vr" style="position:absolute;top:-4px;bottom:-4px;border:4px solid var(--amarelo)"></div></div>
            <div style="font-family:var(--f-dado);font-size:24px;color:#4a4236;padding:8px 2px 12px">VISÃO GERAL · ↓ TRECHO AMPLIADO</div>` : ''}
          <div class="jn" style="position:relative;width:${L}px;height:${A}px;background-image:url('${p.img}');background-repeat:no-repeat;filter:sepia(.18) contrast(1.06)">
            <svg class="anot" width="${L}" height="${A}" style="position:absolute;inset:0;overflow:visible"></svg></div>
          <div class="pr" data-g="proc" style="display:flex;justify-content:space-between;align-items:center;gap:20px;padding:14px 4px 14px;font-family:var(--f-dado);font-size:26px;color:#4a4236">
            <span>ARQUIVO${p.ano ? ' · ' + esc(p.ano) : ''}</span><span style="font-size:24px;text-align:right">${esc(p.credito || '')}</span></div></div>
        ${p.ano ? `<div class="abs carimbo" data-g="carimbo" style="left:600px;white-space:nowrap;top:${top - 36}px;border:5px solid #b4432f;color:#b4432f;font-family:var(--f-dado);font-weight:700;font-size:30px;letter-spacing:3px;padding:6px 14px;transform:rotate(-4deg);background:rgba(239,230,210,.92)">FOTO REAL · ${esc(p.ano)}</div>` : ''}
        ${p.descricao ? `<div class="abs ds serif" data-g="ds" data-txt="1" style="left:72px;right:150px;font-style:italic;font-size:38px;line-height:1.2;color:#efe6d2">${esc(p.descricao)}</div>` : ''}
        ${(p.anotacoes || []).slice(0, 2).map((a, i) => `<div class="abs an an${i}" data-g="an${i}" style="font-weight:800;font-size:30px;color:#0b0f17;background:var(--amarelo);padding:4px 12px;text-transform:uppercase;white-space:nowrap;opacity:0">${esc(a.texto)}</div>`).join('')}`,
      montar(el) {
        const mo = el.querySelector('.mold'), ds = el.querySelector('.ds');
        if (ds) ds.style.top = (mo.offsetTop + mo.offsetHeight + 22) + 'px';
        if (ds && mo.offsetTop + mo.offsetHeight + 22 + ds.offsetHeight > 1110) { mo.style.top = (1110 - ds.offsetHeight - 22 - mo.offsetHeight) + 'px'; ds.style.top = (mo.offsetTop + mo.offsetHeight + 22) + 'px'; }
        const ca = el.querySelector('.carimbo'); if (ca) ca.style.top = (mo.offsetTop - 30) + 'px';
      },
      upd(tl, el, c) {
        const k = clamp(tl / c.dur), e = k * .5 + eio(k) * .5, f = p.foco || [.5, .5];
        const jn = el.querySelector('.jn');
        if (pan) { janela(jn, wh, rc, L, A, lerp(0, 1, e), .5, 1);         // varredura de ponta a ponta
          const vr = el.querySelector('.vr'); if (vr) { const fr = clamp((L / A) / asp, 0, 1); vr.style.width = (fr * L) + 'px'; vr.style.left = (lerp(0, 1, e) * (1 - fr) * L) + 'px'; } }
        else janela(jn, wh, rc, L, A, lerp(.5, f[0], e), lerp(.5, f[1], e), lerp(1, Math.min(1.25, 1 + (res - 1) * .5 + .08), e));
        const mo = el.querySelector('.mold'), km = eo5(tl / .6); mo.style.transform = `translateY(${(1 - km) * 40}px) rotate(${lerp(-1.2, -.6, km)}deg)`;
        const ca = el.querySelector('.carimbo'); if (ca) { const kc = clamp((tl - .6) / .18); ca.style.opacity = kc; ca.style.transform = `rotate(-4deg) scale(${lerp(1.8, 1, eo(kc))})`; }
        aparece(el.querySelector('.ds'), tl, .7, { dy: 12 });
        // anotações: posição recalculada da câmera atual (o círculo acompanha o ponto da foto)
        const svg = el.querySelector('.anot'); let s = '';
        (p.anotacoes || []).slice(0, 2).forEach((a, i) => {
          const bs = jn.style.backgroundSize.split(' ').map(parseFloat), bp = jn.style.backgroundPosition.split(' ').map(parseFloat);
          const px = bp[0] + (rc[0] + a.x * (rc[2] - rc[0])) * bs[0], py = bp[1] + (rc[1] + a.y * (rc[3] - rc[1])) * bs[1];
          const t0 = 1.2 + i * 1.0, ka = eo5((tl - t0) / .6), R = 56;
          if (tl > t0 && px > 0 && px < L) s += `<circle cx="${px}" cy="${py}" r="${R}" fill="none" stroke="#FFD21F" stroke-width="6" stroke-dasharray="${2 * Math.PI * R}" stroke-dashoffset="${2 * Math.PI * R * (1 - ka)}"/>
            <line x1="${px}" y1="${py - R}" x2="${px}" y2="${Math.max(8, py - R - 70 * ka)}" stroke="#FFD21F" stroke-width="4"/>`;
          const an = el.querySelector('.an' + i), r = jn.getBoundingClientRect();
          an.style.left = clamp(r.left + px - an.offsetWidth / 2, 72, 920 - an.offsetWidth) + 'px'; an.style.top = clamp(r.top + py - R - 70 - an.offsetHeight, r.top + 8, r.bottom - an.offsetHeight - 8) + 'px';   // rótulo nunca sai da janela da foto
          an.style.opacity = px > 0 && px < L ? clamp((tl - t0 - .4) / .25) : 0;
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
