/* BASE V2: peças compartilhadas (ícones, rótulos, chip de fonte) + a composição de reserva foto.documental. */
(function () {
  const { esc, hl, clamp, lerp, eo, eo5, aparece } = V2.U;

  /* ícones de traço (48×48), mesma espessura em tudo: linguagem gráfica única */
  const IC = {
    navio: '<path d="M4 30h40l-5 9H9z"/><path d="M10 30V22h24v8"/><path d="M15 22v-6h12v6"/><path d="M20 16v-5"/>',
    agua: '<path d="M24 6c6 9 11 15 11 21a11 11 0 0 1-22 0c0-6 5-12 11-21z"/><path d="M18 29a6 6 0 0 0 6 6"/>',
    pessoa: '<circle cx="24" cy="11" r="5"/><path d="M15 42V27a9 9 0 0 1 18 0v15"/><path d="M24 26v16"/>',
    predio: '<rect x="12" y="6" width="24" height="36"/><path d="M18 12h4M26 12h4M18 19h4M26 19h4M18 26h4M26 26h4M22 42v-8h4v8"/>',
    relogio: '<circle cx="24" cy="24" r="17"/><path d="M24 13v11l7 5"/>',
    dinheiro: '<rect x="5" y="13" width="38" height="22" rx="3"/><circle cx="24" cy="24" r="5"/><path d="M10 18v12M38 18v12"/>',
    planeta: '<circle cx="24" cy="24" r="10"/><ellipse cx="24" cy="24" rx="20" ry="6" transform="rotate(-20 24 24)"/>',
    celula: '<ellipse cx="24" cy="24" rx="18" ry="14"/><circle cx="22" cy="23" r="5"/><path d="M33 17l2 2M33 30l3-1M13 30l2-2"/>',
    raio: '<path d="M27 4L11 27h12l-3 17 17-24H25z"/>',
    fogo: '<path d="M24 43c-8 0-13-6-13-13 0-8 7-11 8-19 4 3 6 7 6 11 2-2 3-4 3-7 5 4 9 9 9 15 0 7-5 13-13 13z"/>',
    montanha: '<path d="M3 40l14-22 8 12 6-8 14 18z"/><path d="M14 23l3 3 3-3"/>',
    livro: '<path d="M6 8h14a4 4 0 0 1 4 4v30a4 4 0 0 0-4-4H6zM42 8H28a4 4 0 0 0-4 4v30a4 4 0 0 1 4-4h14z"/>',
    lupa: '<circle cx="20" cy="20" r="12"/><path d="M29 29l12 12"/>',
    alerta: '<path d="M24 5l20 36H4z"/><path d="M24 18v11M24 34v2"/>',
    pino: '<path d="M24 44s14-14 14-24a14 14 0 0 0-28 0c0 10 14 24 14 24z"/><circle cx="24" cy="20" r="5"/>',
    seta: '<path d="M6 24h34M30 14l10 10-10 10"/>',
    globo: '<circle cx="24" cy="24" r="18"/><path d="M6 24h36M24 6c6 6 6 30 0 36M24 6c-6 6-6 30 0 36"/>',
    documento: '<path d="M11 4h18l9 9v31H11z"/><path d="M29 4v9h9M17 22h15M17 29h15M17 36h10"/>',
    engrenagem: '<circle cx="24" cy="24" r="7"/><path d="M24 4v6M24 38v6M4 24h6M38 24h6M10 10l4 4M34 34l4 4M10 38l4-4M34 14l4-4"/>',
    atomo: '<circle cx="24" cy="24" r="3"/><ellipse cx="24" cy="24" rx="19" ry="7"/><ellipse cx="24" cy="24" rx="19" ry="7" transform="rotate(60 24 24)"/><ellipse cx="24" cy="24" rx="19" ry="7" transform="rotate(-60 24 24)"/>',
    folha: '<path d="M8 40C8 18 22 8 42 6c-2 20-12 34-34 34z"/><path d="M8 40L30 18"/>',
    sol: '<circle cx="24" cy="24" r="8"/><path d="M24 4v6M24 38v6M4 24h6M38 24h6M10 10l4 4M34 34l4 4M10 38l4-4M34 14l4-4"/>',
    termometro: '<path d="M20 30V8a4 4 0 0 1 8 0v22a8 8 0 1 1-8 0z"/><path d="M24 16v18"/>',
    piscina: '<path d="M4 34c4 3 8 3 12 0s8-3 12 0 8 3 12 0 4-2 4-2M4 42c4 3 8 3 12 0s8-3 12 0 8 3 12 0"/><path d="M14 30V8a4 4 0 0 1 8 0M26 30V8a4 4 0 0 1 8 0M14 16h12M14 24h12"/>',
    caixa: '<path d="M6 16l18-9 18 9v18l-18 9-18-9z"/><path d="M6 16l18 9 18-9M24 25v18"/>',
    arvore: '<path d="M24 44V28"/><path d="M24 4c9 0 15 8 13 16 4 2 5 8 0 11H11c-5-3-4-9 0-11-2-8 4-16 13-16z"/>',
    dna: '<path d="M14 4c0 10 20 10 20 20s-20 10-20 20M34 4c0 10-20 10-20 20s20 10 20 20M17 10h14M17 38h14M20 17h8M20 31h8"/>',
  };
  const icone = (nome, { tam = 64, cor = 'currentColor', esp = 3 } = {}) =>
    `<svg viewBox="0 0 48 48" width="${tam}" height="${tam}" fill="none" stroke="${cor}" stroke-width="${esp}" stroke-linecap="round" stroke-linejoin="round" style="display:block">${IC[nome] || IC.lupa}</svg>`;

  const H = V2.H = {
    IC, icone,
    kicker: (txt, cor = 'var(--amarelo)', extra = '') => `<div class="kicker abs" data-g="kicker" style="color:${cor};${extra}"><span style="display:inline-block;width:14px;height:14px;background:${cor};transform:rotate(45deg);margin-right:16px;vertical-align:2px"></span>${esc(txt)}</div>`,
    fonte: (txt, claro) => txt ? `<div class="chip-fonte abs" data-g="fonte" data-opcional="1" style="left:72px;bottom:${1920 - 1150}px;font-family:var(--f-dado);font-size:24px;letter-spacing:2px;color:${claro ? '#5f584c' : 'rgba(255,255,255,.62)'};text-transform:uppercase"><span style="opacity:.75">FONTE ·</span> ${esc(txt)}</div>` : '',
    natureza: (txt, cor = 'var(--vermelho)') => txt ? `<span class="natureza" style="display:inline-block;font-family:var(--f-dado);font-weight:700;font-size:24px;letter-spacing:3px;padding:6px 12px;border:2px solid ${cor};color:${cor};text-transform:uppercase">${esc(txt)}</span>` : '',
  };

  /* foto.documental — reserva e cena de foto pura: a imagem manda, câmera dirigida, rótulo de lugar/data discreto */
  V2.registrar({
    id: 'foto.documental', nome: 'Foto documental dirigida', tratamento: 'documental', tom: 'escuro',
    objetivo: 'Mostrar o lugar, a pessoa, o objeto ou o fato com a própria fotografia, sem texto disputando a imagem.',
    funcoes: ['lugar', 'pessoa', 'objeto', 'ambiente'],
    params: { lugar: 'texto curto opcional (≤ 28 caracteres): "PANAMÁ · 1913"', credito: 'autor/acervo (opcional, ≤ 40)' },
    fundo: 'obrigatório (foto real); fundo.de/para = enquadramento [cx, cy, zoom] calculado pelo acervo_v2',
    layout: 'foto em tela cheia; rótulo de lugar no alto (y≈340), crédito pequeno no rodapé da área útil',
    paleta: 'a da foto + escurecimento só no topo e na base', animacao: 'câmera de foco a foco (sem zoom além de 1,5× a resolução)',
    duracao: [1.5, 3.5, 6], limites: { lugar: 28, credito: 40 }, legenda: 'livre',
    area_segura: 'texto entre y 330 e 1150; x ≤ 930', legibilidade: 'rótulo 30 px mono com sombra; contraste garantido pelo escurecimento do topo',
    rejeicao: ['foto sem relação com a fala (acervo_v2.relevancia < limiar)', 'foto ampliada além da resolução', 'mesma foto já usada sem novo enquadramento'],
    transicao: 'corte',
    exemplo: { params: { lugar: 'LAGO GATÚN · PANAMÁ', credito: 'Wikimedia Commons' }, fundo: { img: '@lago_navios', de: [.5, .55, 1], para: [.55, .5, 1.12] }, dur: 4, fala: 'No meio do caminho há um lago.' },
  }, (p, ctx) => ({
    html: `${p.lugar ? `<div class="abs lugar" data-g="lugar" style="left:72px;top:336px;display:flex;align-items:center;gap:14px;font-family:var(--f-dado);font-weight:700;font-size:30px;letter-spacing:4px;color:#fff" class="sombra-txt"><span style="width:12px;height:12px;border-radius:50%;background:var(--vermelho);box-shadow:0 0 0 5px rgba(255,77,61,.25)"></span><span class="tx" style="text-shadow:0 2px 14px rgba(0,0,0,.8)">${esc(p.lugar)}</span></div>` : ''}
      ${p.credito ? `<div class="abs" data-g="credito" data-opcional="1" style="right:160px;top:1120px;font-family:var(--f-dado);font-size:24px;letter-spacing:1px;color:rgba(255,255,255,.7);text-shadow:0 1px 8px #000">${esc(p.credito)}</div>` : ''}`,
    upd(tl, el) { aparece(el.querySelector('.lugar'), tl, .25, { dx: -30, dy: 0 }); }
  }));
})();

