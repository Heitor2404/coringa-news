/* MECANISMOS V2 — o acontecimento físico desenhado e animado (corte esquemático), não uma foto genérica nem texto.
 * mecanismo.eclusa: navio entra, comporta fecha, a água DO LAGO DESCE POR GRAVIDADE pelo túnel e enche a câmara, o
 * navio sobe junto com o nível (régua em metros), comporta da frente abre, navio sai. Sentido 'descer' = o inverso.
 * evento.impacto: explosão/impacto/onda de choque em esquema com anéis de alcance em escala.                      */
(function () {
  const { esc, hl, clamp, lerp, eo, eo5, eio, back, aparece, caber, fmt } = V2.U;

  V2.registrar({
    id: 'mecanismo.eclusa', nome: 'Mecanismo físico animado: eclusa', tratamento: 'ciencia', tom: 'escuro',
    objetivo: 'Mostrar a água subindo e o navio sendo elevado dentro da câmara, e de onde vem a água (gravidade, sem bombas).',
    funcoes: ['mecanismo', 'agua_subindo', 'elevacao_vertical', 'agua_descendo', 'eclusa'],
    params: { sentido: "'subir' | 'descer'", desnivel_m: 'desnível em metros (dos fatos)', lago: 'nome do nível alto ≤ 18', mar: 'nome do nível baixo ≤ 18',
      etapas: '3 textos ≤ 44 (entra · enche/esvazia · sai) — padrão em português', tempos: '3 segundos (na cena) em que cada etapa começa, alinhados à fala', kicker: '≤ 26' },
    fundo: 'próprio (prancheta técnica)', layout: 'cabeçalho com etapa atual 340–500; corte esquemático 520–1090 (mar à esquerda, câmara no meio, lago à direita); régua em metros na parede esquerda',
    paleta: 'água ciano translúcida; concreto azul-acinzentado; navio branco; fluxo em pontos brancos; GRAVIDADE em amarelo', animacao: 'navio desloca; comportas sobem/descem; fluxo no túnel; nível e navio sobem juntos; régua conta os metros',
    duracao: [4, 7, 12], limites: { etapa: 44, nome: 18 }, legenda: 'livre',
    area_segura: 'y 340–1095; x 40–1040 (o desenho pode encostar nas bordas; textos até 930)', legibilidade: 'etapa 46 px 900; rótulos 28 px mono; régua 30 px mono',
    rejeicao: ['desnível que não está nos fatos', 'cena de mecanismo trocada por foto parada (o fiscal_v2 bloqueia quando a fala descreve o mecanismo)'],
    problemas_conhecidos: ['comportas desenhadas como comportas de levantar (a de Panamá é de duas folhas que giram): simplificação do corte lateral, registrada'],
    transicao: 'mascara',
    exemplo: { params: { sentido: 'subir', desnivel_m: 26, lago: 'LAGO GATÚN', mar: 'MAR DO CARIBE', kicker: 'MECANISMO · ECLUSA' }, dur: 9,
      fala: 'O navio entra e a comporta fecha. A água do lago desce por gravidade e enche a câmara. O navio sobe vinte e seis metros e segue.' },
  }, (p, ctx) => {
    const subir = p.sentido !== 'descer', D = +p.desnivel_m || 26;
    const YB = 1050, YL = 980, YH = 680, CX0 = 300, CX1 = 780, TOPO = 640;     // fundo, nível baixo, nível alto, câmara
    const ET = p.etapas || (subir ? ['O navio entra e a comporta fecha', 'A água do lago desce e enche a câmara', 'Nível igual: a comporta abre'] : ['O navio entra pelo lado alto', 'A câmara esvazia para o mar', 'Nível igual: o navio desce e sai']);
    const navio = `<g class="nav"><path d="M-170 0 H170 L148 56 H-150 Z" fill="#e9eef7"/><path d="M-160 36 H160 L150 56 H-150 Z" fill="#b3261e"/>
      <rect x="-120" y="-40" width="150" height="40" fill="#dfe6f2"/><rect x="50" y="-78" width="90" height="78" fill="#f2f5fa"/><rect x="60" y="-70" width="70" height="14" fill="#2b3a4a"/>
      ${[-110, -78, -46, -14].map(x => `<rect x="${x}" y="-66" width="28" height="26" fill="#f0b429" stroke="#8a6a12" stroke-width="2"/>`).join('')}</g>`;
    return {
      html: `<div class="grade"></div>
        <div class="abs kicker" data-g="kicker" style="left:72px;top:345px;color:var(--ciano)"><span style="display:inline-block;width:14px;height:14px;border:3px solid var(--ciano);transform:rotate(45deg);margin-right:16px;vertical-align:2px"></span>${esc(p.kicker || 'MECANISMO')}</div>
        <div class="abs pas" data-g="pas" style="left:72px;top:392px;display:flex;gap:10px">${[0, 1, 2].map(i => `<div class="pd pd${i}" style="width:90px;height:8px;background:rgba(127,227,240,.25)"></div>`).join('')}</div>
        ${ET.map((t, i) => `<div class="abs et et${i}" data-g="et" data-txt="1" style="left:72px;right:150px;top:420px;font-weight:900;font-size:46px;line-height:1.08;text-transform:uppercase;opacity:0"><span style="font-family:var(--f-dado);color:var(--ciano);margin-right:14px">${i + 1}</span>${hl(t)}</div>`).join('')}
        <svg class="abs cv" style="left:0;top:0" width="1080" height="1920">
          <defs><linearGradient id="ag${ctx.i}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3FD0E0" stop-opacity=".55"/><stop offset="1" stop-color="#0f6a7a" stop-opacity=".75"/></linearGradient>
            <pattern id="cc${ctx.i}" width="24" height="24" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="24" height="24" fill="#33424f"/><line x1="0" y1="0" x2="0" y2="24" stroke="#3d4e5c" stroke-width="10"/></pattern></defs>
          <!-- terreno e concreto -->
          <path d="M0 ${YB + 40} V${YB} H${CX0 - 20} V${TOPO} H${CX0} V${YB} H${CX1} V${TOPO} H${CX1 + 20} V${YH + 90} H1080 V${YB + 40} Z" fill="url(#cc${ctx.i})" stroke="#7fa3b8" stroke-width="3"/>
          <!-- túnel (aqueduto) por baixo da câmara -->
          <path class="tunel" d="${subir ? `M1040 ${YH + 150} V${YB + 25} H${CX0 + 60}` : `M${CX1 - 60} ${YB + 25} H40 V${YL + 40}`}" fill="none" stroke="#0a2027" stroke-width="34"/>
          ${[420, 540, 660].map(x => `<rect x="${x - 10}" y="${YB - 2}" width="20" height="30" fill="#0a2027"/>`).join('')}
          <path class="fluxo" d="${subir ? `M1040 ${YH + 150} V${YB + 25} H${CX0 + 60}` : `M${CX1 - 60} ${YB + 25} H40 V${YL + 40}`}" fill="none" stroke="#fff" stroke-width="8" stroke-dasharray="4 26" stroke-linecap="round" opacity="0"/>
          <circle class="valv" cx="${subir ? 1040 : 40}" cy="${subir ? YH + 230 : YL + 120}" r="22" fill="#0a2027" stroke="#FFD21F" stroke-width="5"/><line class="valvl" x1="${subir ? 1040 : 40}" y1="${subir ? YH + 214 : YL + 104}" x2="${subir ? 1040 : 40}" y2="${subir ? YH + 246 : YL + 136}" stroke="#FFD21F" stroke-width="6"/>
          <!-- águas: mar (baixo), lago (alto), câmara (varia) -->
          <rect x="0" y="${YL}" width="${CX0 - 20}" height="${YB - YL}" fill="url(#ag${ctx.i})"/>
          <rect x="${CX1 + 20}" y="${YH}" width="${1080 - CX1 - 20}" height="${90}" fill="url(#ag${ctx.i})"/>
          <rect class="cam" x="${CX0}" y="${YL}" width="${CX1 - CX0}" height="${YB - YL}" fill="url(#ag${ctx.i})"/>
          <path class="sup" fill="none" stroke="#bff5fb" stroke-width="3"/>
          <g class="bolhas">${Array.from({ length: 14 }, () => '<circle r="5" fill="none" stroke="#e8fdff" stroke-width="2"/>').join('')}</g>
          ${navio}
          <!-- comportas -->
          <rect class="cpE" x="${CX0 - 20}" y="${TOPO - 20}" width="20" height="${YB - TOPO + 20}" fill="#FFD21F" stroke="#0b0f17" stroke-width="3"/>
          <rect class="cpD" x="${CX1}" y="${TOPO - 20}" width="20" height="${YH + 90 - TOPO + 20}" fill="#FFD21F" stroke="#0b0f17" stroke-width="3"/>
          <!-- régua -->
          <line x1="${CX0 + 24}" y1="${YL}" x2="${CX0 + 24}" y2="${YH}" stroke="rgba(255,255,255,.55)" stroke-width="3"/>
          ${Array.from({ length: 6 }, (_, i) => `<line x1="${CX0 + 24}" x2="${CX0 + 44}" y1="${lerp(YL, YH, i / 5)}" y2="${lerp(YL, YH, i / 5)}" stroke="rgba(255,255,255,.55)" stroke-width="3"/>`).join('')}
          <!-- gravidade -->
          <g class="grav" opacity="0"><line x1="${subir ? 990 : 90}" y1="${subir ? YH + 110 : YL + 20}" x2="${subir ? 990 : 90}" y2="${subir ? YH + 210 : YL + 100}" stroke="#FFD21F" stroke-width="8" marker-end="url(#gv${ctx.i})"/></g>
          <defs><marker id="gv${ctx.i}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#FFD21F"/></marker></defs>
        </svg>
        <div class="abs" data-g="lago" style="left:${CX1 + 34}px;top:${YH - 54}px;font-family:var(--f-dado);font-weight:700;font-size:24px;color:#bff5fb">${esc(p.lago || 'LAGO')}<br><span style="color:var(--amarelo)">+${fmt(D, D % 1 ? 1 : 0)} m</span></div>
        <div class="abs" data-g="mar" style="left:24px;top:${YL - 66}px;font-family:var(--f-dado);font-weight:700;font-size:24px;color:#bff5fb">${esc(p.mar || 'MAR')}<br><span style="color:rgba(255,255,255,.7)">0 m</span></div>
        <div class="abs rv" data-g="regua" style="left:${CX0 + 54}px;font-family:var(--f-dado);font-weight:700;font-size:34px;color:#fff;background:rgba(5,20,26,.8);padding:2px 10px;border-left:4px solid var(--amarelo)"></div>
        <div class="abs gt" data-g="grav" style="left:${subir ? 750 : 110}px;top:${subir ? YH + 300 : YL - 260}px;font-weight:900;font-size:34px;color:#FFD21F;opacity:0;text-align:${subir ? 'right' : 'left'};width:240px">GRAVIDADE<div style="font-family:var(--f-dado);font-weight:400;font-size:24px;color:#fff">sem bombas</div></div>
        <div class="abs" data-g="aviso" data-opcional="1" style="right:160px;top:1112px;font-family:var(--f-dado);font-size:24px;color:rgba(255,255,255,.5)">ESQUEMA · FORA DE ESCALA</div>`,
      upd(tl, el, c) {
        const d = c.dur, T = p.tempos || [.2, d * .3, d * .74];
        const f = tl < T[1] ? 0 : tl < T[2] ? 1 : 2;
        // nível da câmara: começa no nível de entrada e vai ao de saída durante a etapa 2
        const kN = eio(clamp((tl - T[1] - .5) / Math.max(1, T[2] - T[1] - .6)));
        const ent = subir ? YL : YH, sai = subir ? YH : YL, nivel = lerp(ent, sai, kN);
        const cam = el.querySelector('.cam'); cam.setAttribute('y', nivel); cam.setAttribute('height', YB - nivel);
        let sp = `M${CX0} ${nivel}`; for (let x = CX0; x <= CX1; x += 20) sp += ` L${x} ${nivel + Math.sin(x / 40 + tl * 4) * (kN > 0 && kN < 1 ? 5 : 2)}`; el.querySelector('.sup').setAttribute('d', sp);
        // navio: entra (etapa 1), sobe com a água (2), sai (3)
        const x0 = subir ? 90 : 990, xm = (CX0 + CX1) / 2, x1 = subir ? 1000 : 80;
        const kE = eio(clamp((tl - T[0]) / Math.max(.8, (T[1] - T[0]) * .7))), kS = eio(clamp((tl - T[2] - .5) / Math.max(.8, d - T[2] - .6)));
        const nx = tl < T[2] + .5 ? lerp(x0, xm, kE) : lerp(xm, x1, kS);
        const ny = (tl < T[1] ? ent : tl < T[2] + .5 ? nivel : sai) - 30 + Math.sin(tl * 1.8) * 3;
        el.querySelector('.nav').setAttribute('transform', `translate(${nx} ${ny}) rotate(${Math.sin(tl * 1.3) * .8})`);
        // comportas: a de trás fecha no fim da etapa 1; a da frente abre no início da etapa 3 (sobem para fora d'água)
        const atras = subir ? el.querySelector('.cpE') : el.querySelector('.cpD'), frente = subir ? el.querySelector('.cpD') : el.querySelector('.cpE');
        const kF = eo5(clamp((tl - (T[1] - .6)) / .5)), kA = eo5(clamp((tl - T[2]) / .5));
        atras.setAttribute('transform', `translate(0 ${-(1 - kF) * 260})`); atras.style.opacity = .35 + .65 * kF;
        frente.setAttribute('transform', `translate(0 ${-kA * 260})`); frente.style.opacity = 1 - .65 * kA;
        // fluxo pelo túnel: só com a válvula aberta (etapa 2)
        const flu = f === 1 && kN < 1, fl = el.querySelector('.fluxo'); fl.style.opacity = flu ? .9 : 0; fl.style.strokeDashoffset = -tl * 160;
        el.querySelector('.valvl').setAttribute('transform', `rotate(${f >= 1 ? 90 * eo5((tl - T[1]) / .4) : 0} ${subir ? 1040 : 40} ${subir ? YH + 230 : YL + 120})`);
        el.querySelector('.grav').setAttribute('opacity', f === 1 ? clamp((tl - T[1]) / .3) : 0); el.querySelector('.gt').style.opacity = f === 1 ? clamp((tl - T[1] - .2) / .3) : 0;
        el.querySelectorAll('.bolhas circle').forEach((b, i) => { const ph = (tl * .9 + i * .37) % 1, x = [420, 540, 660][i % 3] + Math.sin(i * 7 + tl * 3) * 16, y = lerp(YB - 10, nivel + 10, ph);
          b.setAttribute('cx', x); b.setAttribute('cy', y); b.setAttribute('opacity', flu && subir && y > nivel ? (1 - ph) * .9 : 0); });
        // régua em metros, acompanha a superfície
        const m = D * (YL - nivel) / (YL - YH), rv = el.querySelector('.rv'); rv.textContent = fmt(m, 0) + ' m'; rv.style.top = (nivel - 26) + 'px';
        // cabeçalho da etapa
        el.querySelectorAll('.et').forEach((e, i) => { e.style.opacity = i === f ? eo5((tl - T[i]) / .35) : 0; e.style.transform = `translateY(${i === f ? (1 - eo5((tl - T[i]) / .35)) * 16 : 0}px)`; });
        el.querySelectorAll('.pd').forEach((e, i) => e.style.background = i <= f ? 'var(--ciano)' : 'rgba(127,227,240,.25)');
      },
      textos: () => [...ET, p.lago, p.mar, String(D)],
    };
  });


  /* 18b. mecanismo.nivel — nível de líquido subindo/descendo num recipiente/região (enchente, maré, represa, tanque) */
  V2.registrar({
    id: 'mecanismo.nivel', nome: 'Mecanismo: nível subindo ou descendo', tratamento: 'ciencia', tom: 'escuro',
    objetivo: 'Mostrar a água (ou outro líquido) subindo/descendo e o que isso faz com o que está dentro (flutua, submerge).',
    funcoes: ['agua_subindo', 'agua_descendo', 'enchente', 'mare', 'nivel'],
    params: { titulo: '≤ 36', de: 'nível inicial (valor)', ate: 'nível final (valor)', max: 'altura total representada', unidade: "'m', 'cm'…", objeto: "'navio' | 'casa' | 'pessoa' | 'nenhum'", flutua: 'bool (objeto sobe com a água)', entrada: "'cima' | 'baixo' | 'lado' (de onde vem a água)", rotulo: 'o que é o líquido ≤ 20' },
    fundo: 'próprio (prancheta)', layout: 'corte de 860×520 em y 540–1060; régua à esquerda; objeto no centro; seta de entrada/saída',
    paleta: 'líquido ciano translúcido; régua branca; nível atual em amarelo', animacao: 'superfície ondula; nível vai de/até com desaceleração; objeto flutua ou fica submerso; régua conta',
    duracao: [3, 4.5, 7], limites: { titulo: 36, rotulo: 20 }, legenda: 'livre',
    area_segura: 'y 340–1095', legibilidade: 'régua 30 px mono',
    rejeicao: ['níveis sem fonte', 'objeto que a fala não cita'],
    transicao: 'mascara',
    exemplo: { params: { titulo: 'A maré sobe *até 16 m*', de: 1, ate: 16, max: 18, unidade: 'm', objeto: 'navio', flutua: true, entrada: 'lado', rotulo: 'MARÉ' }, dur: 5, fala: 'Na baía de Fundy, a maré sobe até dezesseis metros.' },
  }, (p, ctx) => {
    const X0 = 110, X1 = 970, Y0 = 560, YB = 1060, mx = +p.max || 10, de = +p.de || 0, ate = +p.ate || mx * .8;
    const Y = v => lerp(YB, Y0, clamp(v / mx)), u = esc(p.unidade || '');
    const obj = { navio: '<path d="M-120 0 H120 L100 44 H-104 Z" fill="#e9eef7"/><rect x="20" y="-56" width="70" height="56" fill="#dfe6f2"/>', casa: '<path d="M-80 0 V-90 L0 -150 L80 -90 V0 Z" fill="#dfe6f2" stroke="#0b0f17" stroke-width="3"/><rect x="-20" y="-50" width="40" height="50" fill="#33424f"/>', pessoa: '<circle cx="0" cy="-150" r="18" fill="#dfe6f2"/><rect x="-16" y="-130" width="32" height="80" rx="10" fill="#dfe6f2"/><rect x="-14" y="-50" width="10" height="50" fill="#dfe6f2"/><rect x="4" y="-50" width="10" height="50" fill="#dfe6f2"/>' }[p.objeto] || '';
    return {
      html: `<div class="grade"></div>
        <div class="abs kicker" data-g="kicker" style="left:72px;top:345px;color:var(--ciano)"><span style="display:inline-block;width:14px;height:14px;border:3px solid var(--ciano);transform:rotate(45deg);margin-right:16px;vertical-align:2px"></span>${esc(p.rotulo || 'NÍVEL')}</div>
        <div class="abs tt manchete" data-g="tt" data-txt="1" style="left:72px;right:150px;top:392px;font-size:60px">${hl(p.titulo || '')}</div>
        <svg class="abs" style="left:0;top:0" width="1080" height="1920">
          <rect x="${X0}" y="${Y0}" width="${X1 - X0}" height="${YB - Y0}" fill="none" stroke="#7fa3b8" stroke-width="4"/>
          <rect class="liq" x="${X0 + 2}" width="${X1 - X0 - 4}" fill="rgba(63,208,224,.35)"/><path class="sup" fill="none" stroke="#bff5fb" stroke-width="4"/>
          ${p.objeto && p.objeto !== 'nenhum' ? `<g class="ob">${obj}</g>` : ''}
          ${Array.from({ length: 6 }, (_, i) => `<line x1="${X0 - 24}" x2="${X0}" y1="${lerp(YB, Y0, i / 5)}" y2="${lerp(YB, Y0, i / 5)}" stroke="rgba(255,255,255,.6)" stroke-width="3"/><text x="${X0 - 30}" y="${lerp(YB, Y0, i / 5) + 9}" text-anchor="end" font-family="JBM" font-size="26" fill="rgba(255,255,255,.6)">${fmt(mx * i / 5, 0)}</text>`).join('')}
          <path class="ent" fill="none" stroke="#FFD21F" stroke-width="8" stroke-dasharray="6 18" stroke-linecap="round"/></svg>
        <div class="abs nv" data-g="nv" style="left:${X1 - 260}px;font-family:var(--f-dado);font-weight:700;font-size:40px;color:#0b0f17;background:var(--amarelo);padding:4px 14px"></div>`,
      montar(el) { caber(el.querySelector('.tt'), { max: 60, min: 44, alt: 140 }); },
      upd(tl, el, c) {
        aparece(el.querySelector('.tt'), tl, .05, { dy: 16 });
        const k = eio(clamp((tl - .6) / Math.max(1.2, c.dur - 1.6))), v = lerp(de, ate, k), y = Y(v);
        const lq = el.querySelector('.liq'); lq.setAttribute('y', y); lq.setAttribute('height', YB - y);
        let d = `M${X0 + 2} ${y}`; for (let x = X0; x <= X1; x += 20) d += ` L${x} ${y + Math.sin(x / 45 + tl * 4) * 5}`; el.querySelector('.sup').setAttribute('d', d);
        const ob = el.querySelector('.ob'); if (ob) ob.setAttribute('transform', `translate(540 ${p.flutua ? y - 18 + Math.sin(tl * 2) * 3 : YB})`);
        const nv = el.querySelector('.nv'); nv.textContent = fmt(v, v % 1 && v < 10 ? 1 : 0) + ' ' + (p.unidade || ''); nv.style.top = (y - 70) + 'px';
        const en = el.querySelector('.ent'), ativo = k > 0 && k < 1; en.style.opacity = ativo ? 1 : 0; en.style.strokeDashoffset = -tl * 120;
        en.setAttribute('d', p.entrada === 'cima' ? `M540 ${Y0 - 80} V${y - 10}` : p.entrada === 'baixo' ? `M540 ${YB + 30} V${YB - 40}` : `M${X1 + 60} ${(y + YB) / 2} H${X1 - 60}`);
      },
      textos: () => [p.titulo, p.rotulo],
    };
  });

  /* 25. evento.impacto — explosão/impacto representado em esquema: onda de choque com anéis de alcance */
  V2.registrar({
    id: 'evento.impacto', nome: 'Explosão / impacto em esquema', tratamento: 'ciencia', tom: 'escuro',
    objetivo: 'Representar uma explosão, impacto ou erupção mostrando o que ela FAZ (alcance, onda de choque), sem imagem sensacionalista.',
    funcoes: ['explosao', 'impacto', 'onda_de_choque', 'erupcao'],
    params: { titulo: '≤ 36', aneis: '1–4 × {raio_km, rotulo ≤ 26}', escala_km: 'km representados por 380 px', centro: 'nome do ponto ≤ 20' },
    fundo: 'próprio (prancheta)', layout: 'centro em (540, 800); anéis até 380 px; rótulos à direita dos anéis; barra de escala embaixo (y≈1060)',
    paleta: 'núcleo branco→amarelo→vermelho; anéis tracejados; frente de choque branca', animacao: 'clarão curto, frente de choque expande; anéis se fixam quando a frente passa; tremor de câmera de 0,4 s',
    duracao: [3, 4.5, 7], limites: { titulo: 36, rotulo: 26, aneis: 4 }, legenda: 'livre',
    area_segura: 'y 340–1100', legibilidade: 'rótulos 28 px 700',
    rejeicao: ['alcances sem fonte', 'uso para violência real recente sem contexto informativo'],
    transicao: 'flash',
    exemplo: { params: { titulo: 'Tunguska, *1908*', centro: 'EXPLOSÃO', escala_km: 40, aneis: [{ raio_km: 8, rotulo: 'raio ilustrativo' }, { raio_km: 26, rotulo: 'árvores derrubadas (≈)' }] }, dur: 5, fala: 'Em 1908, a explosão de Tunguska derrubou árvores num raio de trinta quilômetros.' },
  }, (p, ctx) => {
    const C = [540, 790], R = 380, sk = +p.escala_km || 10, an = (p.aneis || []).slice(0, 4).map(a => ({ ...a, r: R * (+a.raio_km) / sk }));
    const arvores = Array.from({ length: 220 }, (_, i) => { const a = i * 2.39996, d = 40 + ((i * 53) % 340); return [C[0] + Math.cos(a) * d, C[1] + Math.sin(a) * d, a]; });
    return {
      html: `<div class="grade"></div>
        <div class="abs kicker" data-g="kicker" style="left:72px;top:345px;color:var(--ciano)"><span style="display:inline-block;width:14px;height:14px;border:3px solid var(--ciano);transform:rotate(45deg);margin-right:16px;vertical-align:2px"></span>ALCANCE</div>
        <div class="abs tt manchete" data-g="tt" data-txt="1" style="left:72px;right:150px;top:392px;font-size:60px">${hl(p.titulo || '')}</div>
        <svg class="abs sv" style="left:0;top:0" width="1080" height="1920">
          <g class="arv">${arvores.map(([x, y, a]) => `<line x1="${x}" y1="${y}" x2="${x}" y2="${y - 16}" stroke="#4fa36a" stroke-width="4" data-a="${a}"/>`).join('')}</g>
          ${an.map((a, i) => `<circle class="an an${i}" cx="${C[0]}" cy="${C[1]}" r="${a.r}" fill="none" stroke="${i ? '#FFD21F' : '#FF4D3D'}" stroke-width="4" stroke-dasharray="12 10" opacity="0"/>`).join('')}
          <circle class="fr" cx="${C[0]}" cy="${C[1]}" r="0" fill="none" stroke="#fff" stroke-width="10" opacity="0"/>
          <circle class="nu" cx="${C[0]}" cy="${C[1]}" r="0" fill="url(#nu${ctx.i})"/>
          <defs><radialGradient id="nu${ctx.i}"><stop offset="0" stop-color="#fff"/><stop offset=".4" stop-color="#FFD21F"/><stop offset="1" stop-color="#FF4D3D" stop-opacity="0"/></radialGradient></defs>
          <line x1="72" x2="${72 + R / 2}" y1="1078" y2="1078" stroke="#fff" stroke-width="4"/><line x1="72" x2="72" y1="1068" y2="1088" stroke="#fff" stroke-width="4"/><line x1="${72 + R / 2}" x2="${72 + R / 2}" y1="1068" y2="1088" stroke="#fff" stroke-width="4"/></svg>
        <div class="abs" data-g="esc" style="left:${72 + R / 2 + 16}px;top:1060px;font-family:var(--f-dado);font-size:26px;color:#fff">${fmt(sk / 2, 0)} km</div>
        ${an.map((a, i) => `<div class="abs al al${i}" data-g="al${i}" style="left:${clamp(C[0] + a.r * .72 + 10, 100, 700)}px;top:${C[1] - a.r * .72 - 40}px;max-width:330px;font-weight:700;font-size:28px;line-height:1.1;color:${i ? '#FFD21F' : '#FF4D3D'};background:rgba(5,20,26,.8);padding:4px 10px;opacity:0">${esc(fmt(a.raio_km, 0) + ' km · ' + a.rotulo)}</div>`).join('')}
        <div class="abs" data-g="ct" style="left:${C[0] - 100}px;width:200px;top:${C[1] + 30}px;text-align:center;font-family:var(--f-dado);font-weight:700;font-size:26px;color:#fff">${esc(p.centro || '')}</div>`,
      upd(tl, el) {
        aparece(el.querySelector('.tt'), tl, .05, { dy: 16 });
        const t0 = .6, k = (tl - t0), rf = Math.max(0, k) * 240, mx = an.length ? an[an.length - 1].r : R;
        if (k > 0 && k < .25) window.__v2flash = .8 * (1 - k / .25);
        el.querySelector('.nu').setAttribute('r', k > 0 ? 60 + 40 * Math.exp(-k * 2) : 0);
        const fr = el.querySelector('.fr'); fr.setAttribute('r', rf); fr.setAttribute('opacity', k > 0 && rf < mx * 1.15 ? 1 - rf / (mx * 1.15) : 0);
        const sh = k > 0 && k < .4 ? (1 - k / .4) * 14 : 0; el.querySelector('.sv').style.transform = `translate(${Math.sin(tl * 61) * sh}px,${Math.cos(tl * 47) * sh}px)`;
        el.querySelectorAll('.arv line').forEach(l => { const x = +l.getAttribute('x1'), y = +l.getAttribute('y1'), d = Math.hypot(x - C[0], y - C[1]), a = Math.atan2(y - C[1], x - C[0]);
          const caiu = rf > d && d < mx; const q = caiu ? clamp((rf - d) / 60) : 0; l.setAttribute('x2', x + Math.cos(a) * 16 * q); l.setAttribute('y2', y - 16 * (1 - q) + Math.sin(a) * 16 * q); l.setAttribute('stroke', caiu ? (d < (an[0] || { r: 0 }).r ? '#3a2a1a' : '#8a7a3a') : '#4fa36a'); });
        an.forEach((a, i) => { const on = clamp((rf - a.r) / 40); el.querySelector('.an' + i).setAttribute('opacity', on); el.querySelector('.al' + i).style.opacity = on; });
      },
      textos: () => [p.titulo, ...an.map(a => a.rotulo)],
    };
  });
})();
