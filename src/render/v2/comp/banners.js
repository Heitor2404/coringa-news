/* BANNERS V2 — informação por cima da imagem, com forma, fundo, divisória e animação próprios (não um cartão genérico). */
(function () {
  const { esc, hl, clamp, lerp, eo, eo5, eio, back, aparece, palavras, revelar, caber } = V2.U;
  const H = V2.H;
  const wipe = (el, k, dir = 'esq') => { if (!el) return; const e = 100 - eo5(k) * 100; el.style.clipPath = dir === 'esq' ? `inset(0 ${e}% 0 0)` : `inset(0 0 0 ${e}%)`; };

  /* 3. banner.discreto — faixa fina no alto: dado de apoio sem roubar a imagem */
  V2.registrar({
    id: 'banner.discreto', nome: 'Banner informativo discreto', tratamento: 'documental', tom: 'escuro',
    objetivo: 'Acrescentar um dado de apoio (lugar, data, medida) enquanto a imagem continua sendo o assunto.',
    funcoes: ['contexto', 'dado_apoio'],
    params: { rotulo: 'categoria curta (≤ 16): "CONTEXTO"', texto: 'informação (≤ 46) com *destaque*', icone: 'nome do ícone (opcional)', posicao: "'alto' (padrão) | 'meio' | 'baixo' (logo acima da legenda)", entra: 's (padrão 0,2)', sai: 's (padrão: fim da cena − 0,35; banner não fica depois da função)' },
    fundo: 'foto ou vídeo da cena', layout: 'faixa a partir de x=72, y≈360 (alto) ou 900 (meio); largura pelo texto, máx. 858',
    paleta: 'vidro escuro (blur) + filete amarelo de 8 px à esquerda; rótulo mono amarelo', animacao: 'faixa abre da esquerda (máscara), texto sobe 20 px, filete pulsa uma vez',
    duracao: [2, 3.5, 6], limites: { rotulo: 16, texto: 46 }, legenda: 'livre',
    area_segura: 'x 72–930; y 340–1100', legibilidade: 'texto 42 px peso 700 sobre vidro com 78% de opacidade',
    rejeicao: ['texto > 46 caracteres (vira banner.importante ou cena própria)', 'repetir literalmente a legenda'],
    transicao: 'corte',
    exemplo: { params: { rotulo: 'CONTEXTO', texto: 'Inaugurado em *1914*, após 10 anos de obra', icone: 'relogio' }, fundo: { img: '@lago_navios', de: [.5, .5, 1], para: [.45, .5, 1.1] }, dur: 4, fala: 'O canal foi aberto em 1914.' },
  }, (p) => ({
    html: `<div class="abs bd" data-g="banner" data-ocupa="1" style="left:72px;top:${p.posicao === 'meio' ? 860 : p.posicao === 'baixo' ? 1080 : 362}px;max-width:858px;display:flex;align-items:stretch;background:rgba(9,13,22,.78);backdrop-filter:blur(14px);box-shadow:0 20px 50px rgba(0,0,0,.35)">
        <div class="filete" style="flex:none;width:8px;background:var(--amarelo)"></div>
        ${p.icone ? `<div style="flex:none;display:flex;align-items:center;padding:0 0 0 24px;color:var(--amarelo)">${H.icone(p.icone, { tam: 50 })}</div>` : ''}
        <div style="padding:18px 30px 20px 24px"><div class="kicker" style="font-size:26px;color:var(--amarelo)">${esc(p.rotulo || '')}</div>
        <div class="tx" data-txt="1" style="font-weight:700;font-size:44px;line-height:1.15;margin-top:6px">${hl(p.texto || '')}</div></div></div>`,
    upd(tl, el, c) {
      const t0 = p.entra ?? .2, t1 = p.sai ?? c.dur - .35;
      const b = el.querySelector('.bd'); b.style.opacity = tl > t0 - .05 && tl < t1 + .35 ? 1 : 0;
      if (tl < t1) wipe(b, (tl - t0) / .55); else b.style.clipPath = `inset(0 0 0 ${(1 - V2.U.saida(tl, t1)) * 100}%)`;   // sai pela direita
      const tx = el.querySelector('.tx'); const k = eo((tl - t0 - .25) / .4); tx.style.transform = `translateY(${(1 - k) * 20}px)`; tx.style.opacity = k;
      const f = el.querySelector('.filete'); f.style.boxShadow = `0 0 ${20 * Math.max(0, Math.sin(clamp((tl - .7) / .6) * Math.PI))}px var(--amarelo)`;
    },
    textos: () => [p.texto],
  }));

  /* 4. banner.importante — bloco largo com ícone, divisória e listras: informação que muda o entendimento */
  V2.registrar({
    id: 'banner.importante', nome: 'Banner de informação importante', tratamento: 'alerta', tom: 'escuro',
    objetivo: 'Marcar uma informação que muda o entendimento (limite, risco, exceção, recorde) com peso visual alto.',
    funcoes: ['importante', 'alerta', 'excecao'],
    params: { nivel: "'importante' (amarelo, informação que muda o entendimento) | 'alerta' (vermelho, SÓ risco/exceção/erro)", rotulo: '≤ 18: "IMPORTANTE", "EXCEÇÃO", "ATENÇÃO"', titulo: '≤ 34, com *destaque*', texto: 'linha de apoio ≤ 60', icone: 'ícone (padrão: documento / alerta)', sai: 's (padrão: fim da cena − 0,4)' },
    fundo: 'foto escurecida (o banner precisa vencer a imagem)', layout: 'bloco de x=0 a 930 na faixa 720–1060: coluna de cor com ícone (180 px) + divisória + texto',
    paleta: 'amarelo ou vermelho sólido no bloco do ícone; painel escuro; listras diagonais animadas na borda', animacao: 'bloco entra da esquerda com overshoot; listras correm; título revela palavra a palavra',
    duracao: [2.5, 4, 6], limites: { rotulo: 18, titulo: 34, texto: 60 }, legenda: 'livre',
    area_segura: 'y 700–1100; texto até x 900', legibilidade: 'título 64 px 900; apoio 34 px 600',
    rejeicao: ['usado mais de 2× por vídeo (banaliza o alerta)', 'informação comum apresentada como excepcional (ver src/v2/fatos.py)'],
    transicao: 'corte',
    exemplo: { params: { nivel: 'importante', rotulo: 'EXCEÇÃO', titulo: 'Leilão de *vaga*, não pedágio', texto: 'US$ 5,3 milhões por uma vaga (1º/09/2026); o pedágio é à parte' }, fundo: { img: '@navio_mar', escurece: 1 }, dur: 4.2, fala: 'Esse valor foi um leilão de vaga, não o pedágio normal.' },
  }, (p) => {
    const alerta = p.nivel === 'alerta' || p.cor === 'vermelho', cor = alerta ? 'var(--vermelho)' : 'var(--amarelo)';
    return {
      html: `<div class="abs" style="inset:0;background:rgba(7,11,18,.35)"></div>
      <div class="abs bi" data-g="banner" data-ocupa="1" style="left:0;top:720px;width:930px;min-height:300px;display:flex;box-shadow:0 30px 70px rgba(0,0,0,.5)">
        <div class="ic" style="flex:none;width:190px;background:${cor};color:#0b0f17;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden">
          ${H.icone(p.icone || (alerta ? 'alerta' : 'documento'), { tam: 96, esp: 3.5 })}
          <div class="listras" data-deco="1" style="position:absolute;inset:0;background:repeating-linear-gradient(-45deg,rgba(0,0,0,.12) 0 14px,transparent 14px 28px)"></div></div>
        <div style="flex:1;background:rgba(10,14,22,.94);padding:34px 40px 34px 40px;border-left:4px solid rgba(255,255,255,.12)">
          <div class="kicker" style="font-size:26px;color:${cor}">${esc(p.rotulo || '')}</div>
          <div class="tt manchete" data-txt="1" style="font-size:64px;margin-top:12px;letter-spacing:-1px">${palavras(p.titulo || '')}</div>
          <div class="sep" style="height:3px;width:0;background:${cor};margin:20px 0 18px"></div>
          <div class="ap" data-txt="1" style="font-weight:600;font-size:36px;line-height:1.25;color:rgba(255,255,255,.88)">${esc(p.texto || '')}</div></div></div>`,
      montar(el) { el.querySelectorAll('.tt .hl').forEach(h => h.style.color = cor); caber(el.querySelector('.tt'), { max: 64, min: 46, alt: 140 }); },
      upd(tl, el, c) {
        const t1 = p.sai ?? c.dur - .4, ks = 1 - V2.U.saida(tl, t1, .4);
        const b = el.querySelector('.bi'), k = back((tl - .1) / .5); b.style.transform = `translateX(${((1 - clamp(k, 0, 1.05)) + ks) * -930}px)`; b.style.opacity = tl > .08 ? 1 : 0;
        el.querySelector('.listras').style.backgroundPosition = `${tl * 40}px 0`;
        revelar(el.querySelector('.tt'), tl, .45, { passo: .07 });
        el.querySelector('.sep').style.width = lerp(0, 160, eo5((tl - .8) / .5)) + 'px';
        aparece(el.querySelector('.ap'), tl, 1.0, { dy: 14 });
      },
      textos: () => [p.titulo, p.texto, p.rotulo],
    };
  });

  /* 5. lower_third — identificação de pessoa ou lugar (padrão de telejornal documental) */
  V2.registrar({
    id: 'lower_third', nome: 'Lower third de identificação', tratamento: 'documental', tom: 'escuro',
    objetivo: 'Dizer quem é a pessoa ou que lugar é este, no momento em que aparece.',
    funcoes: ['pessoa', 'lugar', 'identificacao'],
    params: { nome: '≤ 28', descricao: '≤ 40 (cargo, papel, data)', tipo: "'pessoa' | 'lugar' | 'historia'", ano: 'para tipo historia: ano em destaque (serifa)', sai: 's (padrão: fim − 0,35)' },
    fundo: 'retrato ou foto do lugar (obrigatório: identificação sem imagem não identifica nada)',
    layout: 'x=72; base do bloco em y=1110 (logo acima da faixa da legenda); barra vertical + nome + fio + descrição',
    paleta: 'nome branco 900; descrição mono amarela; fundo vidro escuro só atrás do texto', animacao: 'barra cresce para cima, nome entra por máscara, fio corre, descrição aparece',
    duracao: [2.5, 3.5, 5], limites: { nome: 28, descricao: 40 }, legenda: 'livre',
    area_segura: 'x 72–930; y 920–1110', legibilidade: 'nome 58 px; descrição 28 px mono',
    rejeicao: ['nome sem fonte nos fatos', 'pessoa errada na foto (acervo_v2: pessoas da foto ≠ nome)'],
    transicao: 'corte',
    exemplo: { params: { nome: 'SS Ancon', descricao: '1º navio a cruzar · 15/08/1914', tipo: 'lugar' }, fundo: { img: '@ancon_1914', de: [.5, .45, 1.0], para: [.55, .45, 1.1] }, dur: 3.8, fala: 'O primeiro navio a cruzar foi o SS Ancon.' },
  }, (p) => ({
    html: `<div class="abs lt" data-g="lt" data-ocupa="1" style="left:72px;bottom:${1920 - 1185}px;display:flex;align-items:stretch;gap:0">
        <div class="bar" style="flex:none;width:10px;background:var(--amarelo)"></div>
        ${p.ano ? `<div class="ano" style="flex:none;display:flex;align-items:center;padding:0 22px;background:#efe6d2;color:#2a2318;font-family:var(--f-serif);font-weight:700;font-size:64px">${esc(p.ano)}</div>` : ''}
        <div class="cx" style="background:linear-gradient(90deg,rgba(9,13,22,.86),rgba(9,13,22,.6));padding:18px 34px 20px 26px">
          <div class="nm" data-txt="1" style="font-weight:900;font-size:64px;line-height:1;letter-spacing:-1px;text-transform:uppercase;overflow:hidden"><span style="display:inline-block">${esc(p.nome || '')}</span></div>
          <div class="fio2" style="height:2px;background:rgba(255,255,255,.4);width:0;margin:14px 0 12px"></div>
          <div class="ds" data-txt="1" style="font-family:var(--f-dado);font-weight:700;font-size:30px;letter-spacing:2px;color:var(--amarelo);text-transform:uppercase">${p.tipo === 'lugar' ? '◉ ' : ''}${esc(p.descricao || '')}</div></div></div>`,
    upd(tl, el, c) {
      const sa = V2.U.saida(tl, p.sai ?? c.dur - .35); el.querySelector('.lt').style.opacity = sa; el.querySelector('.lt').style.transform = `translateX(${(1 - sa) * -60}px)`;
      const bar = el.querySelector('.bar'), k = eo5((tl - .15) / .4); bar.style.transform = `scaleY(${k})`; bar.style.transformOrigin = '50% 100%';
      const cx = el.querySelector('.cx'); wipe(cx, (tl - .3) / .5);
      const nm = el.querySelector('.nm span'), kn = eo5((tl - .4) / .5); nm.style.transform = `translateY(${(1 - kn) * 100}%)`;
      el.querySelector('.fio2').style.width = (eo5((tl - .7) / .6) * 100) + '%';
      aparece(el.querySelector('.ds'), tl, .9, { dy: 10 });
    },
    textos: () => [p.nome, p.descricao],
  }));

  /* 23. titulo.capitulo — título e subtítulo de capítulo (transição editorial entre blocos da história) */
  V2.registrar({
    id: 'titulo.capitulo', nome: 'Título de capítulo / transição editorial', tratamento: 'editorial', tom: 'escuro',
    objetivo: 'Separar blocos da história (o mecanismo, a consequência, a virada) e dar ritmo de documentário.',
    funcoes: ['transicao', 'capitulo', 'titulo'],
    params: { numero: "'01'…'09' (opcional)", titulo: '≤ 26, com *destaque*', subtitulo: '≤ 44 (serifa itálica)' },
    fundo: 'opcional: foto bem escurecida e desfocada (fundo.modo = cobrir, fundo.escurece)',
    layout: 'número vazado gigante (360 px) atrás; título no centro óptico (y≈820); subtítulo abaixo do fio',
    paleta: 'preto azulado, número contornado em branco 18%, título branco, fio amarelo', animacao: 'número desliza devagar; título revela por máscara; fio cresce do centro',
    duracao: [1.2, 1.8, 3], limites: { titulo: 26, subtitulo: 44 }, legenda: 'integrada',
    area_segura: 'conteúdo entre y 520 e 1100', legibilidade: 'título 92 px 900',
    rejeicao: ['mais de 3 capítulos num vídeo de 60 s', 'capítulo sem mudança real de assunto'],
    transicao: 'mascara',
    exemplo: { params: { numero: '02', titulo: 'O *mecanismo*', subtitulo: 'como a água faz o trabalho' }, dur: 2.2, fala: 'Agora, o mecanismo.' },
  }, (p) => ({
    html: `<div class="abs" style="inset:0;background:radial-gradient(ellipse at 50% 45%,#141b2a 0%,#070b12 70%)"></div>
      ${p.numero ? `<div class="abs nmr" data-deco="1" style="left:0;right:0;top:470px;text-align:center;font-weight:900;font-size:420px;line-height:1;color:transparent;-webkit-text-stroke:3px rgba(255,255,255,.16);letter-spacing:-10px">${esc(p.numero)}</div>` : ''}
      <div class="abs tt manchete eixo" data-g="tt" data-txt="1" data-centro="1" style="top:760px;font-size:96px">${palavras(p.titulo || '')}</div>
      <div class="abs fio3" style="left:50%;top:900px;height:3px;width:0;background:var(--amarelo)"></div>
      <div class="abs sb serif eixo" data-g="sb" data-txt="1" data-centro="1" style="top:930px;font-style:italic;font-size:44px;color:rgba(255,255,255,.8)">${esc(p.subtitulo || '')}</div>`,
    montar(el) { const t = el.querySelector('.tt'); caber(t, { max: 96, min: 64, alt: 120 }); },
    upd(tl, el) {
      const n = el.querySelector('.nmr'); if (n) { n.style.transform = `translateX(${lerp(60, -60, eio(tl / 2.4))}px)`; n.style.opacity = clamp(tl / .4); }
      revelar(el.querySelector('.tt'), tl, .15, { passo: .07, d: .55 });
      const f = el.querySelector('.fio3'), w = 200 * eo5((tl - .4) / .5); f.style.width = w + 'px'; f.style.marginLeft = (-w / 2 - 30) + 'px';
      aparece(el.querySelector('.sb'), tl, .55, { dy: 16 });
    },
    textos: () => [p.titulo, p.subtitulo],
  }));

  /* 24. destaque.palavras — frase sobre a imagem com marca-texto correndo nas palavras-chave */
  V2.registrar({
    id: 'destaque.palavras', nome: 'Destaque de palavras', tratamento: 'documental', tom: 'escuro',
    objetivo: 'Fixar a ideia-chave de uma frase sem trocar a imagem (marca-texto acompanha a fala).',
    funcoes: ['ideia_chave', 'enfase'],
    params: { frase: '≤ 70 caracteres; palavras-chave entre *asteriscos* (máx. 2 trechos)', ancora: "'meio' | 'alto'" },
    fundo: 'foto da cena', layout: 'bloco de texto alinhado à esquerda (x 72–930), centro em y≈760 (meio) ou 520 (alto)',
    paleta: 'texto branco 900 com sombra; marca-texto amarelo com texto escuro', animacao: 'texto entra por linhas; marca-texto varre a palavra quando ela é dita (ou em sequência)',
    duracao: [2, 3, 5], limites: { frase: 70 }, legenda: 'integrada',
    area_segura: 'y 420–1100', legibilidade: '78 px 900',
    rejeicao: ['mais de 2 destaques', 'frase que já é a legenda inteira sem ganho visual (prefira foto.documental)'],
    transicao: 'corte',
    exemplo: { params: { frase: 'A água desce *por gravidade*: o canal *não usa bombas*.' }, fundo: { img: '@margem_lago', de: [.5, .5, 1.05], para: [.5, .45, 1.12] }, dur: 3.6, fala: 'A água desce por gravidade, sem bombas.' },
  }, (p) => {
    const partes = String(p.frase || '').split(/(\*[^*]+\*)/).filter(Boolean);
    let n = 0;
    const corpo = partes.map(x => x.startsWith('*') ? `<span class="mk" data-i="${n++}" style="position:relative;display:inline;color:#fff;padding:0 8px;box-decoration-break:clone;-webkit-box-decoration-break:clone;background:linear-gradient(var(--amarelo),var(--amarelo)) no-repeat 0 0 / 0% 100%">${esc(x.slice(1, -1))}</span>` : esc(x)).join('');
    return {
      html: `<div class="abs" style="inset:0;background:linear-gradient(180deg,rgba(7,11,18,.15),rgba(7,11,18,.55) 40%,rgba(7,11,18,.55) 70%,rgba(7,11,18,.15))"></div>
        <div class="abs fr" data-g="fr" data-txt="1" style="left:72px;right:150px;top:${p.ancora === 'alto' ? 440 : 600}px;font-weight:900;font-size:78px;line-height:1.14;letter-spacing:-1.5px;text-transform:uppercase;text-shadow:0 4px 24px rgba(0,0,0,.6)">${corpo}</div>`,
      montar(el) { caber(el.querySelector('.fr'), { max: 78, min: 54, alt: 480 }); },
      upd(tl, el, ctx) {
        aparece(el.querySelector('.fr'), tl, .1, { dy: 30 });
        const mks = [...el.querySelectorAll('.mk')], d = ctx.dur;
        mks.forEach((m, i) => { const t0 = .6 + i * Math.max(.6, (d - 1.6) / Math.max(1, mks.length)); const k = eio((tl - t0) / .45);
          m.style.backgroundSize = `${k * 100}% 100%`; m.style.color = k > .5 ? '#0b0f17' : '#fff'; m.style.textShadow = k > .5 ? 'none' : ''; });
      },
      textos: () => [p.frase],
    };
  });
})();