/* animacao.quadros — sequência de quadros pré-renderizada (Manim ou outro motor), com a tipografia do palco por cima */
(function () {
  const { esc, hl, clamp, aparece, caber } = V2.U;
  V2.registrar({
    id: 'animacao.quadros', nome: 'Animação científica pré-renderizada (Manim)', tratamento: 'ciencia', tom: 'escuro',
    objetivo: 'Mostrar o que só cálculo quadro a quadro mostra bem (trajetórias, vetores que mudam, transformações geométricas).',
    funcoes: ['trajetoria', 'vetores', 'geometria', 'fisica'],
    params: { quadros: "{manim: 'lancamento', angulo} (o palco renderiza e guarda) ou {base, n, fps}", kicker: '≤ 22', titulo: '≤ 36', legenda: '≤ 4 × {cor, texto ≤ 18}' },
    fundo: 'os próprios quadros (mesma prancheta da V2)', layout: 'quadros em tela cheia (gráfico 590–1090); kicker e título 345–500; legenda de cores logo abaixo do título',
    paleta: 'a da prancheta; cores dos vetores explicadas na legenda', animacao: 'a do Manim (determinística, mesmo fps do vídeo)',
    duracao: [2, 4, 8], limites: { titulo: 36, legenda: 4 }, legenda: 'livre',
    area_segura: 'y 340–1110', legibilidade: 'legenda das cores 28 px 700',
    rejeicao: ['Manim indisponível (sem Cairo/Pango): a montagem não escolhe esta composição', 'animação que um diagrama SVG já resolveria'],
    problemas_conhecidos: ['módulo opcional: exige Cairo e Pango no sistema (no CI: apt-get libpango1.0-dev)'],
    transicao: 'mascara',
    exemplo: { params: { quadros: { manim: 'lancamento', angulo: 50 }, kicker: 'FÍSICA', titulo: 'A bola *desacelera para cima*, não para o lado', legenda: [{ cor: '#3FD0E0', texto: 'horizontal: constante' }, { cor: '#FF4D3D', texto: 'vertical: muda' }, { cor: '#FFFFFF', texto: 'velocidade' }] }, dur: 4, fala: 'Na horizontal a velocidade não muda; na vertical, a gravidade freia e depois acelera.' },
  }, (p, ctx) => {
    const q = p.quadros || {}, n = +q.n || 0, fps = +q.fps || 30;
    return {
      html: `${n ? `<img class="qd" style="position:absolute;inset:0;width:1080px;height:1920px" src="${q.base}0001.jpg">` : `<div class="abs" style="inset:0;background:var(--tecnico)"></div>`}
        <div class="abs kicker" data-g="kicker" style="left:72px;top:345px;color:var(--ciano)"><span style="display:inline-block;width:14px;height:14px;border:3px solid var(--ciano);transform:rotate(45deg);margin-right:16px;vertical-align:2px"></span>${esc(p.kicker || '')}</div>
        <div class="abs tt manchete" data-g="tt" data-txt="1" style="left:72px;right:150px;top:392px;font-size:56px">${hl(p.titulo || '')}</div>
        <div class="abs lg" data-g="lg" style="left:72px;right:150px;top:520px;display:flex;flex-wrap:wrap;gap:8px 24px">${(p.legenda || []).slice(0, 4).map(l => `<span style="display:flex;align-items:center;gap:10px;font-weight:700;font-size:26px"><i style="width:34px;height:8px;background:${l.cor}"></i>${esc(l.texto)}</span>`).join('')}</div>`,
    montar(el) { const t = el.querySelector('.tt'); caber(t, { max: 56, min: 40, alt: 120 }); el.querySelector('.lg').style.top = (t.offsetTop + t.offsetHeight + 14) + 'px'; },
      upd(tl, el) {
        aparece(el.querySelector('.tt'), tl, .05, { dy: 14 }); aparece(el.querySelector('.lg'), tl, .4, { dy: 10 });
        const im = el.querySelector('.qd'); if (!im) return;
        const f = 1 + Math.min(n - 1, Math.max(0, Math.floor(tl * fps)));
        if (im.dataset.f != f) { im.dataset.f = f; im.src = q.base + String(f).padStart(4, '0') + '.jpg'; return im.decode().catch(() => 0); }
      },
      textos: () => [p.titulo, ...(p.legenda || []).map(l => l.texto)],
    };
  });
})();
