/* ABERTURAS V2 — o 1º quadro já é a capa (feed), e os 2 primeiros segundos vendem a pergunta. */
(function () {
  const { esc, hl, clamp, lerp, eo, eo5, eio, back, aparece, palavras, revelar, caber } = V2.U;
  const H = V2.H;

  /* 1. abertura.pergunta — cinematográfica: foto em movimento, kicker, PERGUNTA no terço de baixo, linha de contexto */
  V2.registrar({
    id: 'abertura.pergunta', nome: 'Abertura cinematográfica com pergunta', tratamento: 'documental', tom: 'escuro',
    objetivo: 'Plantar a pergunta central sobre a imagem mais forte do tema; o 1º quadro já funciona como capa.',
    funcoes: ['abertura', 'gancho'],
    params: { kicker: 'tema/série (≤ 32): "ENGENHARIA · PANAMÁ"', pergunta: 'pergunta com *destaque* (≤ 60 caracteres)', contexto: 'linha de contexto em serifa (≤ 48)',
      mascote: "'' (padrão: sem) | 'surpreso' | 'pensando' | 'apontando' — integrado à luz da cena, não colado", posicao: "'auto' (texto no lado oposto ao assunto da foto) | 'baixo' | 'alto'" },
    fundo: 'obrigatório: foto mais forte (fundo.de → fundo.para aproxima do objeto)',
    layout: 'kicker y≈340 · pergunta ocupa 760–1110 (alinhada à esquerda, 2–3 linhas) · contexto logo abaixo do fio · faixa da legenda livre',
    paleta: 'foto + escurecimento inferior; destaque amarelo em UMA palavra', animacao: 'foto aproxima; fio cresce; palavras sobem de máscaras (0,05 s entre elas); 1º quadro já legível',
    duracao: [2, 3.2, 5], limites: { kicker: 32, pergunta: 60, contexto: 48 }, legenda: 'integrada',
    area_segura: 'x 72–930; nada abaixo de 1130', legibilidade: 'pergunta ≥ 84 px, peso 900, sombra; 3 linhas no máximo',
    rejeicao: ['pergunta > 60 caracteres', 'sem foto (use abertura.revelacao com ilustração ou titulo.capitulo)', 'pergunta que não é respondida no vídeo'],
    transicao: 'corte',
    exemplo: { params: { kicker: 'ENGENHARIA · PANAMÁ', pergunta: 'Quem levanta este *navio* 26 metros?', contexto: 'Sem bombas. Sem guindastes.' }, fundo: { img: '@navio_eclusa', de: [.5, .5, 1.0], para: [.55, .52, 1.12] }, dur: 3.4,
      fala: 'Ninguém empurra este navio, mas ele sobe 26 metros.' },
  }, (p, ctx) => {
    const m = ctx.D.meta.mascote || {};
    // layout adaptativo: o texto vai para o lado OPOSTO ao assunto da foto (fundo.para[1] = altura do foco)
    const foco = ((ctx.sc.fundo || {}).para || [.5, .5])[1];
    const pos = p.posicao && p.posicao !== 'auto' ? p.posicao : (typeof foco === 'number' && foco > .62 ? 'alto' : 'baixo');
    const pose = p.mascote === true ? 'surpreso' : p.mascote;
    const comMasc = pose && m[pose];
    return {
      html: `<div class="abs" style="inset:0;background:${pos === 'alto' ? 'linear-gradient(0deg,rgba(7,11,18,0) 40%,rgba(7,11,18,.6) 65%,rgba(7,11,18,.9) 85%)' : 'linear-gradient(180deg,rgba(7,11,18,0) 30%,rgba(7,11,18,.55) 55%,rgba(7,11,18,.92) 82%)'}"></div>
        ${H.kicker(p.kicker || '', 'var(--amarelo)', 'left:72px;top:352px')}
        <div class="abs fio-k" style="left:72px;top:390px;height:3px;width:0;background:rgba(255,255,255,.5)"></div>
        <div class="abs perg manchete sombra-txt" data-g="pergunta" data-txt="1" data-ocupa="1" style="left:72px;right:${comMasc ? 380 : 150}px;top:760px;font-size:104px;color:#fff">${palavras(p.pergunta || '')}</div>
        <div class="abs ctxl" data-g="contexto" data-txt="1" style="left:72px;right:150px;font-family:var(--f-serif);font-style:italic;font-size:44px;color:rgba(255,255,255,.88);display:flex;align-items:center;gap:22px">
          <span class="fio-c" style="flex:none;display:inline-block;height:3px;width:70px;background:var(--amarelo)"></span><span>${esc(p.contexto || '')}</span></div>
        ${comMasc ? `<div class="abs mascw" data-ocupa="1" style="right:110px;top:${pos === 'alto' ? 760 : 700}px;width:360px;height:480px">
            <div class="abs" style="left:-60px;right:-60px;bottom:-40px;height:160px;background:radial-gradient(ellipse at 50% 70%,rgba(0,0,0,.65),transparent 70%)"></div>
            <div class="abs luz" style="inset:-80px;background:radial-gradient(circle at 50% 45%,rgba(255,210,31,.22),transparent 60%)"></div>
            <img class="abs masc" src="${m[pose]}" style="left:0;bottom:0;width:360px;height:480px;object-fit:contain;object-position:50% 100%;filter:drop-shadow(-6px 0 0 rgba(255,210,31,.35)) drop-shadow(0 24px 30px rgba(0,0,0,.6)) saturate(.92) contrast(1.05)"></div>` : ''}`,
      montar(el) {
        const pq = el.querySelector('.perg'); pq.querySelectorAll('.hl').forEach(h => h.style.color = 'var(--amarelo)');
        caber(pq, { max: 104, min: 68, alt: 330 });
        if (pos === 'alto') { pq.style.top = '440px'; el.querySelector('.ctxl').style.top = (440 + pq.offsetHeight + 14) + 'px'; }
        else { pq.style.top = (1110 - pq.offsetHeight) + 'px'; el.querySelector('.ctxl').style.top = 1124 + 'px'; }   // ancorada embaixo, cresce para cima
      },
      upd(tl, el) {
        // 1º quadro (tl=0) precisa estar legível: as palavras já começam na posição final quando tl<0.02
        const k = tl < .02 ? 1e9 : tl;
        revelar(el.querySelector('.perg'), k, .05, { passo: .055, d: .5 });
        el.querySelector('.fio-k').style.width = (lerp(0, 240, eo5((tl - .05) / .6))) + 'px';
        if (tl < .02) el.querySelector('.fio-k').style.width = '240px';
        const c = el.querySelector('.ctxl'); c.style.opacity = tl < .02 ? 1 : clamp((tl - .6) / .3);
        el.querySelector('.fio-c').style.width = (tl < .02 ? 70 : lerp(0, 70, eo((tl - .6) / .5))) + 'px';
        const mw = el.querySelector('.mascw'); if (mw) { const kk = eo5((tl - .5) / .7); mw.style.opacity = clamp((tl - .5) / .25); const ms = mw.querySelector('.masc');
          ms.style.transform = `translateY(${(1 - kk) * 60}px) rotate(${Math.sin(tl * 1.6) * 1.2}deg)`; ms.style.transformOrigin = '50% 100%'; }
      },
      textos: () => [p.pergunta, p.contexto, p.kicker],
    };
  });

  /* 2. abertura.revelacao — a imagem se revela por uma janela que abre (do detalhe ao todo) e o título assenta */
  V2.registrar({
    id: 'abertura.revelacao', nome: 'Abertura com revelação visual', tratamento: 'documental', tom: 'escuro',
    objetivo: 'Começar no detalhe intrigante e abrir para o todo: a revelação visual É o gancho.',
    funcoes: ['abertura', 'gancho', 'revelacao'],
    params: { titulo: 'título curto com *destaque* (≤ 42)', foco: '[cx, cy] do detalhe na foto (0–1)', kicker: 'opcional (≤ 32)' },
    fundo: 'obrigatório; a câmera começa no foco e afasta',
    layout: 'janela retangular em volta do foco (420×420) → tela cheia em 1,1 s; título no terço de baixo (840–1100)',
    paleta: 'preto em volta da janela; foto; título branco com destaque amarelo', animacao: 'janela abre (clip-path inset), título bate (escala 1,15→1)',
    duracao: [2.5, 3.5, 5], limites: { titulo: 42, kicker: 32 }, legenda: 'integrada',
    area_segura: 'título x 72–930, y ≤ 1110', legibilidade: 'título ≥ 96 px',
    rejeicao: ['foto sem detalhe que valha a revelação', 'foco fora da foto'],
    transicao: 'corte',
    exemplo: { params: { titulo: 'O *caminho* mais caro do mundo', foco: [.62, .45], kicker: 'CURIOSIDADE' }, fundo: { img: '@navio_eclusa', de: [.62, .45, 1.35], para: [.5, .5, 1.0] }, dur: 3.6,
      fala: 'Este é o caminho mais caro do mundo.' },
  }, (p, ctx) => {
    const f = p.foco || [.5, .5];
    return {
      html: `<div class="abs" style="inset:0;background:linear-gradient(180deg,rgba(7,11,18,0) 40%,rgba(7,11,18,.85) 85%)"></div>
        <div class="abs jan" data-deco="1" style="inset:0;border:3px solid var(--amarelo);opacity:0"></div>
        ${p.kicker ? H.kicker(p.kicker, 'var(--amarelo)', 'left:72px;top:352px') : ''}
        <div class="abs tit manchete sombra-txt" data-g="titulo" data-txt="1" style="left:72px;right:150px;top:840px;font-size:112px">${hl(p.titulo || '')}</div>`,
      montar(el) { const t = el.querySelector('.tit'); t.querySelectorAll('.hl').forEach(h => h.style.color = 'var(--amarelo)'); caber(t, { max: 112, min: 76, alt: 270 }); t.style.top = (1100 - t.offsetHeight) + 'px'; },
      upd(tl, el) {
        const k = eio((tl - .15) / 1.1);
        const cx = f[0] * 1080, cy = f[1] * 1920, w0 = 210;
        const L = lerp(cx - w0, 0, k), R = lerp(1080 - cx - w0, 0, k), T = lerp(cy - w0, 0, k), B = lerp(1920 - cy - w0, 0, k);
        el.style.clipPath = k >= 1 ? '' : `inset(${T}px ${R}px ${B}px ${L}px)`;
        el.parentElement.style.background = '#000';
        const j = el.querySelector('.jan'); j.style.opacity = k < 1 ? 1 : 0; j.style.left = L + 'px'; j.style.right = R + 'px'; j.style.top = T + 'px'; j.style.bottom = B + 'px';
        const t = el.querySelector('.tit'), kt = eo5((tl - 1.15) / .45);
        t.style.opacity = clamp((tl - 1.15) / .12); t.style.transform = `scale(${lerp(1.15, 1, kt)})`; t.style.transformOrigin = '0 100%';
        const kk = el.querySelector('.kicker'); if (kk) kk.style.opacity = clamp((tl - 1.3) / .3);
      },
      textos: () => [p.titulo],
    };
  });
})();
