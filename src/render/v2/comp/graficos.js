/* GRÁFICOS V2 (D3) — escalas reais, eixos legíveis, progressão sincronizada com a fala. */
(function () {
  const { esc, hl, clamp, lerp, eo, eo5, eio, aparece, caber, fmt } = V2.U;
  const H = V2.H;
  const papel = `<div class="abs" style="inset:0;background:var(--papel)"></div>`;
  const kick = t => `<div class="abs kicker" data-g="kicker" style="left:72px;top:352px;color:#141414"><span style="display:inline-block;width:14px;height:14px;background:var(--amarelo);outline:2px solid #141414;transform:rotate(45deg);margin-right:16px;vertical-align:2px"></span>${esc(t)}</div>`;

  /* 15. grafico.barras — barras horizontais (cabem rótulos longos no vertical), destaque e valor final */
  V2.registrar({
    id: 'grafico.barras', nome: 'Gráfico de barras animado', tratamento: 'dado', tom: 'claro',
    objetivo: 'Comparar 2–7 quantidades da mesma unidade e destacar a que importa para a história.',
    funcoes: ['comparacao', 'ranking'],
    params: { titulo: '≤ 44: O QUE é medido e em qual unidade', conclusao: 'a conclusão que o gráfico prova ≤ 60 (aparece quando a barra destacada termina)', itens: '2–7 × {rotulo ≤ 20, valor}', unidade: '≤ 10', destaque: 'índice da categoria citada na fala', ordenar: 'bool', fonte: 'obrigatória', nota: 'observação ≤ 60 (ex.: valores aproximados)' },
    fundo: 'próprio (papel)', layout: 'título 400–560; área do gráfico 600–1080 (D3 scaleBand/scaleLinear); valores na ponta da barra',
    paleta: 'barras tinta 85%; destaque amarelo com contorno; eixo fino', animacao: 'barras crescem em sequência (cada uma 0,7 s); valores contam',
    duracao: [3, 5, 7], limites: { titulo: 44, rotulo: 20, itens: 7 }, legenda: 'livre',
    area_segura: 'x 72–930', legibilidade: 'rótulos 30 px 700; valores 32 px mono',
    rejeicao: ['unidades diferentes', 'só 1 item (use numero.animado)', 'valores inventados (todos precisam de fonte)'],
    transicao: 'mascara',
    exemplo: { params: { titulo: 'Água por travessia (milhões de litros)', conclusao: 'As eclusas novas gastam *menos da metade*', unidade: 'mi L', destaque: 1, itens: [{ rotulo: 'Eclusas antigas', valor: 200 }, { rotulo: 'Eclusas novas', valor: 80 }, { rotulo: 'Piscina olímpica', valor: 2.5 }], fonte: 'DADOS ILUSTRATIVOS (galeria)', nota: 'Valores ilustrativos para demonstrar a composição.' }, dur: 5, fala: 'As eclusas novas gastam bem menos água.' },
  }, (p) => {
    let it = (p.itens || []).slice(0, 7).map((x, i) => ({ ...x, i, valor: +x.valor || 0 }));
    if (p.ordenar) it.sort((a, b) => b.valor - a.valor);
    const W = 858, x0 = 72, y0 = 600, y1 = p.conclusao ? 1030 : 1110;
    const y = d3.scaleBand().domain(it.map(d => d.i)).range([y0, y1]).padding(.28);
    const mx = d3.max(it, d => d.valor) || 1, x = d3.scaleLinear().domain([0, mx]).nice().range([0, W - 150]);
    const bw = y.bandwidth(), u = esc(p.unidade || '');
    return {
      html: `${papel}${kick('DADOS')}<div class="abs tt manchete" data-g="tt" data-txt="1" style="left:72px;right:150px;top:400px;font-size:58px;color:#141414;letter-spacing:-1px">${hl(p.titulo || '')}</div>
        <svg class="abs" style="left:0;top:0" width="1080" height="1920">
          ${x.ticks(4).map(v => `<line x1="${x0 + x(v)}" x2="${x0 + x(v)}" y1="${y0 - 10}" y2="${y1}" stroke="rgba(20,20,20,.12)" stroke-width="2"/>`).join('')}
          <line x1="${x0}" x2="${x0}" y1="${y0 - 10}" y2="${y1}" stroke="#141414" stroke-width="3"/>
          ${it.map(d => `<rect class="b b${d.i}" x="${x0}" y="${y(d.i) + bw * .42}" height="${bw * .58}" width="0" fill="${d.i === +p.destaque ? 'var(--amarelo)' : 'rgba(20,20,20,.82)'}" stroke="${d.i === +p.destaque ? '#141414' : 'none'}" stroke-width="3"/>`).join('')}
        </svg>
        ${it.map(d => `<div class="abs rb rb${d.i}" data-g="r${d.i}" style="left:${x0 + 4}px;top:${y(d.i) - 14}px;font-weight:${d.i === +p.destaque ? 900 : 700};font-size:34px;color:#141414">${esc(d.rotulo)}</div>
          <div class="abs vb vb${d.i}" data-g="v${d.i}" style="top:${y(d.i) + bw * .42 + bw * .29 - 24}px;left:${x0 + 16}px;font-family:var(--f-dado);font-weight:700;font-size:38px;color:#141414;white-space:nowrap"></div>`).join('')}
        ${p.conclusao ? `<div class="abs conc" data-g="conc" data-txt="1" style="left:72px;right:150px;top:1060px;padding:14px 20px;border-left:10px solid var(--amarelo);background:rgba(20,20,20,.05);font-weight:800;font-size:40px;line-height:1.15;color:#141414;opacity:0">${hl(p.conclusao)}</div>` : ''}
        ${p.nota ? `<div class="abs" data-g="nota" data-opcional="1" style="right:150px;max-width:420px;text-align:right;top:1186px;font-family:var(--f-serif);font-style:italic;font-size:26px;color:#5f584c">${esc(p.nota)}</div>` : ''}
        ${H.fonte(p.fonte, true).replace('bottom:770px', 'bottom:703px;max-width:420px')}`,
      montar(el) { caber(el.querySelector('.tt'), { max: 58, min: 42, alt: 160 }); },
      upd(tl, el, ctx) {
        aparece(el.querySelector('.tt'), tl, .05, { dy: 16 });
        const passo = Math.min(.55, (ctx.dur - 1.8) / it.length);
        it.forEach((d, j) => { const k = eo5((tl - .4 - j * passo) / .7), w = x(d.valor) * k;
          el.querySelector('.b' + d.i).setAttribute('width', w);
          const v = el.querySelector('.vb' + d.i); v.textContent = fmt(d.valor * k, d.valor % 1 ? 1 : 0) + ' ' + (p.unidade || '');
          v.style.left = (x0 + w + 14) + 'px'; v.style.opacity = clamp((tl - .4 - j * passo) / .2);
          el.querySelector('.rb' + d.i).style.opacity = clamp((tl - .3 - j * passo) / .25); });
        // a conclusão entra quando todas as barras terminaram de crescer
        aparece(el.querySelector('.conc'), tl, .4 + it.length * passo + .6, { dx: -20, dy: 0 });
        aparece(el.querySelector('.chip-fonte'), tl, 1, { dy: 0 });
      },
      textos: () => [p.titulo, ...it.map(d => d.rotulo + ' ' + d.valor)],
    };
  });

  /* 16. grafico.temporal — série no tempo desenhada progressivamente, com anotação do ponto que a história conta */
  V2.registrar({
    id: 'grafico.temporal', nome: 'Gráfico temporal animado', tratamento: 'dado', tom: 'claro',
    objetivo: 'Mostrar como algo mudou ao longo do tempo e apontar o momento que importa.',
    funcoes: ['serie_temporal', 'tendencia'],
    params: { titulo: '≤ 44: o que é medido (unidade)', conclusao: 'a mudança que importa ≤ 60', serie: '≥ 4 × [ano|data, valor]', unidade: '≤ 12', anotacao: '{x, texto ≤ 34}', periodo: '{de, ate, texto ≤ 24} faixa destacada (ex.: seca)', area: 'bool (preenche abaixo da linha)', zero: 'bool (padrão true: eixo começa no zero; false só com aviso)', fonte: 'obrigatória', sintetico: 'bool → selo "DADOS ILUSTRATIVOS"' },
    fundo: 'próprio (papel)', layout: 'título 400–540; plot 600–1060 × 72–930; eixo x com 4–6 marcas; anotação com fio até o ponto',
    paleta: 'linha tinta 6 px; área amarela 35%; ponto anotado vermelho', animacao: 'linha se desenha (stroke-dashoffset) da esquerda; valor corrente acompanha a ponta; anotação aparece quando a linha chega lá',
    duracao: [3.5, 5, 8], limites: { titulo: 44, anotacao: 34 }, legenda: 'livre',
    area_segura: 'x 72–930', legibilidade: 'eixos 26 px mono; anotação 32 px 800',
    rejeicao: ['menos de 4 pontos', 'eixo y cortado sem aviso (domínio começa em 0 por padrão)', 'série sem fonte'],
    transicao: 'mascara',
    exemplo: { params: { titulo: 'Nível do lago Gatún (m)', unidade: 'm', sintetico: true, area: true, serie: [[2019, 26.5], [2020, 26.7], [2021, 26.2], [2022, 26.4], [2023, 24.6], [2024, 25.3], [2025, 26.1]], anotacao: { x: 2023, texto: 'Seca com El Niño' }, periodo: { de: 2022.6, ate: 2023.8 }, conclusao: 'Na seca, o lago caiu *quase 2 m*', fonte: 'ilustrativo (valores aproximados)', zero: false }, dur: 5.5, fala: 'Em 2023, a seca derrubou o nível do lago.' },
  }, (p, ctx) => {
    const s = (p.serie || []).map(([a, b]) => [+a, +b]), W = 858, x0 = 72, y0 = 610, y1 = p.conclusao ? 1010 : 1090;
    const x = d3.scaleLinear().domain(d3.extent(s, d => d[0])).range([x0 + 40, x0 + W - 40]);
    const ext = d3.extent(s, d => d[1]); const y = d3.scaleLinear().domain(p.zero === false ? [ext[0] - (ext[1] - ext[0]) * .25, ext[1] + (ext[1] - ext[0]) * .2] : [0, ext[1] * 1.15]).nice().range([y1, y0]);
    const linha = d3.line().x(d => x(d[0])).y(d => y(d[1])).curve(d3.curveMonotoneX)(s);
    const area = d3.area().x(d => x(d[0])).y0(y1).y1(d => y(d[1])).curve(d3.curveMonotoneX)(s);
    const an = p.anotacao, pa = an && s.find(d => d[0] === +an.x);
    return {
      html: `${papel}${kick(p.sintetico ? 'DADOS ILUSTRATIVOS' : 'SÉRIE HISTÓRICA')}<div class="abs tt manchete" data-g="tt" data-txt="1" style="left:72px;right:150px;top:400px;font-size:58px;color:#141414;letter-spacing:-1px">${hl(p.titulo || '')}</div>
        <svg class="abs" style="left:0;top:0;overflow:visible" width="1080" height="1920">
          <defs><clipPath id="cl${ctx.i}"><rect class="clr" x="0" y="0" width="0" height="1920"/></clipPath></defs>
          ${y.ticks(4).map(v => `<line x1="${x0}" x2="${x0 + W}" y1="${y(v)}" y2="${y(v)}" stroke="rgba(20,20,20,.12)" stroke-width="2"/><text x="${x0}" y="${y(v) - 8}" font-family="JBM" font-size="28" fill="#5f584c">${fmt(v, v % 1 ? 1 : 0)}</text>`).join('')}
          ${p.periodo ? `<rect class="per" x="${x(+p.periodo.de)}" y="${y0 - 10}" width="${Math.max(8, x(+p.periodo.ate) - x(+p.periodo.de))}" height="${y1 - y0 + 10}" fill="rgba(210,47,31,.12)" opacity="0"/>` : ''}
          ${p.zero === false ? `<text x="${x0 + W}" y="${y1 - 10}" text-anchor="end" font-family="JBM" font-size="26" fill="#d22f1f">EIXO NÃO COMEÇA NO ZERO</text>` : ''}
          <line x1="${x0}" x2="${x0 + W}" y1="${y1}" y2="${y1}" stroke="#141414" stroke-width="3"/>
          ${s.filter((d, i) => s.length <= 7 || i % Math.ceil(s.length / 6) === 0).map(d => `<text x="${x(d[0])}" y="${y1 + 40}" text-anchor="middle" font-family="JBM" font-weight="700" font-size="30" fill="#141414">${d[0]}</text>`).join('')}
          <g clip-path="url(#cl${ctx.i})">${p.area ? `<path d="${area}" fill="rgba(255,210,31,.45)"/>` : ''}<path d="${linha}" fill="none" stroke="#141414" stroke-width="6" stroke-linejoin="round"/></g>
          <circle class="pt" r="12" fill="#141414" stroke="var(--papel)" stroke-width="4"/>
          ${pa ? `<g class="an" opacity="0"><line x1="${x(pa[0])}" x2="${x(pa[0])}" y1="${y(pa[1]) - 20}" y2="${y0 - 10}" stroke="#d22f1f" stroke-width="3" stroke-dasharray="8 6"/><circle cx="${x(pa[0])}" cy="${y(pa[1])}" r="14" fill="#d22f1f" stroke="var(--papel)" stroke-width="4"/></g>` : ''}
        </svg>
        <div class="abs vc" data-g="vc" style="font-family:var(--f-dado);font-weight:700;font-size:34px;color:#141414;background:var(--papel);padding:2px 8px"></div>
        ${pa ? `<div class="abs ant" data-g="ant" data-txt="1" style="left:${clamp(x(pa[0]) - 200, 72, 930 - 400)}px;width:400px;top:${y0 - 70}px;text-align:center;font-weight:800;font-size:32px;color:#d22f1f;opacity:0">${esc(an.texto)}</div>` : ''}
        ${p.conclusao ? `<div class="abs conc" data-g="conc" data-txt="1" style="left:72px;right:150px;top:1075px;padding:14px 20px;border-left:10px solid #d22f1f;background:rgba(20,20,20,.05);font-weight:800;font-size:40px;line-height:1.15;color:#141414;opacity:0">${hl(p.conclusao)}</div>` : ''}
        ${H.fonte(p.fonte, true).replace('bottom:770px', 'bottom:700px')}`,
      montar(el) { caber(el.querySelector('.tt'), { max: 58, min: 42, alt: 150 }); },
      upd(tl, el, ctx) {
        aparece(el.querySelector('.tt'), tl, .05, { dy: 16 });
        // a linha termina em 75% da cena: o fim fica parado para ler a conclusão
        const k = eio((tl - .4) / Math.max(1.5, ctx.dur * .75 - .4)), xa = lerp(x.range()[0] - 20, x.range()[1] + 20, k);
        el.querySelector('.clr').setAttribute('width', xa);
        const xv = x.invert(clamp(xa, x.range()[0], x.range()[1])); let i = s.findIndex(d => d[0] >= xv); if (i < 1) i = 1;
        const a = s[i - 1], b = s[i] || a, f = b[0] === a[0] ? 0 : (xv - a[0]) / (b[0] - a[0]), yv = lerp(a[1], b[1], clamp(f));
        const pt = el.querySelector('.pt'); pt.setAttribute('cx', x(xv)); pt.setAttribute('cy', y(yv)); pt.style.opacity = tl > .4 ? 1 : 0;
        const vc = el.querySelector('.vc'); vc.textContent = fmt(yv, 1) + ' ' + (p.unidade || ''); vc.style.left = clamp(x(xv) + 18, 72, 780) + 'px'; vc.style.top = (y(yv) - 62) + 'px'; vc.style.opacity = tl > .5 && k < 1 ? 1 : 0;
        if (pa) { const on = clamp((x(xv) - x(pa[0]) + 5) / 30); el.querySelector('.an').setAttribute('opacity', on); el.querySelector('.ant').style.opacity = on; }
        const per = el.querySelector('.per'); if (per) per.setAttribute('opacity', clamp((x(xv) - x(+p.periodo.de)) / 30));
        aparece(el.querySelector('.conc'), tl, Math.max(1.5, ctx.dur * .75), { dx: -20, dy: 0 });
        aparece(el.querySelector('.chip-fonte'), tl, 1, { dy: 0 });
      },
      textos: () => [p.titulo, an && an.texto],
    };
  });
})();
