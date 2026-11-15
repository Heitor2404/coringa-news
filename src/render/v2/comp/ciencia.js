/* CIÊNCIA V2 — prancheta técnica (azul-petróleo, grade fina, linhas ciano): diagramas, processos, forças, órbitas. */
(function () {
  const { esc, hl, clamp, lerp, eo, eo5, eio, back, aparece, caber, fmt } = V2.U;
  const H = V2.H;
  const prancheta = `<div class="grade"></div>`;
  const titulo = (k, t) => `<div class="abs kicker" data-g="kicker" style="left:72px;top:345px;color:var(--ciano)"><span style="display:inline-block;width:14px;height:14px;border:3px solid var(--ciano);transform:rotate(45deg);margin-right:16px;vertical-align:2px"></span>${esc(k)}</div>
    ${t ? `<div class="abs tt manchete" data-g="tt" data-txt="1" style="left:72px;right:150px;top:392px;font-size:60px;letter-spacing:-1px">${hl(t)}</div>` : ''}`;
  const seta = (id, cor = 'var(--ciano)') => `<marker id="${id}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="${cor}"/></marker>`;

  /* 17. diagrama.explicativo — nós e ligações que se desenham em ordem (causa → efeito, partes de um sistema) */
  V2.registrar({
    id: 'diagrama.explicativo', nome: 'Diagrama explicativo', tratamento: 'ciencia', tom: 'escuro',
    objetivo: 'Explicar relações (causa → efeito, partes de um sistema, ciclo) desenhando-as na ordem da fala.',
    funcoes: ['diagrama', 'causa_efeito', 'sistema', 'ciclo'],
    params: { kicker: '≤ 20', titulo: '≤ 36', nos: '2–6 × {id, rotulo ≤ 18, x, y (0–1 na área), icone}', ligacoes: '1–7 × {de, para, rotulo ≤ 16}', ordem: 'ids na ordem da fala (opcional)' },
    fundo: 'próprio (prancheta)', layout: 'área do diagrama x 90–900, y 520–1080; nós de 230×110; setas curvas com rótulo no meio',
    paleta: 'nós contorno ciano 3 px, preenchimento petróleo; nó ativo com brilho; partículas de fluxo nas setas', animacao: 'nós aparecem na ordem; seta se desenha; pontos correm pela seta (fluxo)',
    duracao: [3, 5, 8], limites: { titulo: 36, rotulo: 18, nos: 6 }, legenda: 'livre',
    area_segura: 'y 340–1090', legibilidade: 'rótulos 32 px 800; rótulo de seta 26 px mono',
    rejeicao: ['diagrama decorativo sem relação causal real', 'mais de 6 nós (vira processo.etapas ou duas cenas)'],
    transicao: 'mascara',
    exemplo: { params: { kicker: 'CICLO DA ÁGUA DO CANAL', titulo: 'De onde vem a *água*?', nos: [{ id: 'chuva', rotulo: 'Chuva', x: .5, y: 0, icone: 'agua' }, { id: 'lago', rotulo: 'Lago Gatún', x: 0, y: .5, icone: 'montanha' }, { id: 'eclusa', rotulo: 'Eclusa', x: 1, y: .5, icone: 'navio' }, { id: 'mar', rotulo: 'Mar', x: .5, y: 1, icone: 'globo' }],
      ligacoes: [{ de: 'chuva', para: 'lago', rotulo: 'enche' }, { de: 'lago', para: 'eclusa', rotulo: 'gravidade' }, { de: 'eclusa', para: 'mar', rotulo: 'escoa' }, { de: 'mar', para: 'chuva', rotulo: 'evapora' }] }, dur: 6, fala: 'A chuva enche o lago, a água desce pela eclusa e vai para o mar.' },
  }, (p, ctx) => {
    const nos = (Array.isArray(p.nos) ? p.nos : []).slice(0, 6).map((n, i, a) => typeof n === 'string' || n.x === undefined ? { id: (n && n.id) || 'n' + i, rotulo: typeof n === 'string' ? n : (n.rotulo || n.nome || ''), x: a.length < 2 ? .5 : i / (a.length - 1), y: i % 2 ? .75 : .25, icone: (n && n.icone) || 'engrenagem' } : n);
    const X0 = 72 + 115, X1 = 930 - 115, Y0 = 540 + 55, Y1 = 1080 - 55, li = ((p.ligacoes && p.ligacoes.length) ? p.ligacoes : nos.slice(1).map((n, i) => ({ de: nos[i].id, para: n.id }))).slice(0, 7);
    const P = id => { const n = nos.find(x => x.id === id); return n ? [lerp(X0, X1, +n.x), lerp(Y0, Y1, +n.y)] : [540, 800]; };
    const curva = (a, b) => { const [x1, y1] = P(a), [x2, y2] = P(b), dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy) || 1;
      const ux = dx / L, uy = dy / L, ax = x1 + ux * Math.min(110, L * .3), ay = y1 + uy * Math.min(60, L * .3), bx = x2 - ux * Math.min(120, L * .3), by = y2 - uy * Math.min(66, L * .3);
      const mx = (ax + bx) / 2 - uy * 60, my = (ay + by) / 2 + ux * 60; return { d: `M${ax} ${ay} Q${mx} ${my} ${bx} ${by}`, m: [(ax + 2 * mx + bx) / 4, (ay + 2 * my + by) / 4] }; };
    const cs = li.map(l => curva(l.de, l.para));
    return {
      html: `${prancheta}${titulo(p.kicker || 'COMO FUNCIONA', p.titulo)}
        <svg class="abs" style="left:0;top:0;overflow:visible" width="1080" height="1920"><defs>${seta('sa' + ctx.i)}</defs>
          ${cs.map((c, i) => `<path class="lg lg${i}" d="${c.d}" fill="none" stroke="var(--ciano)" stroke-width="5" marker-end="url(#sa${ctx.i})"/>`).join('')}
          ${cs.map((c, i) => `<g class="fl fl${i}">${[0, 1, 2].map(() => '<circle r="7" fill="#fff"/>').join('')}</g>`).join('')}</svg>
        ${cs.map((c, i) => li[i].rotulo ? `<div class="abs lr lr${i}" data-g="lr${i}" style="left:${c.m[0]}px;top:${c.m[1]}px;transform:translate(-50%,-50%);font-family:var(--f-dado);font-weight:700;font-size:26px;color:var(--ciano);background:var(--tecnico);padding:2px 10px;white-space:nowrap">${esc(li[i].rotulo)}</div>` : '').join('')}
        ${nos.map((n, i) => { const [x, y] = P(n.id); return `<div class="abs no no${i}" data-g="no${i}" style="left:${x - 115}px;top:${y - 55}px;width:230px;height:110px;display:flex;align-items:center;gap:14px;padding:0 18px;border:3px solid var(--ciano);border-radius:14px;background:rgba(8,32,40,.92);color:#fff">
          <div style="flex:none;color:var(--ciano)">${H.icone(n.icone || 'engrenagem', { tam: 52 })}</div><div data-txt="1" style="font-weight:800;font-size:30px;line-height:1.05;text-transform:uppercase">${esc(n.rotulo)}</div></div>`; }).join('')}`,
      montar(el) { const t = el.querySelector('.tt'); if (t) caber(t, { max: 60, min: 44, alt: 140 });
        el.querySelectorAll('.lg').forEach(g => { const L = g.getTotalLength(); g.dataset.L = L; g.style.strokeDasharray = L; }); },
      upd(tl, el, c) {
        aparece(el.querySelector('.tt'), tl, .05, { dy: 16 });
        const ordem = p.ordem || [...new Set(li.flatMap(l => [l.de, l.para]))].concat(nos.map(n => n.id));
        const vistos = [...new Set(ordem)], passo = (c.dur - 1.4) / Math.max(1, li.length + 1);
        nos.forEach((n, i) => { const j = vistos.indexOf(n.id), t0 = .4 + Math.max(0, li.findIndex(l => l.para === n.id) + 1) * passo * (li.findIndex(l => l.para === n.id) >= 0 ? 1 : 0) - (li.findIndex(l => l.para === n.id) >= 0 ? .2 : 0);
          const e = el.querySelector('.no' + i), k = back((tl - t0) / .45); e.style.opacity = clamp((tl - t0) / .15); e.style.transform = `scale(${clamp(k, 0, 1.1)})`;
          const ativo = li.some((l, q) => l.para === n.id && tl > .4 + q * passo + passo * .6 && tl < .4 + (q + 1) * passo + passo * .6);
          e.style.boxShadow = ativo ? '0 0 40px rgba(63,208,224,.65)' : 'none'; });
        li.forEach((l, i) => { const g = el.querySelector('.lg' + i), L = +g.dataset.L, t0 = .4 + i * passo + passo * .3, k = eio((tl - t0) / .7);
          g.style.strokeDashoffset = L * (1 - k); g.style.opacity = k > 0 ? 1 : 0;
          const r = el.querySelector('.lr' + i); if (r) r.style.opacity = clamp((tl - t0 - .4) / .3);
          el.querySelectorAll(`.fl${i} circle`).forEach((cc, q) => { const ph = ((tl * .6 + q / 3) % 1); const pt = g.getPointAtLength(ph * L); cc.setAttribute('cx', pt.x); cc.setAttribute('cy', pt.y); cc.setAttribute('opacity', k >= 1 ? .9 * Math.sin(ph * Math.PI) : 0); }); });
      },
      textos: () => [p.titulo, ...nos.map(n => n.rotulo), ...li.map(l => l.rotulo)],
    };
  });

  /* 19. processo.etapas — processo científico por etapas, com a etapa atual em destaque */
  V2.registrar({
    id: 'processo.etapas', nome: 'Processo científico por etapas', tratamento: 'ciencia', tom: 'escuro',
    objetivo: 'Dar a sequência de um processo (biológico, químico, industrial) e mostrar em que etapa a fala está.',
    funcoes: ['processo', 'etapas', 'sequencia'],
    params: { kicker: '≤ 22', titulo: '≤ 36', etapas: '2–5 × {titulo ≤ 22, texto ≤ 60, icone}', tempos: 'opcional: segundo (da cena) em que cada etapa começa' },
    fundo: 'próprio (prancheta)', layout: 'trilho vertical em x=130 de y 540 a 1080; etapa ativa expandida (título 46 px + texto 34 px), demais recolhidas (título 32 px, 45%)',
    paleta: 'ciano para concluído/ativo; números em círculo; ícone grande da etapa ativa à direita (x 700–900)', animacao: 'progresso desce pelo trilho; etapa ativa abre; ícone da etapa troca com giro curto',
    duracao: [4, 6, 10], limites: { titulo: 22, texto: 60, etapas: 5 }, legenda: 'livre',
    area_segura: 'y 340–1090; x 72–930', legibilidade: 'título ativo 46 px 900; texto 34 px 600',
    rejeicao: ['etapas que a fala não percorre', 'mais de 5 etapas'],
    transicao: 'mascara',
    exemplo: { params: { kicker: 'BIOLOGIA', titulo: 'Como a planta faz *açúcar*', etapas: [{ titulo: 'Luz', texto: 'A clorofila capta a luz do sol', icone: 'sol' }, { titulo: 'Água', texto: 'As raízes trazem água; ela é quebrada', icone: 'agua' }, { titulo: 'CO₂', texto: 'O gás carbônico entra pelas folhas', icone: 'folha' }, { titulo: 'Glicose', texto: 'Tudo vira açúcar e sobra oxigênio', icone: 'atomo' }] }, dur: 7, fala: 'A folha capta luz, quebra a água, usa o gás carbônico e produz açúcar.' },
  }, (p, ctx) => {
    const et = (Array.isArray(p.etapas) ? p.etapas : []).slice(0, 5).map(e => typeof e === 'string' ? { titulo: e.split(/\s+/).slice(0, 3).join(' '), texto: e } : e), n = et.length;
    return {
      html: `${prancheta}${titulo(p.kicker || 'PROCESSO', p.titulo)}
        <div class="abs" style="left:126px;top:560px;width:6px;height:500px;background:rgba(127,227,240,.18)"></div>
        <div class="abs prg" style="left:126px;top:560px;width:6px;height:0;background:var(--ciano);box-shadow:0 0 16px var(--ciano)"></div>
        ${et.map((e, i) => `<div class="abs et et${i}" data-g="et${i}" style="left:92px;width:560px;display:flex;gap:30px;align-items:flex-start">
            <div class="nb" style="flex:none;width:76px;height:76px;border-radius:50%;border:4px solid var(--ciano);background:var(--tecnico);display:flex;align-items:center;justify-content:center;font-family:var(--f-dado);font-weight:700;font-size:30px;color:var(--ciano)">${i + 1}</div>
            <div style="padding-top:8px"><div class="et-t" data-txt="1" style="font-weight:900;font-size:34px;text-transform:uppercase;line-height:1">${esc(e.titulo)}</div>
            <div class="et-x" data-txt="1" style="font-weight:600;font-size:38px;line-height:1.2;color:rgba(255,255,255,.88);margin-top:12px;max-height:0;overflow:hidden">${hl(e.texto)}</div></div></div>`).join('')}
        <div class="abs icg" data-deco="1" style="left:680px;top:560px;width:240px;height:240px;color:var(--ciano)">${et.map((e, i) => `<div class="ic ic${i}" style="position:absolute;inset:0;opacity:0">${H.icone(e.icone || 'engrenagem', { tam: 240, esp: 2 })}</div>`).join('')}</div>`,
      upd(tl, el, c) {
        aparece(el.querySelector('.tt'), tl, .05, { dy: 16 });
        const ts = p.tempos || et.map((e, i) => .5 + i * (c.dur - 1) / n);
        let at = 0; ts.forEach((t, i) => { if (tl >= t) at = i; });
        // layout dinâmico: etapa ativa aberta, demais recolhidas, empilhadas a partir de y 540
        let y = 545;
        et.forEach((e, i) => { const box = el.querySelector('.et' + i), on = i === at, feito = i < at, kk = eo5((tl - ts[i]) / .45);
          const x = box.querySelector('.et-x'); x.style.maxHeight = on ? (lerp(0, 200, kk)) + 'px' : '0px';
          box.querySelector('.et-t').style.fontSize = (on ? lerp(38, 54, kk) : 38) + 'px';
          box.style.opacity = on ? 1 : feito ? .55 : (tl >= ts[i] - .1 ? 1 : .32); box.style.top = y + 'px';
          const nb = box.querySelector('.nb'); nb.style.background = feito || on ? 'var(--ciano)' : 'var(--tecnico)'; nb.style.color = feito || on ? 'var(--tecnico)' : 'var(--ciano)';
          y += box.offsetHeight + 30; });
        const ab = el.querySelector('.et' + at); el.querySelector('.prg').style.height = clamp((ab.offsetTop + 33) - 560, 0, 500) + 'px';
        et.forEach((e, i) => { const ic = el.querySelector('.ic' + i), k = eo5((tl - ts[i]) / .5); ic.style.opacity = i === at ? k : 0; ic.style.transform = `rotate(${(1 - k) * -40}deg) scale(${lerp(.6, 1, k)})`; });
      },
      textos: () => [p.titulo, ...et.map(e => e.titulo + ' ' + e.texto)],
    };
  });

  /* 26. forcas.vetores — vetores de força sobre um objeto; resultante e movimento */
  V2.registrar({
    id: 'forcas.vetores', nome: 'Vetores e forças', tratamento: 'ciencia', tom: 'escuro',
    objetivo: 'Mostrar por que algo flutua, cai, acelera ou fica parado: as forças como setas proporcionais.',
    funcoes: ['forca', 'fisica', 'equilibrio', 'movimento'],
    params: { titulo: '≤ 36', objeto: "'navio' | 'caixa' | 'bola'", meio: "'agua' | 'ar'", forcas: '1–4 × {nome ≤ 14, angulo (graus, 90 = cima), intensidade 0–1, cor}', resultado: 'conclusão ≤ 40', movimento: 'bool (padrão: anda quando as forças não se equilibram)' },
    fundo: 'próprio (prancheta)', layout: 'objeto no centro (540, 820); setas a partir do centro (até 260 px); conclusão em faixa y≈1020',
    paleta: 'setas em cores próprias por força; resultante tracejada branca', animacao: 'setas crescem uma a uma; resultante soma; objeto se move/equilibra',
    duracao: [3, 5, 7], limites: { titulo: 36, nome: 14, resultado: 40 }, legenda: 'livre',
    area_segura: 'y 340–1090', legibilidade: 'nomes das forças 32 px 800',
    rejeicao: ['intensidades sem relação com a física descrita', 'mais de 4 forças'],
    transicao: 'mascara',
    exemplo: { params: { titulo: 'Por que o navio *flutua*?', objeto: 'navio', meio: 'agua', forcas: [{ nome: 'Peso', angulo: -90, intensidade: .8, cor: '#FF4D3D' }, { nome: 'Empuxo', angulo: 90, intensidade: .8, cor: '#3FD0E0' }], resultado: 'Empuxo = Peso → equilíbrio' }, dur: 5, fala: 'O peso puxa para baixo e o empuxo da água empurra para cima.' },
  }, (p, ctx) => {
    // V2.4: o contrato pode trazer só o nome da força (ou a frase). Sem ângulo numérico, o sentido vem do nome;
    // sem nome reconhecível, a força não é desenhada (seta sem significado é pior que seta nenhuma).
    const SENT = [[/peso|gravid|queda/i, -90], [/empux|sustenta|normal|tra[cç][aã]o|elev|levant/i, 90], [/atrito|arrasto|resist/i, 180], [/impuls|motor|propul|empurr/i, 0]];
    const norm = f => { f = typeof f === 'string' ? { nome: f } : { ...f }; const nome = String(f.nome || '');
      if (!Number.isFinite(+f.angulo)) { const m = SENT.find(([r]) => r.test(nome)); if (!m) return null; f.angulo = m[1]; }
      f.angulo = +f.angulo; f.intensidade = Number.isFinite(+f.intensidade) && +f.intensidade > 0 ? Math.min(1, +f.intensidade) : .75;
      f.nome = nome.split(/\s+/).slice(0, 2).join(' '); return f; };
    const C = [540, 800], fs = (Array.isArray(p.forcas) ? p.forcas : []).map(norm).filter(Boolean).slice(0, 4), R = 270;
    const vec = f => [Math.cos(f.angulo * Math.PI / 180) * R * f.intensidade, -Math.sin(f.angulo * Math.PI / 180) * R * f.intensidade];
    const res = fs.reduce((a, f) => { const v = vec(f); return [a[0] + v[0], a[1] + v[1]]; }, [0, 0]);
    const obj = { navio: `<path d="M-150 0 H150 L120 60 H-130 Z" fill="#2b3a4a" stroke="#fff" stroke-width="4"/><rect x="20" y="-70" width="80" height="70" fill="#2b3a4a" stroke="#fff" stroke-width="4"/>`,
      caixa: `<rect x="-90" y="-90" width="180" height="180" fill="#2b3a4a" stroke="#fff" stroke-width="4"/>`, bola: `<circle r="90" fill="#2b3a4a" stroke="#fff" stroke-width="4"/>` }[p.objeto || 'caixa'];
    return {
      html: `${prancheta}${titulo('FORÇAS', p.titulo)}
        <svg class="abs" style="left:0;top:0;overflow:visible" width="1080" height="1920"><defs>${fs.map((f, i) => seta('fv' + ctx.i + i, f.cor || 'var(--ciano)')).join('')}${seta('fr' + ctx.i, '#fff')}</defs>
          ${p.meio === 'agua' ? `<rect class="agua" x="0" y="${C[1] + 10}" width="1080" height="${1100 - C[1] - 10}" fill="rgba(63,208,224,.16)"/><path class="onda" fill="none" stroke="var(--ciano)" stroke-width="3"/>` : ''}
          <g class="obj" transform="translate(${C[0]} ${C[1]})">${obj}</g>
          ${fs.map((f, i) => `<line class="fv fv${i}" x1="${C[0]}" y1="${C[1]}" x2="${C[0]}" y2="${C[1]}" stroke="${f.cor || 'var(--ciano)'}" stroke-width="12" stroke-linecap="round" marker-end="url(#fv${ctx.i}${i})"/>`).join('')}
          <line class="fr" x1="${C[0]}" y1="${C[1]}" x2="${C[0]}" y2="${C[1]}" stroke="#fff" stroke-width="5" stroke-dasharray="14 10" marker-end="url(#fr${ctx.i})" opacity="0"/></svg>
        ${fs.map((f, i) => { const v = vec(f); return `<div class="abs fn fn${i}" data-g="fn${i}" style="left:${clamp(C[0] + v[0] * 1.12 + (Math.abs(v[0]) < 20 ? 40 : 0), 80, 760)}px;top:${C[1] + v[1] * 1.12 - 20}px;font-weight:800;font-size:34px;color:${f.cor || 'var(--ciano)'};text-transform:uppercase;opacity:0">${esc(f.nome)}</div>`; }).join('')}
        ${p.resultado ? `<div class="abs rs eixo" data-g="rs" data-txt="1" data-centro="1" style="top:1060px;font-family:var(--f-dado);font-weight:700;font-size:36px;color:#fff;background:rgba(5,20,26,.85);padding:12px;border:2px solid var(--ciano)">${esc(p.resultado)}</div>` : ''}`,
      upd(tl, el, c) {
        aparece(el.querySelector('.tt'), tl, .05, { dy: 16 });
        const on = el.querySelector('.onda'); if (on) { let d = `M0 ${C[1] + 10}`; for (let x = 0; x <= 1080; x += 30) d += ` L${x} ${C[1] + 10 + Math.sin(x / 50 + tl * 3) * 6}`; on.setAttribute('d', d); }
        const passo = Math.min(.9, (c.dur - 2) / Math.max(1, fs.length));
        fs.forEach((f, i) => { const t0 = .5 + i * passo, k = eo5((tl - t0) / .5), v = vec(f), l = el.querySelector('.fv' + i);
          l.setAttribute('x2', C[0] + v[0] * k); l.setAttribute('y2', C[1] + v[1] * k); l.style.opacity = k > .02 ? 1 : 0; el.querySelector('.fn' + i).style.opacity = clamp((tl - t0 - .3) / .2); });
        const tr = .5 + fs.length * passo, kr = eo5((tl - tr) / .5), fr = el.querySelector('.fr');
        const nul = Math.hypot(res[0], res[1]) < 8;
        fr.setAttribute('x2', C[0] + res[0] * kr); fr.setAttribute('y2', C[1] + res[1] * kr); fr.setAttribute('opacity', nul ? 0 : kr);
        // V2.5: forças desequilibradas MOVEM o objeto na direção da resultante (padrão); em equilíbrio ele fica parado.
        // As setas e os nomes acompanham o objeto (antes a seta ficava solta no lugar e o objeto saía de baixo dela).
        const mv = (p.movimento ?? true) && !nul ? eio(clamp((tl - tr - .3) / 1.2)) : 0, bob = p.meio === 'agua' ? Math.sin(tl * 2) * 5 : 0;
        const dx = res[0] * .9 * mv, dy = res[1] * .9 * mv;          // desloca o bastante para o movimento ser visto
        el.querySelector('.obj').setAttribute('transform', `translate(${C[0] + dx} ${C[1] + dy + bob})`);
        el.querySelectorAll('.fv, .fr').forEach(l => l.setAttribute('transform', `translate(${dx} ${dy})`));
        el.querySelectorAll('.fn').forEach(n => { n.style.transform = `translate(${dx}px, ${dy}px)`; });
        aparece(el.querySelector('.rs'), tl, tr + .3, { dy: 14 });
      },
      textos: () => [p.titulo, p.resultado, ...fs.map(f => f.nome)],
    };
  });

  /* 28. mecanismo.estados (V2.4) — ESQUEMA ANIMADO GENÉRICO de um mecanismo: objetos 2D (superfície, corpo,
   * cerdas, ramos, partículas, seta) que mudam de ESTADO em estado (posição, escala, rotação, opacidade, polaridade)
   * e RELAÇÕES entre eles (atração, repulsão, contato, empurra) com intensidade. Mostra quem participa, o estado
   * inicial, o que muda, a relação causal/espacial e o estado resultante. Nada de lagartixa aqui: tudo vem dos dados
   * (Ever Given: canal + navio + vento; Tacoma: ponte + vento; adesão: espátula + parede + moléculas).
   * Sempre identificado na tela como ESQUEMA (não é foto nem microscopia). */
  const FORMAS = ['superficie', 'corpo', 'cerdas', 'ramos', 'particulas', 'seta'];
  V2.registrar({
    id: 'mecanismo.estados', nome: 'Mecanismo em estados (esquema animado)', tratamento: 'ciencia', tom: 'escuro',
    objetivo: 'Demonstrar um mecanismo: objetos identificados, estado inicial, mudança visível, relação causal/espacial e estado resultante.',
    funcoes: ['mecanismo', 'processo', 'causa_efeito', 'transformacao'],
    params: { kicker: '≤ 22', titulo: '≤ 36', esquema: '{objetos, estados, tempos}', objetos: `(dentro de esquema) 2–7 × {id, forma (${FORMAS.join('|')}), rotulo ≤ 18, x, y (0–1 na área), w, h (0–1), n, lado ('cima'|'baixo'), cor}`,
      estados: '(dentro de esquema) 2–4 × {rotulo ≤ 30, objetos: {id: {dx, dy (0–1), escala, rot (graus), opacidade, polar 0–1}}, relacoes: [{de, para, tipo atracao|repulsao|contato|empurra, forca 0–1, n, rotulo ≤ 16}]}', tempos: 'opcional: segundo de cada estado', limpa: 'bool: só as formas (uso como base de outra cena)' },
    fundo: 'próprio (prancheta)', layout: 'área x 90–990, y 560–1040; faixa de estados y 1050–1100; selo ESQUEMA no alto à direita',
    paleta: 'objetos petróleo com contorno ciano; atração amarela; repulsão vermelha; contato branco', animacao: 'objetos interpolam entre estados; relações aparecem/somem com a intensidade; faixa mostra INÍCIO → … → RESULTADO',
    duracao: [3, 5, 8], limites: { titulo: 36, rotulo: 18, estado: 30, objetos: 7, estados: 4 }, legenda: 'livre',
    area_segura: 'y 340–1100; x 72–990', legibilidade: 'rótulos 30 px 800; estado 32 px 800',
    rejeicao: ['estados iguais (nada muda)', 'objetos sem rótulo', 'relação entre objetos que não existem', 'apresentar como foto ou microscopia real'],
    transicao: 'mascara',
    exemplo: { params: { kicker: 'ESQUEMA · ADESÃO', titulo: 'Perto, as moléculas se *atraem*', esquema: {
      objetos: [{ id: 'par', forma: 'superficie', rotulo: 'PAREDE', x: .5, y: .08, w: 1, h: .13 }, { id: 'mp', forma: 'particulas', x: .55, y: .21, w: .78, n: 8 },
        { id: 'esp', forma: 'ramos', rotulo: 'ESPÁTULAS', x: .55, y: .8, w: .8, h: .32, n: 6, lado: 'cima' }, { id: 'me', forma: 'particulas', rotulo: 'MOLÉCULAS', x: .55, y: .6, w: .667, n: 6, preso_a: 'esp' }],
      estados: [{ rotulo: 'LONGE: SEM ATRAÇÃO', objetos: { esp: { dy: .08 } }, relacoes: [{ de: 'me', para: 'mp', tipo: 'atracao', forca: 0, n: 6 }] },
        { rotulo: 'ENCOSTA NA PAREDE', objetos: { esp: { dy: -.28 }, me: { polar: .5 }, mp: { polar: .5 } }, relacoes: [{ de: 'me', para: 'mp', tipo: 'atracao', forca: .6, n: 6 }] },
        { rotulo: 'AS MOLÉCULAS SE ATRAEM', objetos: { esp: { dy: -.32 }, me: { polar: 1 }, mp: { polar: 1 } }, relacoes: [{ de: 'me', para: 'mp', tipo: 'atracao', forca: 1, n: 6, rotulo: 'ATRAÇÃO' }] }] } },
      dur: 5, fala: 'Quando encosta, as moléculas das duas superfícies se atraem.' },
  }, (p, ctx) => {
    const c = p.esquema || p, ob = (c.objetos || []).filter(o => o && o.id && FORMAS.includes(o.forma)).slice(0, 7), es = (c.estados || []).slice(0, 4);
    const AX0 = 90, AX1 = 990, AY0 = 560, AY1 = 1030, W = AX1 - AX0, Hh = AY1 - AY0;
    const num = (v, d) => (v === undefined || v === null || isNaN(+v)) ? d : +v;
    const HPAD = { particulas: 40 / Hh, superficie: .1, seta: .25 };
    const base = o => ({ x: AX0 + num(o.x, .5) * W, y: AY0 + num(o.y, .5) * Hh, w: num(o.w, .4) * W, h: num(o.h, HPAD[o.forma] || .16) * Hh });
    const C = { linha: 'var(--ciano)', corpo: 'rgba(16,52,64,.95)', atracao: 'var(--amarelo)', repulsao: 'var(--vermelho)', contato: '#fff', empurra: 'var(--ciano)' };
    const forma = (o, b) => {
      const w = b.w, h = b.h, n = Math.max(1, Math.min(40, num(o.n, o.forma === 'particulas' ? 6 : 9))), cor = o.cor || C.linha, baixo = (o.lado || 'baixo') === 'baixo' ? 1 : -1;
      if (o.forma === 'superficie') return `<rect x="${-w / 2}" y="${-h / 2}" width="${w}" height="${h}" fill="rgba(140,170,180,.22)" stroke="${cor}" stroke-width="3"/>` +
        Array.from({ length: Math.ceil(w / 34) }, (_, i) => `<line x1="${-w / 2 + i * 34}" y1="${-h / 2}" x2="${-w / 2 + i * 34 + 22}" y2="${h / 2}" stroke="rgba(127,227,240,.28)" stroke-width="2"/>`).join('');
      if (o.forma === 'corpo') return `<rect x="${-w / 2}" y="${-h / 2}" width="${w}" height="${h}" rx="${Math.min(40, h / 2)}" fill="${C.corpo}" stroke="${cor}" stroke-width="4"/>`;
      if (o.forma === 'cerdas') { const top = -h / 2 * baixo; return `<line x1="${-w / 2}" y1="${top}" x2="${w / 2}" y2="${top}" stroke="${cor}" stroke-width="6" stroke-linecap="round"/>` +
        Array.from({ length: n }, (_, i) => { const x = -w / 2 + (i + .5) * w / n; return `<path class="cd" d="M${x} ${top} Q${x + 10} ${0} ${x + 4} ${h / 2 * baixo}" fill="none" stroke="${cor}" stroke-width="4" stroke-linecap="round"/>`; }).join(''); }
      if (o.forma === 'ramos') { const top = -h / 2 * baixo, mid = 0; let s = `<line x1="0" y1="${top}" x2="0" y2="${mid}" stroke="${cor}" stroke-width="10" stroke-linecap="round"/>`;
        for (let i = 0; i < n; i++) { const x = -w / 2 + (i + .5) * w / n, y2 = h / 2 * baixo; s += `<path d="M0 ${mid} Q${x * .4} ${(mid + y2) / 2} ${x} ${y2 - 10 * baixo}" fill="none" stroke="${cor}" stroke-width="5" stroke-linecap="round"/><rect class="ponta" x="${x - 18}" y="${y2 - 4 - (baixo < 0 ? 0 : 0)}" width="36" height="8" rx="3" fill="#fff"/>`; }
        return s; }
      if (o.forma === 'particulas') return Array.from({ length: n }, (_, i) => { const x = n === 1 ? 0 : -w / 2 + i * w / (n - 1);
        return `<g transform="translate(${x} 0)"><circle r="19" fill="rgba(91,155,255,.35)" stroke="var(--azul)" stroke-width="3"/><text class="pol" data-deco="1" x="0" y="8" text-anchor="middle" font-size="24" font-weight="800" fill="var(--amarelo)" opacity="0">${i % 2 ? '+' : '−'}</text></g>`; }).join('');
      if (o.forma === 'seta') { const L = h, a = num(o.angulo, -90) * Math.PI / 180, x2 = Math.cos(a) * L, y2 = -Math.sin(a) * L;
        return `<line x1="0" y1="0" x2="${x2}" y2="${y2}" stroke="${o.cor || 'var(--vermelho)'}" stroke-width="12" stroke-linecap="round" marker-end="url(#me${ctx.i})"/>`; }
      return '';
    };
    const B = Object.fromEntries(ob.map(o => [o.id, base(o)]));
    const estado = (k, id) => Object.assign({ dx: 0, dy: 0, escala: 1, rot: 0, opacidade: 1, polar: 0 }, ((es[k] || {}).objetos || {})[id] || {});
    const rels = [...new Set(es.flatMap(e => (e.relacoes || []).map(r => `${r.de}>${r.para}>${r.tipo || 'atracao'}`)))].map(k => { const [de, para, tipo] = k.split('>'); return { de, para, tipo }; })
      .filter(r => B[r.de] && B[r.para]);
    const relEm = (k, r) => ((es[k] || {}).relacoes || []).find(x => x.de === r.de && x.para === r.para && (x.tipo || 'atracao') === r.tipo);
    const NL = r => Math.max(1, Math.min(14, Math.max(...es.flatMap(e => e.relacoes || []).filter(x => x.de === r.de && x.para === r.para).map(x => num(x.n, 6)))));
    return {
      html: `${prancheta}${titulo(p.kicker || 'ESQUEMA', p.titulo)}
        <div class="abs" data-g="selo" style="right:150px;top:345px;font-family:var(--f-dado);font-weight:700;font-size:26px;color:rgba(255,255,255,.75);border:2px solid rgba(255,255,255,.35);padding:4px 10px">ESQUEMA · FORA DE ESCALA</div>
        <svg class="abs" style="left:0;top:0;overflow:visible" width="1080" height="1920"><defs><marker id="me${ctx.i}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="var(--vermelho)"/></marker>
          <marker id="ma${ctx.i}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="var(--amarelo)"/></marker>
          <marker id="mr${ctx.i}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="var(--vermelho)"/></marker></defs>
          ${ob.map((o, i) => `<g class="ob ob${i}">${forma(o, B[o.id])}</g>`).join('')}
          ${rels.map((r, j) => `<g class="rl rl${j}">${Array.from({ length: NL(r) }, (_, q) => `<line class="rq" stroke-linecap="round"/><line class="rq2" stroke-linecap="round"/>`).join('')}</g>`).join('')}</svg>
        ${ob.map((o, i) => o.rotulo ? `<div class="abs or or${i}" data-g="or${i}" data-txt="1" style="font-weight:800;font-size:30px;color:#fff;text-transform:uppercase;white-space:nowrap;background:rgba(5,20,26,.8);padding:2px 10px">${esc(o.rotulo)}</div>` : '').join('')}
        ${rels.map((r, j) => `<div class="abs rr rr${j}" data-g="rr${j}" data-txt="1" style="font-family:var(--f-dado);font-weight:700;font-size:28px;color:${r.tipo === 'repulsao' ? 'var(--vermelho)' : 'var(--amarelo)'};white-space:nowrap;opacity:0"></div>`).join('')}
        <div class="abs fx" data-g="fx" style="left:72px;right:90px;top:1060px;display:flex;align-items:center;gap:14px">
          ${es.map((e, k) => `<div class="fe fe${k}" style="flex:none;width:22px;height:22px;border-radius:50%;border:3px solid var(--ciano)"></div>`).join('')}
          <div class="fr" data-txt="1" style="flex:1;font-weight:800;font-size:32px;color:#fff;text-transform:uppercase;white-space:nowrap;overflow:hidden"></div></div>`,
      montar(el) {
        if (p.limpa) {   // usada como BASE (ex.: revelação sobre o resultado): só as formas, nenhum texto concorrendo
          el.querySelectorAll('div').forEach(d => { if (d.textContent.trim() || d.matches('.rr, .or, .fx, .fr')) d.style.display = 'none'; }); return;
        }
        const t = el.querySelector('.tt'); if (t) caber(t, { max: 60, min: 44, alt: 140 }); el.querySelectorAll('.or').forEach(r => caber(r, { max: 30, min: 26, larg: 520 })); },
      upd(tl, el, cc) {
        aparece(el.querySelector('.tt'), tl, .05, { dy: 16 });
        const n = Math.max(1, es.length), ts = p.tempos || (c.tempos) || es.map((e, k) => k === 0 ? 0 : .5 + k * (cc.dur - 1.2) / n);
        let k0 = 0; ts.forEach((t, k) => { if (tl >= t) k0 = k; });
        const k1 = Math.min(es.length - 1, k0 + 1), tr = k0 === k1 ? 1 : eio(clamp((tl - ts[k0]) / .7)), prev = Math.max(0, k0 - 1);
        const mix = (id, campo) => { const a = estado(k0 === 0 ? 0 : prev, id)[campo], b = estado(k0, id)[campo]; return k0 === 0 ? b : lerp(a, b, tr); };
        const atual = {}, pai = id => { const o = ob.find(x => x.id === id); return o && o.preso_a && B[o.preso_a] ? o.preso_a : null; };
        const desl = (id, campo) => mix(id, campo) + (pai(id) ? desl(pai(id), campo) : 0);
        ob.forEach((o, i) => { const b = B[o.id], dx = desl(o.id, 'dx') * W, dy = desl(o.id, 'dy') * Hh, es_ = mix(o.id, 'escala'), rot = mix(o.id, 'rot'), op = mix(o.id, 'opacidade'), pol = mix(o.id, 'polar');
          const x = b.x + dx, y = b.y + dy; atual[o.id] = { x, y, w: b.w * es_, h: b.h * es_, op };
          const g = el.querySelector('.ob' + i); g.setAttribute('transform', `translate(${x} ${y}) rotate(${rot}) scale(${es_})`); g.style.opacity = op * clamp((tl - .15 - i * .08) / .3);
          g.querySelectorAll('.pol').forEach(t => t.setAttribute('opacity', pol));
          const r = el.querySelector('.or' + i); if (r) {
            /* superfície: rótulo dentro, à esquerda; partículas: à esquerda da fileira; seta: ao lado do meio da seta; resto: à direita */
            const L = o.forma === 'superficie' ? x - b.w / 2 + 24 : o.forma === 'particulas' ? x - b.w * es_ / 2 - r.offsetWidth - 26
              : o.forma === 'seta' ? x + 26 : x + b.w * es_ / 2 + 18;
            const T = o.forma === 'seta' ? y + b.h * .45 - 22 : y - 22;
            r.style.left = clamp(L, 80, 990 - r.offsetWidth) + 'px';
            r.style.top = clamp(T, 520, 1010) + 'px'; r.style.opacity = op > .3 ? clamp((tl - .3 - i * .08) / .3) : 0; } });
        /* rótulos visíveis nunca se sobrepõem: o de baixo desce até ficar livre */
        const rs_ = [...el.querySelectorAll('.or')].filter(r => +r.style.opacity > .05).sort((a, b) => a.offsetTop - b.offsetTop);
        rs_.forEach((r, q) => { for (let j = 0; j < q; j++) { const o2 = rs_[j]; const sobre = !(r.offsetLeft > o2.offsetLeft + o2.offsetWidth || o2.offsetLeft > r.offsetLeft + r.offsetWidth);
          if (sobre && r.offsetTop < o2.offsetTop + o2.offsetHeight + 6) r.style.top = (o2.offsetTop + o2.offsetHeight + 6) + 'px'; } });
        rels.forEach((r, j) => { const A = atual[r.de], Bb = atual[r.para], fa = (relEm(prev, r) || {}).forca || 0, fb = (relEm(k0, r) || {}).forca || 0, f = k0 === 0 ? fb : lerp(fa, fb, tr);
          const g = el.querySelector('.rl' + j), cima = A.y > Bb.y, ya = A.y + (cima ? -A.h / 2 : A.h / 2), yb = Bb.y + (cima ? Bb.h / 2 : -Bb.h / 2);
          const xa0 = Math.max(A.x - A.w / 2, Bb.x - Bb.w / 2), xa1 = Math.min(A.x + A.w / 2, Bb.x + Bb.w / 2), qs = g.querySelectorAll('.rq'), q2 = g.querySelectorAll('.rq2'), N = qs.length;
          const cor = C[r.tipo] || C.atracao, mk = r.tipo === 'repulsao' ? `url(#mr${ctx.i})` : `url(#ma${ctx.i})`;
          /* quantas linhas aparecem neste estado (n do estado): a soma de atrações cresce/diminui de verdade na tela */
          const na = num((relEm(prev, r) || {}).n, N), nb = num((relEm(k0, r) || {}).n, (relEm(k0, r) ? N : 0)), nv = k0 === 0 ? nb : lerp(na, nb, tr);
          const ordem = Array.from({ length: N }, (_, q) => q).sort((a, b) => Math.abs(a - (N - 1) / 2) - Math.abs(b - (N - 1) / 2));
          qs.forEach((ln, q) => { const x = N === 1 ? (xa0 + xa1) / 2 : lerp(xa0 + 20, xa1 - 20, q / (N - 1)), m = (ya + yb) / 2, pul = .75 + .25 * Math.sin(tl * 6 + q);
            const vis = f * Math.min(1, A.op, Bb.op) * clamp(nv - ordem.indexOf(q)), atr = r.tipo !== 'repulsao';
            [[ln, ya], [q2[q], yb]].forEach(([L, y0]) => { L.setAttribute('x1', x); L.setAttribute('y1', atr ? y0 : m); L.setAttribute('x2', x); L.setAttribute('y2', atr ? lerp(y0, m, .85) : y0);
              L.setAttribute('stroke', cor); L.setAttribute('stroke-width', 2 + 5 * f); L.setAttribute('stroke-dasharray', r.tipo === 'contato' ? '0' : '10 8');
              L.setAttribute('marker-end', r.tipo === 'contato' ? '' : mk); L.setAttribute('opacity', vis * pul); }); });
          const rot = (es.flatMap(e => e.relacoes || []).find(x => x.de === r.de && x.para === r.para && x.rotulo) || {}).rotulo, rr = el.querySelector('.rr' + j);
          rr.textContent = rot || ''; const esq = xa0 - rr.offsetWidth - 20;
          rr.style.left = (esq >= 80 ? esq : clamp(xa1 + 16, 80, 990 - rr.offsetWidth)) + 'px'; rr.style.top = ((ya + yb) / 2 - 18) + 'px'; rr.style.opacity = rot ? clamp(f * 1.4) : 0;
          /* não cobre rótulo de objeto: troca de lado; se ainda cobrir, desce para baixo da fileira de baixo */
          const bate = () => [...el.querySelectorAll('.or')].some(o => +o.style.opacity > .05 && !(rr.offsetLeft > o.offsetLeft + o.offsetWidth + 4 || o.offsetLeft > rr.offsetLeft + rr.offsetWidth + 4
            || rr.offsetTop > o.offsetTop + o.offsetHeight + 2 || o.offsetTop > rr.offsetTop + rr.offsetHeight + 2));
          if (rot && bate()) { rr.style.left = clamp(xa1 + 16, 80, 990 - rr.offsetWidth) + 'px'; if (bate()) rr.style.top = (Math.max(ya, yb) + 14) + 'px'; } });
        es.forEach((e, k) => { const d = el.querySelector('.fe' + k); d.style.background = k <= k0 ? 'var(--ciano)' : 'transparent'; });
        const fr = el.querySelector('.fr'), rot = (es[k0] || {}).rotulo || '', tag = k0 === 0 ? 'INÍCIO · ' : k0 === es.length - 1 ? 'RESULTADO · ' : '';
        if (fr.dataset.k !== String(k0)) { fr.dataset.k = String(k0); fr.textContent = tag + rot; caber(fr, { max: 32, min: 26 }); }
        fr.style.opacity = clamp((tl - ts[k0]) / .3);
      },
      textos: () => [p.titulo, ...ob.map(o => o.rotulo), ...es.map(e => e.rotulo), ...es.flatMap(e => (e.relacoes || []).map(r => r.rotulo))],
    };
  });

  /* 27. astronomia.orbita — corpo central, órbita e período, em escala indicada */
  V2.registrar({
    id: 'astronomia.orbita', nome: 'Órbita (astronomia)', tratamento: 'ciencia', tom: 'escuro',
    objetivo: 'Mostrar movimento orbital, período e distância (planetas, luas, cometas, satélites).',
    funcoes: ['orbita', 'astronomia', 'movimento_celeste'],
    params: { titulo: '≤ 36', central: '{nome, cor, raio px}', orbitante: '{nome, cor, raio px}', excentricidade: '0–0,9', periodo: 'texto ≤ 24 ("365 dias")', distancia: 'texto ≤ 24', voltas: 'voltas na cena (padrão 1)', fora_de_escala: 'bool → aviso "TAMANHOS FORA DE ESCALA"' },
    fundo: 'próprio (céu escuro com estrelas fixas)', layout: 'órbita centrada em (540, 780), semi-eixo 360 px; rótulos de período/distância em placas abaixo (y≈1040)',
    paleta: 'preto-azulado; órbita tracejada ciano; rastro do orbitante', animacao: 'orbitante percorre a elipse (lei das áreas: mais rápido perto do foco); contador do período',
    duracao: [3, 5, 8], limites: { titulo: 36, periodo: 24, distancia: 24 }, legenda: 'livre',
    area_segura: 'y 340–1100', legibilidade: 'nomes 30 px 800; placas 32 px mono',
    rejeicao: ['escala sugerida como real quando não é (marque fora_de_escala)'],
    transicao: 'zoom',
    exemplo: { params: { titulo: 'Um ano é *uma volta*', central: { nome: 'Sol', cor: '#FFD21F', raio: 70 }, orbitante: { nome: 'Terra', cor: '#5B9BFF', raio: 22 }, excentricidade: .3, periodo: '365,25 dias', distancia: '150 milhões de km', fora_de_escala: true }, dur: 6, fala: 'A Terra leva um ano para dar uma volta no Sol.' },
  }, (p, ctx) => {
    const a = 360, e = clamp(+p.excentricidade || 0, 0, .9), b = a * Math.sqrt(1 - e * e), cx = 540, cy = 790, fx = cx + a * e;
    // V2.5 (auditoria renderizada): o contrato costuma trazer só {nome}; sem raio/cor o corpo central sumia (raio NaN)
    // e o nome ia para o topo da tela. Cada campo ausente cai num padrão desenhável; string vira {nome}.
    const corpo = (x, pad) => { x = typeof x === 'string' ? { nome: x } : (x && typeof x === 'object' ? x : {}); return {
      nome: x.nome || pad.nome, cor: x.cor || pad.cor, raio: Number.isFinite(+x.raio) && +x.raio > 0 ? clamp(+x.raio, 8, 90) : pad.raio }; };
    const C = corpo(p.central, { nome: 'Sol', cor: '#FFD21F', raio: 60 }), O = corpo(p.orbitante, { nome: 'Planeta', cor: '#5B9BFF', raio: 22 });
    const est = Array.from({ length: 90 }, (_, i) => `<circle cx="${(i * 197) % 1080}" cy="${(i * 331) % 1920}" r="${1 + (i % 3) * .7}" fill="#fff" opacity="${.15 + (i % 5) / 10}"/>`).join('');
    // anomalia excêntrica pela equação de Kepler (M = E − e·sen E): velocidade real ao longo da órbita
    const kepler = M => { let E = M; for (let i = 0; i < 8; i++) E = E - (E - e * Math.sin(E) - M) / (1 - e * Math.cos(E)); return E; };
    return {
      html: `<div class="abs" style="inset:0;background:radial-gradient(ellipse at 50% 40%,#0d1830 0%,#03060d 75%)"></div>
        <svg class="abs" style="left:0;top:0" width="1080" height="1920">${est}
          <ellipse cx="${cx}" cy="${cy}" rx="${a}" ry="${b}" fill="none" stroke="rgba(127,227,240,.45)" stroke-width="3" stroke-dasharray="10 10"/>
          <path class="rastro" fill="none" stroke="${O.cor}" stroke-width="6" stroke-linecap="round" opacity=".7"/>
          <defs><radialGradient id="gl${ctx.i}"><stop offset="0" stop-color="${C.cor}" stop-opacity=".55"/><stop offset="1" stop-color="${C.cor}" stop-opacity="0"/></radialGradient></defs><circle cx="${fx}" cy="${cy}" r="${C.raio * 2.6}" fill="url(#gl${ctx.i})"/><circle cx="${fx}" cy="${cy}" r="${C.raio}" fill="${C.cor}"/>
          <circle class="orb" r="${O.raio}" fill="${O.cor}" stroke="#fff" stroke-width="3"/></svg>
        ${titulo('ASTRONOMIA', p.titulo)}
        <div class="abs" data-g="nc" data-alinhamento="local" style="left:${fx - 100}px;width:200px;top:${cy + C.raio + 16}px;text-align:center;font-weight:800;font-size:30px;text-transform:uppercase;color:${C.cor}">${esc(C.nome)}</div>
        <div class="abs no" data-g="no" style="font-weight:800;font-size:30px;text-transform:uppercase;color:#fff;white-space:nowrap">${esc(O.nome)}</div>
        <div class="abs" data-g="pl" style="left:72px;right:150px;top:1036px;display:flex;gap:16px">
          ${p.periodo ? `<div class="pl1" data-txt="1" style="font-family:var(--f-dado);font-weight:700;font-size:30px;padding:10px 16px;border:2px solid var(--ciano);color:#fff">PERÍODO · <span class="pv">${esc(p.periodo)}</span></div>` : ''}
          ${p.distancia ? `<div data-txt="1" style="font-family:var(--f-dado);font-weight:700;font-size:30px;padding:10px 16px;border:2px solid rgba(255,255,255,.4);color:#fff">${esc(p.distancia)}</div>` : ''}</div>
        ${p.fora_de_escala ? `<div class="abs" data-g="esc" data-opcional="1" style="right:160px;top:984px;font-family:var(--f-dado);font-size:26px;color:rgba(255,255,255,.55)">TAMANHOS FORA DE ESCALA</div>` : ''}`,
      upd(tl, el, c) {
        aparece(el.querySelector('.tt'), tl, .05, { dy: 16 });
        const vt = +p.voltas || 1, M = clamp((tl - .4) / (c.dur - .8)) * vt * 2 * Math.PI, E = kepler(M % (2 * Math.PI) + (M >= 2 * Math.PI * vt ? 2 * Math.PI : 0));
        const ang = E + Math.PI, x = cx + a * Math.cos(ang) * -1 * -1, y = cy + b * Math.sin(ang);
        const X = cx - a * Math.cos(E), Y = cy + b * Math.sin(E);
        const o = el.querySelector('.orb'); o.setAttribute('cx', X); o.setAttribute('cy', Y);
        let d = ''; for (let q = 0; q <= 40; q++) { const Mq = Math.max(0, M - q * .05), Eq = kepler(Mq); d += (q ? 'L' : 'M') + (cx - a * Math.cos(Eq)) + ' ' + (cy + b * Math.sin(Eq)); }
        el.querySelector('.rastro').setAttribute('d', tl > .45 ? d : '');
        const no = el.querySelector('.no'); no.style.left = clamp(X + 30, 80, 800) + 'px'; no.style.top = clamp(Y - 60, 520, 960) + 'px';
      },
      textos: () => [p.titulo, p.periodo, p.distancia, O.nome, C.nome],
    };
  });
})();
