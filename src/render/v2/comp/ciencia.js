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
    const X0 = 72 + 115, X1 = 930 - 115, Y0 = 540 + 55, Y1 = 1080 - 55, nos = (p.nos || []).slice(0, 6), li = (p.ligacoes || []).slice(0, 7);
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
    const et = (p.etapas || []).slice(0, 5), n = et.length;
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
    params: { titulo: '≤ 36', objeto: "'navio' | 'caixa' | 'bola'", meio: "'agua' | 'ar'", forcas: '1–4 × {nome ≤ 14, angulo (graus, 90 = cima), intensidade 0–1, cor}', resultado: 'conclusão ≤ 40', movimento: 'bool (objeto anda na direção da resultante)' },
    fundo: 'próprio (prancheta)', layout: 'objeto no centro (540, 820); setas a partir do centro (até 260 px); conclusão em faixa y≈1020',
    paleta: 'setas em cores próprias por força; resultante tracejada branca', animacao: 'setas crescem uma a uma; resultante soma; objeto se move/equilibra',
    duracao: [3, 5, 7], limites: { titulo: 36, nome: 14, resultado: 40 }, legenda: 'livre',
    area_segura: 'y 340–1090', legibilidade: 'nomes das forças 32 px 800',
    rejeicao: ['intensidades sem relação com a física descrita', 'mais de 4 forças'],
    transicao: 'mascara',
    exemplo: { params: { titulo: 'Por que o navio *flutua*?', objeto: 'navio', meio: 'agua', forcas: [{ nome: 'Peso', angulo: -90, intensidade: .8, cor: '#FF4D3D' }, { nome: 'Empuxo', angulo: 90, intensidade: .8, cor: '#3FD0E0' }], resultado: 'Empuxo = Peso → equilíbrio' }, dur: 5, fala: 'O peso puxa para baixo e o empuxo da água empurra para cima.' },
  }, (p, ctx) => {
    const C = [540, 800], fs = (p.forcas || []).slice(0, 4), R = 270;
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
        const mv = p.movimento && !nul ? eio(clamp((tl - tr - .3) / 1.2)) : 0, bob = p.meio === 'agua' ? Math.sin(tl * 2) * 5 : 0;
        el.querySelector('.obj').setAttribute('transform', `translate(${C[0] + res[0] * .4 * mv} ${C[1] + res[1] * .4 * mv + bob})`);
        aparece(el.querySelector('.rs'), tl, tr + .3, { dy: 14 });
      },
      textos: () => [p.titulo, p.resultado, ...fs.map(f => f.nome)],
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
    const C = p.central || { nome: 'Sol', cor: '#FFD21F', raio: 60 }, O = p.orbitante || { nome: 'Planeta', cor: '#5B9BFF', raio: 20 };
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
