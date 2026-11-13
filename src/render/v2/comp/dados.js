/* DADOS V2 — números que se explicam: papel claro, tinta escura, natureza do valor e fonte sempre na tela. */
(function () {
  const { esc, hl, clamp, lerp, eo, eo5, eio, back, aparece, palavras, revelar, caber, fmt } = V2.U;
  const H = V2.H;
  const papelFundo = `<div class="abs" style="inset:0;background:var(--papel)"></div><div class="abs" data-deco="1" style="inset:0;opacity:.5;background-image:linear-gradient(rgba(0,0,0,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(0,0,0,.035) 1px,transparent 1px);background-size:54px 54px"></div>`;
  const kickerP = (t, top = 352) => `<div class="abs kicker" data-g="kicker" style="left:72px;top:${top}px;color:#141414"><span style="display:inline-block;width:14px;height:14px;background:var(--amarelo);outline:2px solid #141414;transform:rotate(45deg);margin-right:16px;vertical-align:2px"></span>${esc(t)}</div>`;

  /* 6. numero.animado — V2.1: o número é o PROTAGONISTA (até 260 px) e vem com UMA representação concreta:
   *  - 'cubo': volume desenhado como cubo em escala ao lado de uma referência conhecida (src/v2/unidades.py: só
   *    conversão exata de unidade + alturas de referência da Wikipédia);
   *  - 'grade': N ícones (contagem real, ex.: 80 piscinas de volume nominal);
   *  - 'barra': o valor contra um valor de referência da mesma unidade (com fonte).
   * Natureza do valor (média, recorde, leilão…) e fonte sempre na tela. */
  V2.registrar({
    id: 'numero.animado', nome: 'Número estatístico animado', tratamento: 'dado', tom: 'claro',
    objetivo: 'Fazer um número ser entendido: valor, unidade, NATUREZA (média, recorde, estimativa), uma representação concreta e a fonte.',
    funcoes: ['numero', 'estatistica'],
    params: { rotulo: '≤ 32 (o que é medido)', valor: 'número', casas: 'casas decimais', prefixo: "moeda ORIGINAL ('US$', 'R$'…)", unidade: '≤ 22',
      natureza: '≤ 28 (obrigatória para dinheiro)', contexto: 'frase ≤ 70 (serifa)', fonte: 'obrigatória (lista do vídeo)', conversao: 'texto da conversão com data/fonte (opcional)',
      equivalencia: "{tipo:'cubo', lado_m, ref:{nome, altura_m, forma}, texto, apoio} | {tipo:'grade', icone, n ≤ 100, texto} | {tipo:'barra', ref_valor, ref_nome, texto}" },
    fundo: 'próprio (papel)', layout: 'kicker 345 · natureza 400 · NÚMERO 450–700 · contexto · representação 790–1150 · fonte 1165',
    paleta: 'papel #F2EDE3, tinta #141414, amarelo marca-texto (vermelho só para recorde/excepcional)', animacao: 'contagem com desaceleração; régua; a representação se constrói (cubo cresce até o lado real; ícones preenchem; barra corre)',
    duracao: [3, 5, 7], limites: { rotulo: 32, unidade: 22, natureza: 28, contexto: 110 }, legenda: 'integrada',
    area_segura: 'x 72–930', legibilidade: 'número ≥ 180 px; contexto 42 px; fonte 26 px',
    rejeicao: ['valor sem fonte listada', 'dinheiro sem natureza ou conversão sem data (fatos.py)', 'equivalência que não sai de conversão exata (não inventar)'],
    transicao: 'mascara',
    exemplo: { params: { rotulo: 'Água doce por travessia', valor: 200, unidade: 'milhões de litros', natureza: 'MÉDIA POR TRAVESSIA', contexto: 'Sai do lago Gatún e vai para o mar.',
      equivalencia: { tipo: 'cubo', lado_m: 58.5, ref: { nome: 'Cristo Redentor', altura_m: 38, forma: 'torre' }, texto: 'um cubo de ≈ 59 m de lado', apoio: '≈ 80 piscinas olímpicas (volume nominal)' }, fonte: 'Wikipédia' },
      dur: 5.5, fala: 'Cada travessia gasta duzentos milhões de litros de água doce.' },
  }, (p) => {
    const v = +p.valor, cs = +p.casas || 0, eq = p.equivalencia;
    const vermelho = /RECORDE|EXCE|LEIL/i.test(p.natureza || ''), acento = vermelho ? '#d22f1f' : 'var(--amarelo)';
    let rep = '';
    if (eq && eq.tipo === 'cubo') {
      // cubo isométrico e a referência NA MESMA ESCALA (altura em px = metros × escala)
      const ALT = 290, ref = eq.ref || { nome: 'Pessoa', altura_m: 1.75, forma: 'pessoa' };
      const esc_ = ALT / Math.max(eq.lado_m * 1.12, ref.altura_m), L = eq.lado_m * esc_, dx = L * .5, dy = L * .28, hR = ref.altura_m * esc_;
      rep = `<svg class="abs repr" data-ocupa="1" style="left:72px;top:800px;overflow:visible" width="840" height="${ALT + 70}">
        <g transform="translate(60 ${ALT + 20})"><g class="cubo">
          <path d="M0 0 H${L} V${-L} H0 Z" fill="var(--amarelo)" stroke="#141414" stroke-width="5"/>
          <path d="M0 ${-L} L${dx} ${-L - dy} H${L + dx} L${L} ${-L} Z" fill="#ffe680" stroke="#141414" stroke-width="5"/>
          <path d="M${L} 0 L${L + dx} ${-dy} V${-L - dy} L${L} ${-L} Z" fill="#e0b400" stroke="#141414" stroke-width="5"/>
          <line x1="0" y1="18" x2="${L}" y2="18" stroke="#141414" stroke-width="3"/><text x="${L / 2}" y="52" text-anchor="middle" font-family="JBM" font-weight="700" font-size="30" fill="#141414">${fmt(eq.lado_m, 0)} m</text></g></g>
        <g class="refg" transform="translate(${60 + L + dx + 70} ${ALT + 20})">
          <g transform="translate(0 ${-hR})" fill="#2b2925">${(SIL[ref.forma] || SIL.barra)(Math.max(26, hR * .38), hR)}</g>
          <text x="0" y="${-hR - 16}" font-family="Mont" font-weight="800" font-size="28" fill="#141414">${esc(ref.nome)} · ${fmt(ref.altura_m, 0)} m</text></g>
        <line x1="0" x2="840" y1="${ALT + 20}" y2="${ALT + 20}" stroke="#141414" stroke-width="4"/></svg>
        <div class="abs eqt" data-g="eqt" data-txt="1" style="left:72px;right:150px;font-weight:800;font-size:34px;line-height:1.2;color:#141414">${esc(eq.texto || '')}${eq.apoio ? `<div style="font-weight:600;font-size:28px;color:#5f584c">${esc(eq.apoio)}</div>` : ''}</div>`;
    } else if (eq && eq.tipo === 'barra') {
      const mx = Math.max(v, +eq.ref_valor || 0) || 1;
      rep = `<div class="abs repr" data-ocupa="1" style="left:72px;right:150px;top:840px">
        ${[[p.rotulo || 'valor', v, acento], [eq.ref_nome, +eq.ref_valor, '#2b2925']].map(([n, x, cor], i) => `<div style="margin-top:${i ? 34 : 0}px"><div style="display:flex;justify-content:space-between;font-weight:800;font-size:34px;color:#141414"><span>${esc(n)}</span><span style="font-family:var(--f-dado)">${fmt(x, cs)}</span></div>
          <div style="height:60px;background:rgba(20,20,20,.08);margin-top:10px"><div class="br br${i}" style="height:100%;width:0;background:${cor};outline:3px solid #141414;outline-offset:-3px" data-w="${100 * x / mx}"></div></div></div>`).join('')}
        ${eq.texto ? `<div data-txt="1" style="font-weight:800;font-size:36px;margin-top:28px;color:#141414">${esc(eq.texto)}</div>` : ''}</div>`;
    } else if (eq) {
      const n = Math.min(100, Math.max(1, Math.round(eq.n || 1)));
      rep = `<div class="abs repr grade" data-ocupa="1" style="left:72px;top:820px;display:grid;color:#141414">${Array.from({ length: n }, () => `<div class="u" style="opacity:.12;padding:4px">${H.icone(eq.icone || 'caixa', { tam: 56, esp: 3 })}</div>`).join('')}</div>
        <div class="abs eqt" data-g="eqt" data-txt="1" style="left:72px;right:150px;font-weight:800;font-size:38px;color:#141414">${esc(eq.texto || '')}</div>`;
    }
    return {
      html: `${papelFundo}${kickerP(p.rotulo || '')}
        <div class="abs nat" style="left:72px;top:400px">${H.natureza(p.natureza, vermelho ? '#d22f1f' : '#141414')}</div>
        <div class="abs nb" data-g="num" data-txt="1" data-ocupa="1" style="left:62px;right:150px;top:478px;display:flex;align-items:baseline;gap:22px;flex-wrap:wrap;color:#141414">
          <span class="pr" style="font-weight:800;font-size:96px">${esc(p.prefixo || '')}</span><span class="v" style="font-weight:900;font-size:230px;line-height:.86;letter-spacing:-9px;font-variant-numeric:tabular-nums">${fmt(v, cs)}</span>
          <span class="un" style="font-weight:800;font-size:52px;line-height:1;max-width:330px">${esc(p.unidade || '')}</span></div>
        <div class="abs regua" data-deco="1" style="left:72px;height:12px;width:0;background:${acento}"></div>
        <div class="abs ctx serif" data-g="ctx" data-txt="1" style="left:72px;right:150px;font-size:42px;line-height:1.2;color:#2a2722">${hl(p.contexto || '')}</div>
        ${p.conversao ? `<div class="abs cv" data-g="cv" style="left:72px;right:150px;font-family:var(--f-dado);font-size:26px;color:#5f584c">${esc(p.conversao)}</div>` : ''}
        ${rep}
        ${p.fonte ? `<div class="abs chip-fonte" data-g="fonte" style="right:150px;top:404px;font-family:var(--f-dado);font-size:26px;letter-spacing:2px;color:#5f584c;text-transform:uppercase">FONTE · ${esc(p.fonte)}</div>` : ''}`,
      montar(el) {
        const nb = el.querySelector('.nb'), vv = el.querySelector('.v');
        let f = 230; while ((nb.scrollWidth > nb.clientWidth + 2 || nb.offsetHeight > 300) && f > 140) { f -= 10; vv.style.fontSize = f + 'px'; }
        let y = nb.offsetTop + nb.offsetHeight + 16;
        el.querySelector('.regua').style.top = y + 'px'; y += 30;
        const cx = el.querySelector('.ctx'); cx.style.top = y + 'px'; y += cx.offsetHeight + 12;
        const cv = el.querySelector('.cv'); if (cv) { cv.style.top = y + 'px'; y += cv.offsetHeight + 8; }
        const rp = el.querySelector('.repr'), et = el.querySelector('.eqt');
        if (rp && rp.classList.contains('grade')) {          // grade que cabe entre o contexto e a fonte
          const disp = 1150 - (et ? 52 : 0) - (y + 20), nn = rp.children.length; let best = null;
          for (let c = 5; c <= 14; c++) { const rows = Math.ceil(nn / c), l = Math.floor(Math.min(820 / c, disp / rows, 110)); if (l >= 36 && (!best || l > best.l)) best = { c, l, rows }; }
          best = best || { c: 14, l: 36, rows: Math.ceil(nn / 14) };
          rp.style.gridTemplateColumns = `repeat(${best.c},${best.l}px)`; rp.querySelectorAll('svg').forEach(s => { s.setAttribute('width', best.l - 8); s.setAttribute('height', best.l - 8); });
          rp.style.top = (y + 20) + 'px'; if (et) et.style.top = (y + 20 + best.rows * best.l + 10) + 'px';
        } else if (rp) {
          // representação ocupa o espaço entre o contexto e o fim da área de conteúdo (1200), texto de apoio embaixo
          const alt0 = +rp.getAttribute('height') || rp.offsetHeight, hEt = et ? et.offsetHeight + 8 : 0;
          // escala para caber entre o contexto e o fim da área de conteúdo (nada invade a faixa da legenda)
          const disp = 1200 - hEt - (y + 24), k = Math.min(1, disp / alt0), alt = alt0 * k;
          rp.style.transformOrigin = '0 0'; rp.style.transform = `scale(${k})`;
          const topo = Math.max(y + 24, 1200 - hEt - alt);
          rp.style.top = topo + 'px'; if (et) et.style.top = (topo + alt + 4) + 'px';
        }
      },
      upd(tl, el) {
        aparece(el.querySelector('.nat'), tl, .15, { dy: 10 });
        const vv = el.querySelector('.v'), k = eo((tl - .2) / 1.3); vv.textContent = fmt(v * k, cs);
        aparece(el.querySelector('.nb'), tl, .05, { dy: 20 });
        el.querySelector('.regua').style.width = lerp(0, 300, eo5((tl - .4) / 1.1)) + 'px';
        aparece(el.querySelector('.ctx'), tl, .9, { dy: 16 }); aparece(el.querySelector('.cv'), tl, 1.1, { dy: 10 });
        const cb = el.querySelector('.cubo'); if (cb) { const kc = eo5((tl - 1.3) / 1.0); cb.style.transform = `scale(${kc})`; cb.style.transformOrigin = '0 100%'; cb.style.transformBox = 'fill-box'; }
        const rg = el.querySelector('.refg'); if (rg) rg.style.opacity = clamp((tl - 2.1) / .4);
        el.querySelectorAll('.br').forEach((b, i) => b.style.width = (+b.dataset.w * eio((tl - 1.3 - i * .5) / .9)) + '%');
        const us = el.querySelectorAll('.u'); us.forEach((u, i) => { u.style.opacity = .12 + .88 * clamp((tl - 1.3 - i * .02) / .2); });
        aparece(el.querySelector('.eqt'), tl, 2.3, { dy: 10 });
        aparece(el.querySelector('.chip-fonte'), tl, .8, { dy: 0 });
      },
      textos: () => [p.rotulo, String(p.valor), fmt(v, cs), p.unidade, p.contexto, eq && eq.texto],
    };
  });

  /* 7. comparacao.grandezas — escala física: objetos com altura proporcional sobre o mesmo chão */
  const SIL = {   // silhuetas desenhadas numa caixa w×h (a altura é a grandeza)
    pessoa: (w, h) => { const r = Math.min(w * .18, h * .1); return `<circle cx="${w / 2}" cy="${r}" r="${r}"/><path d="M${w / 2 - r * 1.5} ${r * 2.4} h${r * 3} l${r * .3} ${h * .45} h-${r * .8} l-.2 ${h - r * 2.4 - h * .45} h-${r * .9} v-${h * .4} h-.6 v${h * .4} h-${r * .9} l-.2 -${h - r * 2.4 - h * .45} h-${r * .8} z"/>`; },
    predio: (w, h) => { let s = `<rect x="${w * .1}" y="0" width="${w * .8}" height="${h}"/>`; const n = Math.max(2, Math.round(h / 34)); for (let i = 0; i < n; i++) for (let j = 0; j < 3; j++) s += `<rect x="${w * .2 + j * w * .22}" y="${10 + i * (h - 20) / n}" width="${w * .12}" height="${(h - 20) / n * .5}" fill="var(--papel)"/>`; return s; },
    navio: (w, h) => `<path d="M0 ${h * .55} H${w} L${w * .9} ${h} H${w * .08} Z"/><rect x="${w * .55}" y="${h * .1}" width="${w * .3}" height="${h * .45}"/><rect x="${w * .62}" y="0" width="${w * .06}" height="${h * .12}"/>`,
    arvore: (w, h) => `<rect x="${w * .45}" y="${h * .6}" width="${w * .1}" height="${h * .4}"/><ellipse cx="${w / 2}" cy="${h * .33}" rx="${w * .42}" ry="${h * .33}"/>`,
    torre: (w, h) => `<path d="M${w / 2} 0 L${w * .62} ${h * .55} L${w * .9} ${h} H${w * .65} Q${w / 2} ${h * .78} ${w * .35} ${h} H${w * .1} L${w * .38} ${h * .55} Z"/>`,
    onda: (w, h) => `<path d="M0 ${h} C${w * .2} ${h * .2} ${w * .55} 0 ${w} ${h * .25} C${w * .7} ${h * .25} ${w * .55} ${h * .5} ${w * .75} ${h} Z"/>`,
    agua: (w, h) => { let d = `M0 ${h} V12`; for (let x = 0; x <= w; x += w / 6) d += ` Q${x + w / 24} 0 ${x + w / 12} 12 T${x + w / 6} 12`; return `<path d="${d} V${h} Z"/>`; },
    barra: (w, h) => `<rect x="${w * .15}" y="0" width="${w * .7}" height="${h}"/>`,
  };
  V2.registrar({
    id: 'comparacao.grandezas', nome: 'Comparação de grandezas (escala)', tratamento: 'dado', tom: 'claro',
    objetivo: 'Mostrar o tamanho de algo ao lado de referências conhecidas, na MESMA escala.',
    funcoes: ['escala', 'comparacao', 'tamanho'],
    params: { titulo: '≤ 40', itens: '2–4 × {rotulo ≤ 16, valor, forma: pessoa|predio|navio|arvore|torre|onda|agua|barra}', unidade: "'m', 'km'…", destaque: 'índice do item principal', fonte: 'origem das medidas' },
    fundo: 'próprio (papel)', layout: 'título 352–470; chão em y=1080; maior item = 560 px de altura; régua tracejada na altura do destaque',
    paleta: 'silhuetas em tinta; destaque em amarelo com contorno', animacao: 'itens crescem do chão um após o outro; régua corre; valor conta',
    duracao: [3, 4.5, 6], limites: { titulo: 40, rotulo: 16 }, legenda: 'livre',
    area_segura: 'x 72–930', legibilidade: 'rótulos 30 px 800; valores 40 px mono',
    rejeicao: ['unidades diferentes no mesmo gráfico', 'razão maior que 40× (o menor some: use grafico.barras com escala log ou duas cenas)'],
    transicao: 'mascara',
    exemplo: { params: { titulo: 'Quanto são *26 metros*?', unidade: 'm', destaque: 2, itens: [{ rotulo: 'Pessoa', valor: 1.8, forma: 'pessoa' }, { rotulo: 'Prédio 8 andares', valor: 24, forma: 'predio' }, { rotulo: 'Subida na eclusa', valor: 26, forma: 'agua' }, { rotulo: 'Árvore alta', valor: 30, forma: 'arvore' }], fonte: 'Wikipédia; referências aproximadas' }, dur: 5, fala: 'Vinte e seis metros: a altura de um prédio de oito andares.' },
  }, (p) => {
    const it = (p.itens || []).slice(0, 4), mx = Math.max(...it.map(x => +x.valor || 0), 1), n = it.length, larg = 858 / n, chao = 1010, ALT = 470, u = esc(p.unidade || '');
    const de = it[+p.destaque || 0] || it[0];
    return {
      html: `${papelFundo}${kickerP('ESCALA')}<div class="abs tt manchete" data-g="tt" data-txt="1" style="left:72px;right:150px;top:400px;font-size:72px;color:#141414">${hl(p.titulo || '')}</div>
        <div class="abs" style="left:72px;width:858px;top:${chao}px;height:4px;background:#141414"></div>
        ${it.map((x, i) => { const h = Math.max(24, ALT * (+x.valor || 0) / mx), w = Math.min(larg * .8, x.forma === 'navio' ? larg * .95 : x.forma === 'predio' ? larg * .7 : x.forma === 'pessoa' ? Math.max(30, h * .35) : larg * .7), dz = x === de;
          return `<div class="abs it it${i}" data-g="it${i}" style="left:${72 + i * larg}px;width:${larg}px;top:${chao - h - 70}px;height:${h + 70}px">
            <div class="vl" style="position:absolute;left:0;right:0;top:0;text-align:center;font-family:var(--f-dado);font-weight:700;font-size:38px;color:${dz ? '#141414' : '#3d3a33'}">${fmt(+x.valor, (+x.valor) % 1 ? 1 : 0)} ${u}</div>
            <svg class="sil" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" style="position:absolute;left:${(larg - w) / 2}px;bottom:0;overflow:visible" fill="${dz ? 'var(--amarelo)' : '#2b2925'}" stroke="${dz ? '#141414' : 'none'}" stroke-width="${dz ? 4 : 0}">${(SIL[x.forma] || SIL.barra)(w, h)}</svg></div>
            <div class="abs rt rt${i}" data-g="rt${i}" style="left:${72 + i * larg}px;width:${larg}px;top:${chao + 14}px;text-align:center;font-weight:800;font-size:28px;line-height:1.1;color:#141414;text-transform:uppercase">${esc(x.rotulo)}</div>`; }).join('')}
        ${de ? `<div class="abs ref" data-deco="1" style="left:72px;width:858px;top:${chao - ALT * (+de.valor) / mx}px;height:0;border-top:3px dashed #141414;opacity:0"></div>` : ''}
        ${H.fonte(p.fonte, true)}`,
      montar(el) { caber(el.querySelector('.tt'), { max: 72, min: 50, alt: 170 }); },
      upd(tl, el, ctx) {
        aparece(el.querySelector('.tt'), tl, .05, { dy: 20 });
        it.forEach((x, i) => { const t0 = .4 + i * Math.min(.6, (ctx.dur - 2) / n), k = eo5((tl - t0) / .7);
          const s = el.querySelector(`.it${i} .sil`); s.style.transform = `scaleY(${k})`; s.style.transformOrigin = '50% 100%';
          el.querySelector(`.it${i} .vl`).style.opacity = clamp((tl - t0 - .4) / .3); el.querySelector(`.rt${i}`).style.opacity = clamp((tl - t0) / .3); });
        const r = el.querySelector('.ref'); if (r) { const k = eo5((tl - .4 - n * Math.min(.6, (ctx.dur - 2) / n)) / .6); r.style.opacity = k; r.style.clipPath = `inset(0 ${100 - k * 100}% 0 0)`; }
        aparece(el.querySelector('.chip-fonte'), tl, 1, { dy: 0 });
      },
      textos: () => [p.titulo, ...it.map(x => x.rotulo + ' ' + x.valor)],
    };
  });

  /* 28. proporcao — fração de um todo em grade 10×10 (lê-se de relance) */
  V2.registrar({
    id: 'proporcao', nome: 'Gráfico de proporção (grade 10×10)', tratamento: 'dado', tom: 'claro',
    objetivo: 'Mostrar uma porcentagem como parte concreta de um todo.',
    funcoes: ['proporcao', 'porcentagem'],
    params: { rotulo: '≤ 32', pct: '0–100', texto: 'o que a parte representa (≤ 50)', resto: 'o que o resto representa (≤ 40)', fonte: 'obrigatória' },
    fundo: 'próprio (papel)', layout: 'kicker 352; % grande 410–620; grade 10×10 de 600×600 em 660–1060 (esq.) com legenda à direita',
    paleta: 'parte = amarelo com contorno tinta; resto = tinta 12%', animacao: 'células preenchem em serpentina; % conta junto',
    duracao: [3, 4, 6], limites: { rotulo: 32, texto: 50, resto: 40 }, legenda: 'livre',
    area_segura: 'x 72–930', legibilidade: '% 200 px; textos 34 px',
    rejeicao: ['soma de partes ≠ 100 quando houver várias', 'porcentagem sem base (de quê?)'],
    transicao: 'mascara',
    exemplo: { params: { rotulo: 'Eclusas novas (2016)', pct: 60, texto: 'da água é reaproveitada em 18 bacias', resto: 'vai para o mar', fonte: 'Wikipédia' }, dur: 4.5, fala: 'As eclusas novas reaproveitam sessenta por cento da água.' },
  }, (p) => {
    const pc = clamp(+p.pct || 0, 0, 100), L = 40;
    const ordem = []; for (let r = 9; r >= 0; r--) for (let c = 0; c < 10; c++) ordem.push([r, (9 - r) % 2 ? 9 - c : c]);
    return {
      html: `${papelFundo}${kickerP(p.rotulo || '')}
        <div class="abs pc" data-g="pc" data-txt="1" style="left:66px;top:400px;font-weight:900;font-size:200px;line-height:1;letter-spacing:-6px;color:#141414"><span class="v">0</span>%</div>
        <div class="abs tx" data-g="tx" data-txt="1" style="left:72px;right:150px;top:606px;font-weight:700;font-size:40px;line-height:1.15;color:#141414">${hl(p.texto || '')}</div>
        <svg class="abs gr" style="left:72px;top:690px" width="${10 * L}" height="${10 * L}">${ordem.map(([r, c], i) => `<rect class="q" data-i="${i}" x="${c * L + 3}" y="${r * L + 3}" width="${L - 6}" height="${L - 6}" fill="rgba(20,20,20,.1)"/>`).join('')}</svg>
        <div class="abs lg" data-g="lg" style="left:${72 + 10 * L + 36}px;width:${930 - 72 - 10 * L - 36}px;top:700px;font-size:28px;font-weight:700;color:#141414;line-height:1.2">
          <div style="display:flex;gap:12px;align-items:flex-start"><span style="flex:none;width:28px;height:28px;background:var(--amarelo);outline:3px solid #141414;outline-offset:-3px"></span><span>${esc(p.texto ? Math.round(pc) + '%' : '')}</span></div>
          <div style="display:flex;gap:12px;align-items:flex-start;margin-top:20px;color:#5f584c"><span style="flex:none;width:28px;height:28px;background:rgba(20,20,20,.1)"></span><span>${esc(p.resto || '')}</span></div></div>
        ${H.fonte(p.fonte, true).replace('bottom:770px', 'bottom:790px')}`,
      montar(el) { caber(el.querySelector('.tx'), { max: 40, min: 30, alt: 100 }); },
      upd(tl, el) {
        const k = eio((tl - .4) / 1.6), nq = Math.round(pc * k);
        el.querySelector('.v').textContent = nq;
        el.querySelectorAll('.q').forEach((q, i) => { const on = i < nq; q.setAttribute('fill', on ? 'var(--amarelo)' : 'rgba(20,20,20,.1)'); q.setAttribute('stroke', on ? '#141414' : 'none'); q.setAttribute('stroke-width', on ? 3 : 0); });
        aparece(el.querySelector('.tx'), tl, .3, { dy: 14 }); aparece(el.querySelector('.lg'), tl, 1.8, { dx: 20, dy: 0 }); aparece(el.querySelector('.chip-fonte'), tl, 1, { dy: 0 });
      },
      textos: () => [p.rotulo, pc + '%', String(pc), p.texto],
    };
  });
})();
