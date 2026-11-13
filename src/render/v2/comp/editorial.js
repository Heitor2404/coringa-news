/* EDITORIAL V2 — revelação, evidência (fonte), citação e encerramento. */
(function () {
  const { esc, hl, clamp, lerp, eo, eo5, eio, back, aparece, palavras, revelar, caber } = V2.U;
  const H = V2.H;

  /* 20. revelacao.surpresa */
  V2.registrar({
    id: 'revelacao.surpresa', nome: 'Revelação de informação surpreendente', tratamento: 'alerta', tom: 'escuro',
    objetivo: 'Entregar a resposta da pergunta central (payoff) no instante em que é falada, com impacto.',
    funcoes: ['revelacao', 'payoff', 'surpresa'],
    params: { pergunta: '≤ 40 (a pergunta do início)', resposta: '1–3 palavras (≤ 18 caracteres)', detalhe: '≤ 60 (o porquê, serifa)', virada: 'segundo (na cena) em que a resposta é DITA (o motor calcula pela legenda)', cor: "'amarelo' | 'verde' | 'vermelho'" },
    fundo: 'opcional: a imagem do gancho (fecha o ciclo), muito escurecida — OU, melhor, o próprio acontecimento: cena.base = a composição do mecanismo congelada no estado final (a resposta aparece SOBRE a explicação visual)', layout: 'sem base: pergunta 380, resposta gigante y≈700, detalhe abaixo; com base: pergunta+resposta+detalhe no alto (360–700) e o mecanismo visível embaixo',
    paleta: 'resposta na cor escolhida, brilho; fundo escurecido 75%', animacao: 'antes da virada: pergunta + pulso de expectativa; na virada: clarão, resposta bate (1,25 → 1), barra corre; detalhe aparece',
    duracao: [2.5, 3.5, 5], limites: { pergunta: 40, resposta: 18, detalhe: 60 }, legenda: 'integrada',
    area_segura: 'y 360–1100', legibilidade: 'resposta ≥ 130 px 900',
    rejeicao: ['resposta mostrada antes de ser dita (spoiler)', 'revelação que não responde a pergunta do gancho'],
    transicao: 'corte',
    exemplo: { params: { pergunta: 'O que ergue o navio?', resposta: 'GRAVIDADE', detalhe: 'A água desce do lago e enche a câmara.', virada: 1.2, cor: 'amarelo' }, fundo: { img: '@navio_eclusa', escurece: 1 }, dur: 4, fala: 'Quem levanta o navio é a gravidade.' },
  }, (p, ctx) => {
    const cor = { verde: 'var(--verde)', vermelho: 'var(--vermelho)' }[p.cor] || 'var(--amarelo)', base = !!ctx.sc.base;
    const Y = base ? { pq: 360, rs: 430, pul: 520 } : { pq: 380, rs: 600, pul: 700 };
    return {
      html: `<div class="abs" style="inset:0;background:${base ? 'linear-gradient(180deg,rgba(5,8,14,.9) 0%,rgba(5,8,14,.8) 33%,rgba(5,8,14,0) 46%)' : 'rgba(5,8,14,.74)'}"></div>
        <div class="abs pul" data-deco="1" style="left:540px;top:${Y.pul}px;width:0;height:0">${[0, 1, 2].map(i => `<div class="rv-pr pr${i}" style="position:absolute;left:-150px;top:-150px;width:300px;height:300px;border-radius:50%;border:3px solid ${cor};opacity:0"></div>`).join('')}</div>
        <div class="abs rv-pq eixo" data-g="pq" data-txt="1" data-centro="1" style="top:${Y.pq}px;font-family:var(--f-serif);font-style:italic;font-size:50px;color:rgba(255,255,255,.85)">${esc(p.pergunta || '')}</div>
        <div class="abs rv-rs manchete eixo" data-g="rs" data-txt="1" data-centro="1" style="top:${Y.rs}px;white-space:nowrap;font-size:150px;color:${cor};text-shadow:0 0 60px ${cor}55,0 10px 40px rgba(0,0,0,.8);opacity:0">${esc(p.resposta || '')}</div>
        <div class="abs rv-br" style="left:50%;top:790px;height:10px;width:0;background:${cor}"></div>
        <div class="abs rv-dt serif eixo" data-g="dt" data-txt="1" data-centro="1" style="top:830px;font-size:${base ? 40 : 46}px;line-height:1.2;color:#fff">${hl(p.detalhe || '')}</div>`,
      montar(el) { const r = el.querySelector('.rv-rs'); r.style.opacity = 1; caber(r, { max: base ? 130 : 150, min: 80, larg: 780 }); r.style.opacity = 0;
        const b = el.querySelector('.rv-br'); b.style.top = (r.offsetTop + r.offsetHeight + 12) + 'px'; el.querySelector('.rv-dt').style.top = (r.offsetTop + r.offsetHeight + (base ? 40 : 60)) + 'px'; },
      upd(tl, el) {
        const v = +p.virada || 1.0;
        aparece(el.querySelector('.rv-pq'), tl, .05, { dy: -16 });
        el.querySelectorAll('.rv-pr').forEach((r, i) => { const ph = ((tl * .9 + i / 3) % 1); r.style.transform = `scale(${.4 + ph})`; r.style.opacity = tl < v ? (1 - ph) * .7 : 0; });
        const k = tl - v, rs = el.querySelector('.rv-rs');
        rs.style.opacity = k >= 0 ? 1 : 0; rs.style.transform = `scale(${k >= 0 ? lerp(1.25, 1, eo5(k / .3)) : 1.25})`;
        if (k >= 0 && k < .2) window.__v2flash = .85 * (1 - k / .2);
        const b = el.querySelector('.rv-br'), w = 300 * eo5((k - .15) / .45); b.style.width = Math.max(0, w) + 'px'; b.style.marginLeft = (-Math.max(0, w) / 2) + 'px';   /* barra centrada no eixo (sem compensação de margem torta) */
        aparece(el.querySelector('.rv-dt'), tl, v + .5, { dy: 16 });
      },
      textos: () => [p.pergunta, p.resposta, p.detalhe],
    };
  });

  /* 21. fonte.evidencia */
  V2.registrar({
    id: 'fonte.evidencia', nome: 'Cartão de fonte / evidência', tratamento: 'arquivo', tom: 'escuro',
    objetivo: 'Mostrar DE ONDE vem a informação (jornal, estudo, documento oficial), com o trecho que a sustenta grifado.',
    funcoes: ['fonte', 'evidencia', 'prova', 'documento'],
    params: { tipo: "'JORNAL' | 'ESTUDO' | 'DOCUMENTO OFICIAL'", veiculo: '≤ 30 (precisa estar na lista de fontes do vídeo)', data: 'dd/mm/aaaa', titulo: 'manchete ≤ 90', trecho: 'trecho ≤ 160', grifo: 'parte do trecho a grifar (substring)', endereco: 'domínio curto ≤ 32' },
    fundo: 'próprio (mesa escura) ou foto do assunto desfocada', layout: 'folha de papel 900 px, girada −1,5°, em y 380–1080; cabeçalho (veículo + data), manchete serifada, trecho com grifo amarelo, rodapé com endereço',
    paleta: 'papel claro; tinta; grifo amarelo; selo "FONTE VERIFICADA" verde-escuro', animacao: 'folha desliza; grifo corre no trecho quando é citado; selo carimba',
    duracao: [3, 4.5, 7], limites: { veiculo: 30, titulo: 90, trecho: 160 }, legenda: 'livre',
    area_segura: 'y 360–1100', legibilidade: 'manchete 50 px serifa 700; trecho 38 px serifa',
    rejeicao: ['veículo fora da lista de fontes do vídeo (era o "O GLOBO" do Panamá)', 'trecho inventado ou parafraseado como se fosse literal'],
    transicao: 'deslize',
    exemplo: { params: { tipo: 'EXEMPLO SINTÉTICO', veiculo: 'Jornal Exemplo', data: '00/00/0000', titulo: 'Manchete de demonstração do cartão de fonte', trecho: 'Trecho fictício: o valor foi pago em leilão por uma vaga, e não é a tarifa normal, cobrada à parte.', grifo: 'pago em leilão por uma vaga', endereco: 'exemplo.invalid' }, dur: 5, fala: 'O valor foi pago em leilão por uma vaga, não é a tarifa normal.' },
  }, (p) => {
    const tr = esc(p.trecho || ''), g = esc(p.grifo || ''), i = g ? tr.indexOf(g) : -1;
    const corpo = i >= 0 ? `${tr.slice(0, i)}<span class="gr" style="background:linear-gradient(var(--amarelo),var(--amarelo)) no-repeat 0 80% / 0% 70%;box-decoration-break:clone;-webkit-box-decoration-break:clone">${g}</span>${tr.slice(i + g.length)}` : tr;
    return {
      html: `<div class="abs" style="inset:0;background:radial-gradient(ellipse at 50% 45%,#2a2318 0%,#0e0b08 75%)"></div>
        <div class="abs folha" data-g="folha" style="left:70px;width:860px;top:380px;background:#f4efe4;color:#151515;padding:40px 44px 34px;box-shadow:0 40px 80px rgba(0,0,0,.6);transform:rotate(-1.5deg)">
          <div style="display:flex;justify-content:space-between;align-items:baseline;border-bottom:3px solid #151515;padding-bottom:14px">
            <div style="font-family:var(--f-serif);font-weight:700;font-size:40px">${esc(p.veiculo || '')}</div><div style="font-family:var(--f-dado);font-size:26px;color:#4d463a">${esc(p.data || '')}</div></div>
          <div style="font-family:var(--f-dado);font-weight:700;font-size:26px;letter-spacing:3px;color:#8a2a1a;margin:18px 0 8px">${esc(p.tipo || 'FONTE')}</div>
          <div class="ft" data-txt="1" style="font-family:var(--f-serif);font-weight:700;font-size:50px;line-height:1.1">${esc(p.titulo || '')}</div>
          <div class="ftr" data-txt="1" style="font-family:var(--f-serif);font-size:38px;line-height:1.35;margin-top:22px;color:#2a2620">${corpo}</div>
          <div style="margin-top:22px;font-family:var(--f-dado);font-size:26px;color:#6b6455">${esc(p.endereco || '')}</div></div>
        <div class="abs selo" data-g="selo" style="left:640px;top:330px;border:5px solid #1f6b3a;color:#1f6b3a;background:rgba(244,239,228,.95);font-family:var(--f-dado);font-weight:700;font-size:26px;letter-spacing:2px;padding:8px 14px;transform:rotate(5deg);opacity:0">✓ FONTE CITADA</div>`,
      montar(el) { const f = el.querySelector('.folha'); caber(el.querySelector('.ftr'), { max: 38, min: 28, alt: 9e9 });
        let fs = 38; const tr2 = el.querySelector('.ftr'); while (f.offsetTop + f.offsetHeight > 1090 && fs > 28) { fs -= 2; tr2.style.fontSize = fs + 'px'; el.querySelector('.ft').style.fontSize = (fs + 10) + 'px'; } },
      upd(tl, el, c) {
        const f = el.querySelector('.folha'), k = eo5(tl / .6); f.style.transform = `translateY(${(1 - k) * 120}px) rotate(${lerp(3, -1.5, k)}deg)`; f.style.opacity = clamp(tl / .2);
        const gr = el.querySelector('.gr'); if (gr) gr.style.backgroundSize = `${eio((tl - 1.0) / 1.0) * 100}% 70%`;
        const s = el.querySelector('.selo'), ks = clamp((tl - Math.min(2.2, c.dur - 1)) / .18); s.style.opacity = ks; s.style.transform = `rotate(5deg) scale(${lerp(1.8, 1, eo(ks))})`;
      },
      textos: () => [p.titulo, p.trecho, p.veiculo],
    };
  });

  /* 22b. citacao */
  V2.registrar({
    id: 'citacao', nome: 'Citação', tratamento: 'editorial', tom: 'escuro',
    objetivo: 'Dar voz a uma pessoa real com a frase exata dela (só se estiver nos fatos, com autor e data).',
    funcoes: ['citacao', 'depoimento'],
    params: { texto: 'frase literal ≤ 140', autor: '≤ 30', papel: '≤ 40 (cargo, ano)' },
    fundo: 'opcional: retrato do autor (lado esquerdo), escurecido', layout: 'aspas gigantes decorativas 340–560; texto serifado 560–960; autor com fio 990–1090',
    paleta: 'serifa branca, aspas amarelas 30%, fio amarelo', animacao: 'aspas entram; texto revela por linhas; autor desliza',
    duracao: [3, 5, 8], limites: { texto: 140, autor: 30, papel: 40 }, legenda: 'integrada',
    area_segura: 'y 340–1100', legibilidade: 'texto ≥ 50 px serifa',
    rejeicao: ['citação não literal ou sem fonte', 'autor que a fala não identifica'],
    transicao: 'mascara',
    exemplo: { params: { texto: 'A terra se divide, o mundo se une.', autor: 'Lema do Canal do Panamá', papel: 'inscrito no selo da Zona do Canal' }, dur: 4, fala: 'O lema do canal: a terra se divide, o mundo se une.' },
  }, (p) => ({
    html: `<div class="abs" style="inset:0;background:radial-gradient(ellipse at 30% 30%,#1a2233 0%,#070b12 75%)"></div>
      <div class="abs aspas" data-deco="1" style="left:50px;top:300px;font-family:var(--f-serif);font-weight:700;font-size:420px;line-height:1;color:var(--amarelo);opacity:.3">“</div>
      <div class="abs qt" data-g="qt" data-txt="1" style="left:90px;right:150px;top:600px;font-family:var(--f-serif);font-size:66px;line-height:1.18;color:#fff">${palavras(p.texto || '')}</div>
      <div class="abs au" data-g="au" style="left:90px;right:150px;display:flex;gap:20px;align-items:center"><span style="flex:none;width:60px;height:4px;background:var(--amarelo)"></span>
        <div><div data-txt="1" style="font-weight:900;font-size:36px;text-transform:uppercase">${esc(p.autor || '')}</div><div style="font-family:var(--f-dado);font-size:26px;color:rgba(255,255,255,.7)">${esc(p.papel || '')}</div></div></div>`,
    montar(el) { const q = el.querySelector('.qt'); caber(q, { max: 66, min: 46, alt: 420 }); el.querySelector('.au').style.top = (q.offsetTop + q.offsetHeight + 40) + 'px'; },
    upd(tl, el) { aparece(el.querySelector('.aspas'), tl, 0, { dy: 30, s0: .8 }); revelar(el.querySelector('.qt'), tl, .3, { passo: .045 }); aparece(el.querySelector('.au'), tl, 1.2, { dx: -30, dy: 0 }); },
    textos: () => [p.texto, p.autor],
  }));

  /* 22. encerramento.editorial — V2.1: QUATRO variantes; a conclusão tem relação com o acontecimento do vídeo.
   *  conclusao: a ideia em letra grande + (opcional) a composição do acontecimento CONGELADA ao fundo (cena.base);
   *  pergunta: uma pergunta aberta para o próximo vídeo; marca: só a marca, discreta, sobre a última imagem;
   *  cta: chamada contextual ("Parte 2 amanhã: …"). Mascote opcional, com chão e luz (não colado). */
  V2.registrar({
    id: 'encerramento.editorial', nome: 'Encerramento editorial (4 variantes)', tratamento: 'editorial', tom: 'escuro', marca: false,
    objetivo: 'Fechar com a conclusão do acontecimento (não só a identidade do canal), a marca legível, a chamada e as fontes.',
    funcoes: ['encerramento', 'fechamento'],
    params: { variante: "'conclusao' (padrão) | 'pergunta' | 'marca' | 'cta'", resumo: 'a conclusão ≤ 70 (conclusao) ou a pergunta ≤ 60 (pergunta)', chamada: 'CTA contextual ≤ 40 (cta)', proxima: 'nº da próxima parte',
      fontes: 'lista (≥ 1; 26 px)', marca: "'@coringa.explica'", mascote: "'' | 'apontando' | 'comemorando' (opcional)" },
    fundo: 'próprio, ou a composição do acontecimento congelada ao fundo (cena.base) / a última foto (cena.fundo, variante marca)', layout: 'conclusão grande 380–760; marca em faixa compacta 1030–1110 (logo + @ uma vez); fontes 1130–1200',
    paleta: 'grafite; amarelo só na marca e na chamada', animacao: 'a conclusão revela palavra a palavra; faixa da marca desliza; chamada pulsa uma vez; fontes aparecem',
    duracao: [2.5, 3.5, 5], limites: { resumo: 70, chamada: 40, fontes: 5 }, legenda: 'integrada',
    area_segura: 'y 360–1200; x 72–930', legibilidade: 'conclusão ≥ 64 px; marca 52 px; fontes 26 px',
    rejeicao: ['@ duplicado na tela', 'conclusão sem relação com o acontecimento do vídeo', 'mascote sobre foto poluída'],
    transicao: 'mascara',
    exemplo: { params: { variante: 'conclusao', resumo: 'Quem ergue o navio é a *gravidade*, não uma bomba.', fontes: ['Wikipédia', 'Wikipedia (inglês)', 'Revista Oeste'], marca: '@coringa.explica', mascote: 'apontando' }, dur: 4, fala: 'Segue o Coringa Explica.' },
  }, (p, ctx) => {
    const m = ctx.D.meta.mascote || {}, fts = (p.fontes || ctx.D.meta.fontes || []).slice(0, 5), v = p.variante || 'conclusao';
    const comBase = !!ctx.sc.base || !!ctx.sc.fundo, pose = p.mascote && m[p.mascote] ? m[p.mascote] : null;
    const grande = v === 'pergunta' ? `<div class="abs rz manchete" data-g="rz" data-txt="1" style="left:72px;right:${pose ? 330 : 150}px;top:400px;font-size:84px;line-height:1.02;color:#fff"><span style="color:var(--amarelo)">?</span> ${palavras(p.resumo || '')}</div>`
      : v === 'marca' ? '' : `<div class="abs rz" data-g="rz" data-txt="1" style="left:72px;right:${pose ? 330 : 150}px;top:400px;font-family:var(--f-serif);font-weight:600;font-size:70px;line-height:1.1;color:#fff;text-shadow:0 4px 20px rgba(0,0,0,.5)">${palavras(v === 'cta' ? (p.chamada || p.resumo || '') : (p.resumo || ''))}</div>`;
    return {
      html: `${comBase ? '' : `<div class="abs" style="inset:0;background:radial-gradient(ellipse at 40% 45%,#1c2436 0%,#080c14 70%)"></div>`}
        <div class="abs" style="inset:0;background:linear-gradient(180deg,rgba(7,11,18,${comBase ? .55 : 0}) 0%,rgba(7,11,18,${comBase ? .2 : 0}) 45%,rgba(7,11,18,.9) 75%)"></div>
        ${grande}
        ${pose ? `<div class="abs mascw" data-ocupa="1" style="right:110px;top:560px;width:300px;height:420px"><div class="abs" style="left:-40px;right:-40px;bottom:-30px;height:120px;background:radial-gradient(ellipse at 50% 70%,rgba(0,0,0,.7),transparent 70%)"></div>
          <img class="abs masc" src="${pose}" style="left:0;bottom:0;width:100%;height:100%;object-fit:contain;object-position:50% 100%;filter:drop-shadow(-5px 0 0 rgba(255,210,31,.35)) drop-shadow(0 20px 26px rgba(0,0,0,.6))"></div>` : ''}
        <div class="abs mc" data-g="mc" data-txt="1" style="left:72px;right:150px;top:1010px;display:flex;align-items:center;gap:22px;padding:18px 24px;background:rgba(7,11,18,.85);border-top:6px solid var(--amarelo)">
          <span style="flex:none;width:34px;height:34px;background:var(--amarelo);transform:rotate(45deg)"></span>
          <div style="flex:1"><div style="font-weight:900;font-size:52px;line-height:.95;letter-spacing:-1px">CORINGA EXPLICA</div><div style="font-family:var(--f-dado);font-weight:700;font-size:28px;margin-top:8px;color:rgba(255,255,255,.85)">${esc(p.marca || '@coringa.explica')}</div></div>
          ${v === 'marca' ? '' : `<div class="cta" style="flex:none;background:var(--amarelo);color:#0b0f17;font-weight:900;font-size:30px;padding:12px 18px">${p.proxima ? `PARTE ${esc(p.proxima)} AMANHÃ` : v === 'pergunta' ? 'RESPONDA AQUI' : 'SIGA'}</div>`}</div>
        ${fts.length ? `<div class="abs fts" data-g="fts" style="left:72px;right:150px;top:1150px;font-family:var(--f-dado);font-size:26px;line-height:1.3;color:rgba(255,255,255,.8)"><span class="fu" style="color:var(--amarelo);white-space:nowrap">FONTES ·</span> ${fts.map((x, i) => `<span class="fu" style="white-space:nowrap">${esc(x)}${i < fts.length - 1 ? ' ·' : ''}</span>`).join(' ')}</div>` : ''}`,
      montar(el) { const r = el.querySelector('.rz'); if (r) caber(r, { max: v === 'pergunta' ? 84 : 70, min: 48, alt: 560 });
        const f = el.querySelector('.fts'); if (f) {
          /* quebra DETERMINÍSTICA: fontes são unidades inteiras e a decisão de quebrar usa folga de 40 px. Antes a linha
             cabia com ~16 px de sobra e o Chromium do CI a quebrava (diferença de rasterização), mudando o layout. */
          const L = f.clientWidth - 40; let x = 0;
          f.querySelectorAll('.fu').forEach(u => { const w = u.getBoundingClientRect().width + 10; if (x > 0 && x + w > L) { u.insertAdjacentHTML('beforebegin', '<br>'); x = 0; } x += w; }); f.style.top = (1210 - f.offsetHeight) + 'px'; el.querySelector('.mc').style.top = (1210 - f.offsetHeight - 14 - el.querySelector('.mc').offsetHeight) + 'px'; }
        /* V2.2: o mascote começa 24 px ABAIXO do fim do resumo (antes a caixa 560–980 cruzava a 3ª linha e o chapéu encostava
           no texto); encolhe na proporção mantendo o pé no mesmo lugar, acima do painel da marca */
        const mw = el.querySelector('.mascw'), mc = el.querySelector('.mc');
        if (mw && r) { const base = Math.min(980, (mc ? mc.offsetTop : 1000) - 20), topo = Math.max(560, r.offsetTop + r.offsetHeight + 24);
          const h = Math.max(240, base - topo); mw.style.top = (base - h) + 'px'; mw.style.height = h + 'px'; mw.style.width = Math.round(h * 300 / 420) + 'px';
          if (base - h < topo) V2.avisos.push(`encerramento: mascote ainda encosta no resumo (${topo - (base - h)} px)`); } },
      upd(tl, el) {
        revelar(el.querySelector('.rz'), tl, .05, { passo: .05 });
        const mw = el.querySelector('.mascw'); if (mw) { const k = eo5((tl - .5) / .6); mw.style.opacity = clamp((tl - .5) / .2); mw.querySelector('.masc').style.transform = `translateY(${(1 - k) * 50}px)`; }
        aparece(el.querySelector('.mc'), tl, .7, { dy: 30 });
        const c = el.querySelector('.cta'); if (c) { const pu = Math.max(0, Math.sin(clamp((tl - 1.6) / .35) * Math.PI)) * .08; c.style.transform = `scale(${1 + pu})`; }
        aparece(el.querySelector('.fts'), tl, 1.1, { dy: 10 });
      },
      textos: () => [p.resumo, p.chamada, 'coringa explica segue siga seguir', p.marca],
    };
  });
})();
