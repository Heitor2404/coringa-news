/* TEMPO V2 — linha do tempo que ANDA: a câmera percorre as datas na ordem em que a fala as conta. */
(function () {
  const { esc, hl, clamp, lerp, eo, eo5, eio, back, aparece, caber, fmt } = V2.U;

  /* 12. linha_tempo.historica */
  V2.registrar({
    id: 'linha_tempo.historica', nome: 'Linha do tempo histórica', tratamento: 'arquivo', tom: 'escuro',
    objetivo: 'Mostrar uma sequência histórica e as distâncias entre as datas (progressão temporal real).',
    funcoes: ['sequencia_historica', 'datas', 'progressao'],
    params: { titulo: '≤ 36 (opcional)', eventos: '2–6 × {ano, texto ≤ 46, img? (foto do evento)}', escala: 'bool: espaçamento proporcional aos anos (padrão true quando ≤ 6 eventos)' },
    fundo: 'próprio (papel escuro de arquivo)', layout: 'eixo horizontal em y=820; câmera desliza para cada data; ano em serifa 128 px acima do eixo, texto abaixo; foto opcional 360×240 acima do ano',
    paleta: 'fundo #15110c, eixo creme 30%, progresso amarelo, anos creme/amarelo, texto branco', animacao: 'progresso corre no eixo; câmera centraliza a data falada; marcas de intervalo ("+25 anos") entre datas',
    duracao: [3.5, 6, 9], limites: { titulo: 36, texto: 46, eventos: 6 }, legenda: 'livre',
    area_segura: 'conteúdo entre y 340 e 1110; data atual sempre centrada em x≈440', legibilidade: 'ano 128 px; texto 40 px 700',
    rejeicao: ['datas fora de ordem', 'evento sem data nos fatos', 'um único evento (use lower_third/banner)'],
    transicao: 'mascara',
    exemplo: { params: { titulo: 'Um século de *canal*', eventos: [{ ano: 1881, texto: 'França começa a obra e fracassa' }, { ano: 1904, texto: 'EUA assumem a construção' }, { ano: 1914, texto: 'SS Ancon faz a 1ª travessia', img: '@ancon_1914' }, { ano: 1999, texto: 'Canal passa ao Panamá' }, { ano: 2016, texto: 'Eclusas novas, maiores' }] }, dur: 8, fala: 'A França começou em 1881, os Estados Unidos terminaram em 1914, e o Panamá assumiu em 1999.' },
  }, (p, ctx) => {
    const ev = (p.eventos || []).slice(0, 6).map(e => ({ ...e, ano: +e.ano }));
    const n = ev.length, esc0 = p.escala !== false && n <= 6;
    const a0 = ev[0] ? ev[0].ano : 0, a1 = ev[n - 1] ? ev[n - 1].ano : 1;
    // posição no eixo virtual: proporcional (com espaço mínimo de 420 px) ou fixo
    const X = []; let x = 0; ev.forEach((e, i) => { if (i) { const d = esc0 ? clamp((e.ano - ev[i - 1].ano) / Math.max(1, a1 - a0) * 2400, 470, 820) : 520; x += d; } X.push(x); });
    const Y = 880, CX = 420;
    return {
      html: `<div class="abs" style="inset:0;background:radial-gradient(ellipse at 40% 45%,#2a2117 0%,#15110c 70%)"></div>
        <div class="abs" data-deco="1" style="inset:0;opacity:.25;background:repeating-linear-gradient(90deg,rgba(255,240,210,.05) 0 1px,transparent 1px 120px)"></div>
        ${p.titulo ? `<div class="abs tt" data-g="tt" data-txt="1" style="left:72px;right:150px;top:345px;font-family:var(--f-serif);font-weight:600;font-size:54px;line-height:1.1;color:#efe6d2">${hl(p.titulo)}</div><div class="abs" style="left:72px;top:420px;width:120px;height:3px;background:var(--amarelo)"></div>` : ''}
        <div class="abs trilho" style="left:0;top:0;width:${X[n - 1] + 2000}px;height:1920px">
          <div class="abs" style="left:-1000px;top:${Y}px;width:${X[n - 1] + 3000}px;height:4px;background:rgba(239,230,210,.25)"></div>
          <div class="abs prog" style="left:-1000px;top:${Y - 1}px;height:6px;width:0;background:var(--amarelo);box-shadow:0 0 18px rgba(255,210,31,.6)"></div>
          ${ev.map((e, i) => `<div class="abs ev ev${i}" data-g="ev${i}" style="left:${X[i]}px;top:0;width:0;height:1920px">
              <div class="abs" style="left:-14px;top:${Y - 12}px;width:28px;height:28px;border-radius:50%;background:#15110c;border:5px solid var(--amarelo)"></div>
              ${e.img ? `<div class="abs" style="left:0;top:${Y - 430}px;width:320px;height:220px;padding:10px;background:#efe6d2;box-shadow:0 20px 40px rgba(0,0,0,.5);transform:rotate(-1.5deg)"><div style="width:300px;height:200px;background:url('${e.img}') center/cover;filter:sepia(.3) contrast(1.05)"></div></div>` : ''}
              <div class="abs ano" data-txt="1" style="left:0;top:${Y - 180}px;font-family:var(--f-serif);font-weight:700;font-size:128px;line-height:1;color:#efe6d2;white-space:nowrap">${esc(e.ano)}</div>
              <div class="abs tx" data-txt="1" style="left:0;top:${Y + 44}px;width:430px;font-weight:700;font-size:40px;line-height:1.15;color:#fff">${hl(e.texto)}</div></div>`).join('')}
          ${ev.slice(1).map((e, i) => `<div class="abs gap gap${i}" data-g="gap${i}" data-opcional="1" style="left:${(X[i] + X[i + 1]) / 2 - 90}px;width:180px;text-align:center;top:${Y - 50}px;font-family:var(--f-dado);font-size:26px;color:rgba(239,230,210,.7)">+${e.ano - ev[i].ano} anos</div>`).join('')}
        </div>`,
      upd(tl, el, c) {
        const d = c.dur, t0 = .3, passo = (d - 1.2) / Math.max(1, n - 1);
        // posição da câmera: anda de evento em evento (assenta em cada um), em vez de deslizar sem parar
        const f = clamp((tl - t0) / passo, 0, n - 1), i = Math.floor(f), fr = f - i;
        const xs = i >= n - 1 ? X[n - 1] : lerp(X[i], X[i + 1], eio(clamp((fr - .45) / .55)));
        el.querySelector('.trilho').style.transform = `translateX(${CX - xs}px)`;
        el.querySelector('.prog').style.width = (xs + 1000) + 'px';
        ev.forEach((e, j) => { const on = clamp((xs - X[j] + 60) / 60); const ee = el.querySelector('.ev' + j);
          const sx = CX - xs + X[j], inteiro = sx > 40 && sx + 440 < 1050;
          ee.querySelector('.ano').style.color = on > .5 ? 'var(--amarelo)' : '#efe6d2'; ee.style.opacity = inteiro ? .35 + .65 * on : .28;
          const tx = ee.querySelector('.tx'); tx.style.opacity = inteiro ? on : 0; tx.style.transform = `translateY(${(1 - on) * 20}px)`;
          // datas fora do quadro somem; datas cortadas pela borda ficam apagadas (contexto), nunca como texto principal
          ee.style.visibility = sx > -460 && sx < 1080 ? 'visible' : 'hidden'; });
        el.querySelectorAll('.gap').forEach((g, j) => { const sx = CX - xs + (X[j] + X[j + 1]) / 2; g.style.opacity = sx > 80 && sx < 900 ? .9 : 0; });
        aparece(el.querySelector('.tt'), tl, .05, { dy: 14 });
      },
      textos: () => [p.titulo, ...ev.map(e => e.ano + ' ' + e.texto)],
    };
  });
})();
