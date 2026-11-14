/* MECANISMOS V2 — o acontecimento físico desenhado e animado (corte esquemático), não uma foto genérica nem texto.
 * mecanismo.eclusa: navio entra, comporta fecha, a água DO LAGO DESCE POR GRAVIDADE pelo túnel e enche a câmara, o
 * navio sobe junto com o nível (régua em metros), comporta da frente abre, navio sai. Sentido 'descer' = o inverso.
 * evento.impacto: explosão/impacto/onda de choque em esquema com anéis de alcance em escala.                      */
(function () {
  const { esc, hl, clamp, lerp, eo, eo5, eio, back, aparece, caber, fmt } = V2.U;

  /* 18. mecanismo.eclusa — V2.1: corte lateral em ESCALA DE CELULAR, com direção de câmera (planos A–F) e física coerente:
   *  - a água entra/sai pelo TÚNEL com válvula (sistema hidráulico desenhado), nunca atravessando comporta fechada;
   *  - comporta só abre com os níveis iguais (o desenho calcula a diferença e trava a abertura);
   *  - o navio NÃO tem altura própria: a linha d'água do casco é a superfície da água em cada quadro;
   *  - o enchimento desacelera como na física (vazão ∝ √Δh: a diferença de nível cai como (1 − k)²).
   * Planos: A visão geral · B comporta fechando · C fluxo pelo túnel · D elevação (acompanha o navio) · E equalização ·
   * F saída. Os planos seguem os tempos da fala (params.tempos) e podem ser desligados (params.planos = false). */
  V2.registrar({
    id: 'mecanismo.eclusa', nome: 'Mecanismo físico animado: eclusa', tratamento: 'ciencia', tom: 'escuro',
    objetivo: 'Mostrar, sem áudio, por que o navio sobe: a água do nível alto desce pelo túnel por gravidade, enche a câmara fechada e levanta o navio; a comporta só abre com os níveis iguais.',
    funcoes: ['mecanismo', 'agua_subindo', 'elevacao_vertical', 'agua_descendo', 'eclusa'],
    params: { sentido: "'subir' | 'descer'", desnivel_m: 'desnível em metros (dos fatos)', lago: 'nome do nível alto ≤ 18', mar: 'nome do nível baixo ≤ 18',
      etapas: '3 textos ≤ 40 (entra/fecha · enche/esvazia · iguala/sai)', tempos: '3 segundos (na cena) em que cada etapa começa, alinhados à fala',
      planos: 'bool (padrão true): câmera dirigida A–F; false = só visão geral', kicker: '≤ 26',
      degraus: 'nº de câmaras REAIS em sequência que somam o desnível (ex.: 3 em Gatún). > 1 = aviso explícito + escada com o navio subindo todos os degraus' },
    fundo: 'próprio (prancheta técnica)', layout: 'cabeçalho 340–440 (etapa atual, 3 marcadores); corte esquemático 450–1210 em tela cheia; rótulos de estado (comportas, válvula, níveis) em HTML de tamanho fixo que acompanham a câmera',
    paleta: 'água ciano; concreto azul-acinzentado com textura; comportas amarelas; navio branco/vermelho; GRAVIDADE e Δh em amarelo', animacao: 'navio desloca → comporta fecha (plano B) → válvula abre, fluxo no túnel (plano C) → água e navio sobem juntos (plano D) → níveis iguais, comporta abre (plano E) → navio sai (plano F)',
    duracao: [5, 9, 16], limites: { etapa: 40, nome: 18 }, legenda: 'livre',
    area_segura: 'cabeçalho e rótulos dentro de x 72–930; desenho em tela cheia (pode encostar nas bordas)', legibilidade: 'etapa 52 px 900; rótulos de estado 30 px; nível 40 px mono',
    rejeicao: ['desnível que não está nos fatos', 'sentido (subir/descer) que contradiz a fala (fiscal_v2 S3)', 'cena de mecanismo trocada por foto parada (fiscal_v2 B2)'],
    problemas_conhecidos: ['corte lateral simplificado: as comportas aparecem como de levantar (no Panamá são de duas folhas que giram) e o túnel aparece sob a câmara (no Panamá corre dentro das paredes) — rotulado como ESQUEMA ILUSTRATIVO'],
    transicao: 'mascara',
    exemplo: { params: { sentido: 'subir', desnivel_m: 26, lago: 'LAGO GATÚN', mar: 'MAR DO CARIBE', kicker: 'MECANISMO · ECLUSA', tempos: [0, 3.2, 8.4] }, dur: 11,
      fala: 'O navio entra e a comporta fecha. A água do lago desce por gravidade e enche a câmara. O navio sobe vinte e seis metros e segue.' },
  }, (p, ctx) => {
    const subir = p.sentido !== 'descer', D = +p.desnivel_m || 26;
    // ---- mundo (unidades de desenho) ----
    const MW = 1480, TOPO = 290, YH = 340, YL = 650, FUNDO = 860, C0 = 360, C1 = 1060, PAR = 28, SOLEIRA = 570, TUN = 915;
    const PORTAS = [540, 720, 900];
    const TUN_ENCHE = `M1310 ${SOLEIRA} V${TUN} H${PORTAS[0] - 60}`, TUN_ESVAZIA = `M${PORTAS[2] + 60} ${TUN} H150 V${YL + 40}`;
    const ET = p.etapas || (subir ? ['O navio entra e a comporta de trás fecha', 'Água do lago desce pelo túnel e enche a câmara', 'Níveis iguais: a comporta da frente abre']
      : ['O navio entra pelo lado alto e a comporta fecha', 'A câmara esvazia pelo túnel para o mar', 'Níveis iguais: a comporta abre e o navio sai']);
    // ---- tela ----
    const SY = 535, SH = 675, SW = 1080, ASP = SW / SH;
    const navio = `<g class="nav">
      <path d="M-215 -26 H215 L190 50 H-198 Z" fill="#f2f5fa" stroke="#0b0f17" stroke-width="4"/>
      <path d="M-206 20 H206 L190 50 H-198 Z" fill="#c4302b"/>
      <rect x="80" y="-120" width="110" height="94" fill="#f7f9fc" stroke="#0b0f17" stroke-width="4"/>
      <rect x="92" y="-108" width="86" height="18" fill="#22313f"/>
      ${[-180, -138, -96, -54, -12, 30].map((x, k) => `<rect x="${x}" y="${k % 2 ? -66 : -64}" width="38" height="38" fill="${['#f0b429', '#3a86c8', '#e05a3a', '#f0b429', '#4caf7a', '#3a86c8'][k]}" stroke="#0b0f17" stroke-width="3"/>`).join('')}
      <line x1="150" y1="-120" x2="150" y2="-160" stroke="#0b0f17" stroke-width="5"/></g>`;
    const comporta = (cls, x, y0, y1) => `<g class="${cls}"><rect x="${x}" y="${y0}" width="${PAR}" height="${y1 - y0}" fill="#FFD21F" stroke="#0b0f17" stroke-width="4"/>
      ${Array.from({ length: Math.floor((y1 - y0) / 56) }, (_, k) => `<line x1="${x}" x2="${x + PAR}" y1="${y0 + 28 + k * 56}" y2="${y0 + 48 + k * 56}" stroke="#0b0f17" stroke-width="5"/>`).join('')}</g>`;
    const torre = x => `<rect x="${x - 14}" y="80" width="${PAR + 28}" height="${TOPO - 80}" fill="#42566a" stroke="#9fb6c8" stroke-width="3"/><rect x="${x - 14}" y="70" width="${PAR + 28}" height="14" fill="#9fb6c8"/>`;
    const html = `<div class="grade"></div>
      <div class="abs kicker" data-g="kicker" style="left:72px;top:345px;color:var(--ciano)"><span style="display:inline-block;width:14px;height:14px;border:3px solid var(--ciano);transform:rotate(45deg);margin-right:16px;vertical-align:2px"></span>${esc(p.kicker || 'MECANISMO · ECLUSA')}</div>
      <div class="abs pas" style="left:72px;top:388px;display:flex;gap:10px">${[0, 1, 2].map(i => `<div class="pd pd${i}" style="width:110px;height:10px;background:rgba(127,227,240,.25)"></div>`).join('')}</div>
      ${ET.map((t, i) => `<div class="abs et et${i}" data-g="et" data-txt="1" style="left:72px;right:150px;top:412px;font-weight:900;font-size:46px;line-height:1.04;text-transform:uppercase;opacity:0;text-shadow:0 3px 14px rgba(0,0,0,.6)"><span style="font-family:var(--f-dado);color:var(--ciano);margin-right:14px">${i + 1}</span>${hl(t)}</div>`).join('')}
      <svg class="abs cv" data-ocupa="1" style="left:0;top:${SY}px" width="${SW}" height="${SH}" viewBox="0 0 ${MW} ${MW / ASP}" preserveAspectRatio="xMidYMid slice">
        <defs><linearGradient id="ag${ctx.i}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4fd8e8" stop-opacity=".78"/><stop offset="1" stop-color="#0c6676" stop-opacity=".92"/></linearGradient>
          <pattern id="cc${ctx.i}" width="36" height="36" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="36" height="36" fill="#34495b"/><line x1="0" y1="0" x2="0" y2="36" stroke="#3e566a" stroke-width="12"/></pattern>
          <pattern id="rc${ctx.i}" width="60" height="40" patternUnits="userSpaceOnUse"><rect width="60" height="40" fill="#1d2a33"/><circle cx="14" cy="12" r="5" fill="#26353f"/><circle cx="44" cy="28" r="7" fill="#26353f"/></pattern>
          <marker id="sf${ctx.i}" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#fff"/></marker></defs>
        <rect x="-400" y="-400" width="${MW + 800}" height="1800" fill="none"/>
        <!-- rocha e concreto -->
        <rect x="-300" y="${FUNDO}" width="${MW + 600}" height="400" fill="url(#rc${ctx.i})"/>
        <path d="M${C1 + PAR} ${SOLEIRA} H${MW + 300} V${FUNDO} H${C1 + PAR} Z" fill="url(#rc${ctx.i})"/>
        <!-- túneis (aquedutos) e portas no piso da câmara -->
        <path d="${TUN_ENCHE}" fill="none" stroke="#08171d" stroke-width="44" stroke-linejoin="round"/>
        <path d="${TUN_ESVAZIA}" fill="none" stroke="#08171d" stroke-width="44" stroke-linejoin="round"/>
        ${PORTAS.map(x => `<rect x="${x - 16}" y="${FUNDO - 4}" width="32" height="${TUN - FUNDO + 4}" fill="#08171d"/>`).join('')}
        <path class="fl fl-enche" d="${TUN_ENCHE}" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" stroke-dasharray="6 34" opacity="0"/>
        <path class="fl fl-esvazia" d="${TUN_ESVAZIA}" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" stroke-dasharray="6 34" opacity="0"/>
        <!-- águas -->
        <rect x="-300" y="${YL}" width="${C0 - PAR + 300}" height="${FUNDO - YL}" fill="url(#ag${ctx.i})"/>
        <rect x="${C1 + PAR}" y="${YH}" width="${MW + 300 - C1 - PAR}" height="${SOLEIRA - YH}" fill="url(#ag${ctx.i})"/>
        <rect class="cam" x="${C0}" y="${YL}" width="${C1 - C0}" height="${FUNDO - YL}" fill="url(#ag${ctx.i})"/>
        <path class="sup" fill="none" stroke="#d6fbff" stroke-width="5"/>
        <g class="jatos">${PORTAS.map(() => '<path fill="none" stroke="#e8fdff" stroke-width="5" stroke-linecap="round"/>').join('')}</g>
        <!-- paredes da câmara -->
        <rect x="${C0 - PAR - 40}" y="${TOPO}" width="40" height="${YL - TOPO}" fill="url(#cc${ctx.i})" opacity="0"/>
        <rect x="${C0}" y="${FUNDO}" width="${C1 - C0}" height="10" fill="#9fb6c8"/>
        ${navio}
        ${torre(C0 - PAR)}${torre(C1)}
        ${comporta('cpE', C0 - PAR, TOPO, FUNDO)}${comporta('cpD', C1, TOPO, SOLEIRA)}
        <!-- válvulas -->
        <g class="vE"><circle cx="1310" cy="${(SOLEIRA + TUN) / 2}" r="34" fill="#0b0f17" stroke="#FFD21F" stroke-width="7"/><line class="vEl" x1="1310" y1="${(SOLEIRA + TUN) / 2 - 30}" x2="1310" y2="${(SOLEIRA + TUN) / 2 + 30}" stroke="#FFD21F" stroke-width="9"/></g>
        <g class="vS"><circle cx="300" cy="${TUN}" r="34" fill="#0b0f17" stroke="#FFD21F" stroke-width="7"/><line class="vSl" x1="270" y1="${TUN}" x2="330" y2="${TUN}" stroke="#FFD21F" stroke-width="9"/></g>
        <!-- régua e Δh -->
        <line x1="${C0 + 34}" y1="${YL}" x2="${C0 + 34}" y2="${YH}" stroke="rgba(255,255,255,.7)" stroke-width="4"/>
        ${Array.from({ length: 6 }, (_, k) => `<line x1="${C0 + 34}" x2="${C0 + 64}" y1="${lerp(YL, YH, k / 5)}" y2="${lerp(YL, YH, k / 5)}" stroke="rgba(255,255,255,.7)" stroke-width="4"/>`).join('')}
        <g class="delta"><line class="dl" x1="${C1 - 60}" x2="${C1 - 60}" stroke="#FFD21F" stroke-width="6"/><line class="dt" x1="${C1 - 80}" x2="${C1 - 40}" stroke="#FFD21F" stroke-width="6"/><line class="db" x1="${C1 - 80}" x2="${C1 - 40}" stroke="#FFD21F" stroke-width="6"/>
          <line x1="${C1 - 60}" x2="${MW + 300}" y1="${YH}" y2="${YH}" stroke="#FFD21F" stroke-width="3" stroke-dasharray="14 10" opacity=".7"/></g>
        <g class="grav"><line class="ga" stroke="#FFD21F" stroke-width="12" marker-end="url(#sf${ctx.i})"/></g>
      </svg>
      <div class="rotulos-ecl">
        <div class="abs re r-mar" data-g="r-mar">${esc(p.mar || 'NÍVEL BAIXO')} · 0 m</div>
        <div class="abs re r-lago" data-g="r-lago">${esc(p.lago || 'NÍVEL ALTO')} · +${fmt(D, D % 1 ? 1 : 0)} m</div>
        <div class="abs re r-cpE" data-g="r-cpE"></div><div class="abs re r-cpD" data-g="r-cpD"></div>
        <div class="abs re r-val" data-g="r-val">VÁLVULA ABERTA</div>
        <div class="abs re r-grav" data-g="r-grav" style="background:#FFD21F;color:#0b0f17">${subir ? 'DESCE DO LAGO POR GRAVIDADE' : 'ESCOA PARA O MAR POR GRAVIDADE'}</div>
        <div class="abs re r-nivel" data-g="r-nivel" style="font-size:40px;padding:4px 14px;background:#0b0f17;border-left:8px solid #FFD21F"></div>
        <div class="abs re r-delta" data-g="r-delta" style="color:#FFD21F;background:rgba(5,20,26,.9)"></div>
      </div>
      ${+p.degraus > 1 ? `<div class="abs esc-deg" data-g="degraus" style="left:72px;top:1218px;display:flex;align-items:center;gap:16px;padding:8px 16px;background:rgba(6,18,26,.92);box-shadow:0 6px 18px rgba(0,0,0,.4)">
          <svg width="120" height="60" viewBox="0 0 190 96" style="overflow:visible">${Array.from({ length: +p.degraus }, (_, i) => {
            const w = 190 / +p.degraus, h = 96 / +p.degraus; return `<rect class="dg dg${i}" x="${i * w}" y="${96 - (i + 1) * h}" width="${w - 4}" height="${(i + 1) * h}" fill="rgba(63,208,224,.18)" stroke="#3FD0E0" stroke-width="2"/>`; }).join('')}
            <circle class="dg-navio" r="9" fill="#FFD21F" stroke="#0b0f17" stroke-width="3"/></svg>
          <div style="font-family:var(--f-dado);font-weight:700;font-size:26px;line-height:1.3;color:rgba(255,255,255,.85)">ESQUEMA: 1 CÂMARA PARA OS ${esc(String(D))} m<br><span style="color:#FFD21F">NO CANAL: ${+p.degraus} CÂMARAS EM SEQUÊNCIA</span></div></div>`
        : `<div class="abs" data-g="aviso" data-opcional="1" style="right:160px;top:1176px;font-family:var(--f-dado);font-size:26px;color:rgba(255,255,255,.6)">ESQUEMA ILUSTRATIVO · FORA DE ESCALA</div>`}
      <style>.re{font-family:var(--f-dado);font-weight:700;font-size:30px;color:#fff;background:rgba(5,20,26,.88);padding:4px 12px;white-space:nowrap;letter-spacing:1px}</style>`;

    // ---- linha do tempo física ----
    function tempos(d) {
      const T = (p.tempos || [0, d * .32, d * .76]).map(Number);
      const entra = [T[0] + .25, Math.max(T[0] + 1.6, Math.min(T[1] - 1.0, T[0] + (T[1] - T[0]) * .65))];
      const fecha = [entra[1] + .1, entra[1] + .8];                         // só fecha com o navio inteiro dentro
      const valv = Math.max(fecha[1] + .15, T[1]);
      const enche = [valv + .35, Math.max(valv + 1.6, T[2] - .5)];
      const abre = [Math.max(enche[1] + .2, T[2]), Math.max(enche[1] + .2, T[2]) + .7];
      const sai = [abre[1] + .1, d - .1];
      return { T, entra, fecha, valv, enche, abre, sai };
    }
    // ---- câmera: retângulos [x, y, w] no mundo (h = w / aspecto) ----
    const rect = (cx, cy, w) => [cx - w / 2, cy - w / ASP / 2, w];
    function plano(nome, est) {
      switch (nome) {
        case 'A': return rect(MW / 2, 600, MW);
        case 'B': return rect(subir ? C0 + 40 : C1 - 40, 600, 820);
        case 'C': return subir ? rect(1000, 700, 1100) : rect(470, 720, 1100);
        case 'D': return rect((C0 + C1) / 2 + 60, est.nivel + 40, 1000);
        case 'E': return rect(subir ? C1 - 60 : C0 + 60, (YH + YL) / 2 + 60, 900);
        default: return rect(subir ? MW / 2 + 60 : MW / 2 - 60, 600, MW);
      }
    }
    return {
      html,
      upd(tl, el, c) {
        const tm = tempos(c.dur), { T, entra, fecha, valv, enche, abre, sai } = tm;
        // nível na câmara: (1 − k)² na diferença (vazão ∝ √Δh) — desacelera ao se aproximar do nível final
        const k = clamp((tl - enche[0]) / (enche[1] - enche[0])), frac = 1 - Math.pow(1 - k, 2);
        const ent = subir ? YL : YH, sai_ = subir ? YH : YL, nivel = lerp(ent, sai_, frac);
        const delta = Math.abs(nivel - sai_) / (YL - YH) * D;                 // metros que faltam
        // navio: x pelas etapas; y = SEMPRE a superfície onde ele está
        const xIni = subir ? 140 : 1330, xMid = (C0 + C1) / 2, xFim = subir ? 1330 : 140;
        const ke = eio(clamp((tl - entra[0]) / (entra[1] - entra[0]))), ks = eio(clamp((tl - sai[0]) / Math.max(.8, sai[1] - sai[0])));
        const nx = tl < sai[0] ? lerp(xIni, xMid, ke) : lerp(xMid, xFim, ks);
        const superficie = nx < C0 ? YL : nx > C1 + PAR ? YH : nivel;
        const ny = superficie + Math.sin(tl * 1.7) * 2.5;
        el.querySelector('.nav').setAttribute('transform', `translate(${nx} ${ny})`);
        const cam = el.querySelector('.cam'); cam.setAttribute('y', nivel); cam.setAttribute('height', FUNDO - nivel);
        let sp = `M${C0} ${nivel}`; for (let x = C0; x <= C1; x += 20) sp += ` L${x} ${nivel + Math.sin(x / 38 + tl * 5) * (k > 0 && k < 1 ? 6 : 2.5)}`;
        el.querySelector('.sup').setAttribute('d', sp);
        // comportas (mecânica: movimento linear com freio curto, sem "mola")
        const mec = x => { x = clamp(x); return x < .85 ? x / .85 * .95 : .95 + (x - .85) / .15 * .05; };
        const atras = el.querySelector(subir ? '.cpE' : '.cpD'), frente = el.querySelector(subir ? '.cpD' : '.cpE');
        const hA = subir ? FUNDO - TOPO : SOLEIRA - TOPO, hF = subir ? SOLEIRA - TOPO : FUNDO - TOPO;
        const fechada = mec((tl - fecha[0]) / (fecha[1] - fecha[0]));
        // TRAVA FÍSICA: a comporta da frente só abre com Δh ≈ 0
        const aberta = delta < .3 ? mec((tl - abre[0]) / (abre[1] - abre[0])) : 0;
        atras.setAttribute('transform', `translate(0 ${-(1 - fechada) * (hA - 10)})`);
        frente.setAttribute('transform', `translate(0 ${-aberta * (hF - 10)})`);
        // válvula e fluxo pelo túnel certo
        const vAberta = tl >= valv && k < 1, vk = vAberta ? eo((tl - valv) / .35) : (k >= 1 ? 1 - eo((tl - enche[1]) / .3) : 0);
        el.querySelector(subir ? '.vEl' : '.vSl').setAttribute('transform', `rotate(${90 * vk} ${subir ? 1310 : 300} ${subir ? (SOLEIRA + TUN) / 2 : TUN})`);
        const fl = el.querySelector(subir ? '.fl-enche' : '.fl-esvazia');
        fl.setAttribute('opacity', vAberta ? .95 : 0); fl.setAttribute('stroke-dashoffset', subir ? -tl * 220 : -tl * 220);
        el.querySelectorAll('.jatos path').forEach((j, q) => { const x = PORTAS[q], h = vAberta && subir ? 40 + 20 * Math.sin(tl * 9 + q) : 0;
          j.setAttribute('d', `M${x} ${FUNDO} q ${8 * Math.sin(tl * 7 + q)} ${-h / 2} 0 ${-h}`); j.setAttribute('opacity', h ? .85 : 0); });
        const ga = el.querySelector('.ga');
        if (subir) { ga.setAttribute('x1', 1250); ga.setAttribute('y1', SOLEIRA - 130); ga.setAttribute('x2', 1250); ga.setAttribute('y2', SOLEIRA + 120); }
        else { ga.setAttribute('x1', 210); ga.setAttribute('y1', TUN - 160); ga.setAttribute('x2', 210); ga.setAttribute('y2', TUN - 30); }
        el.querySelector('.grav').setAttribute('opacity', vAberta ? clamp((tl - valv) / .3) : 0);
        // Δh: colchete entre a superfície da câmara e o nível de destino
        const dl = el.querySelector('.dl'); dl.setAttribute('y1', Math.min(nivel, sai_)); dl.setAttribute('y2', Math.max(nivel, sai_));
        el.querySelector('.dt').setAttribute('y1', sai_); el.querySelector('.dt').setAttribute('y2', sai_);
        el.querySelector('.db').setAttribute('y1', nivel); el.querySelector('.db').setAttribute('y2', nivel);
        el.querySelector('.delta').setAttribute('opacity', tl > fecha[0] && tl < abre[1] + .4 ? 1 : 0);
        // ---- câmera dirigida ----
        const est = { nx, nivel };
        const seq = p.planos === false ? [['A', 0]] : [['A', 0], ['B', fecha[0] - .5], ['C', valv - .1], ['D', enche[0] + (enche[1] - enche[0]) * .3], ['E', enche[1] - .3], ['F', abre[1] + .2]];
        let r = plano(seq[0][0], est);
        for (let q = 1; q < seq.length; q++) { if (tl < seq[q][1]) break; const kq = eio((tl - seq[q][1]) / .8); const r1 = plano(seq[q][0], est); r = [lerp(r[0], r1[0], kq), lerp(r[1], r1[1], kq), lerp(r[2], r1[2], kq)]; }
        const svg = el.querySelector('.cv'); svg.setAttribute('viewBox', `${r[0]} ${r[1]} ${r[2]} ${r[2] / ASP}`);
        const P = (x, y) => [(x - r[0]) / r[2] * SW, SY + (y - r[1]) / (r[2] / ASP) * SH];
        const poe = (sel, x, y, txt, vis = true, ax = 0, ay = -1) => { const e = el.querySelector(sel); if (txt !== undefined) e.textContent = txt;
          const [px, py] = P(x, y), w = e.offsetWidth, h = e.offsetHeight; const L = clamp(px - w * (ax === 0 ? .5 : ax < 0 ? 1 : 0), 76, 926 - w), Tt = py + (ay < 0 ? -h - 10 : 10);
          const dentro = Tt > SY + 10 && Tt + h < SY + SH - 40 && px > 30 && px < 1050; /* âncora fora do quadro: rótulo some */ e.style.left = L + 'px'; e.style.top = Tt + 'px'; e.style.opacity = vis && dentro ? 1 : 0; };
        poe('.r-mar', 150, YL, undefined, true);
        poe('.r-lago', 1300, YH, undefined, true);
        poe('.r-cpE', C0 - PAR / 2, TOPO - 10, (subir ? fechada : (tl < abre[0] ? 1 : 1 - aberta)) > .9 ? 'COMPORTA FECHADA' : 'COMPORTA ABERTA', true);
        poe('.r-cpD', C1 + PAR / 2, TOPO - 10, (subir ? 1 - aberta : fechada) > .9 ? 'COMPORTA FECHADA' : 'COMPORTA ABERTA', tl > fecha[0] - .6);
        poe('.r-val', subir ? 1310 : 300, subir ? (SOLEIRA + TUN) / 2 + 40 : TUN + 40, undefined, vAberta, 0, 1);
        poe('.r-grav', subir ? 1250 : 210, subir ? SOLEIRA - 140 : TUN - 170, undefined, vAberta);
        const m = D * (YL - nivel) / (YL - YH);
        poe('.r-nivel', C0 + 80, nivel, `${fmt(m, 0)} m`, tl > entra[1] - .3, 1, -1);
        poe('.r-delta', C1 - 80, (nivel + sai_) / 2, delta > .3 ? `FALTAM ${fmt(delta, 0)} m` : 'NÍVEIS IGUAIS ✓', tl > fecha[0] && tl < abre[1] + .4, -1, 1);
        // rótulos não se cobrem: na ordem de prioridade, o que bater num já posto desce uma linha; se ainda bater, some
        const postos = [];
        for (const sel of ['.r-nivel', '.r-delta', '.r-grav', '.r-cpE', '.r-cpD', '.r-val', '.r-lago', '.r-mar']) {
          const e = el.querySelector(sel); if (+e.style.opacity < .5) continue;
          const caixa = () => { const b = e.getBoundingClientRect(); return [b.left - 6, b.top - 4, b.right + 6, b.bottom + 4]; };
          const bate = b => postos.some(q => b[0] < q[2] && q[0] < b[2] && b[1] < q[3] && q[1] < b[3]);
          let b = caixa(); if (bate(b)) { e.style.top = (parseFloat(e.style.top) + (b[3] - b[1]) + 6) + 'px'; b = caixa(); if (bate(b) || b[3] > SY + SH - 40) { e.style.opacity = 0; continue; } }
          postos.push(b);
        }
        // cabeçalho
        const f = tl < T[1] ? 0 : tl < T[2] ? 1 : 2;
        el.querySelectorAll('.et').forEach((e, i) => { e.style.opacity = i === f ? eo5((tl - (i ? T[i] : 0)) / .35) : 0; e.style.transform = `translateY(${i === f ? (1 - eo5((tl - (i ? T[i] : 0)) / .35)) * 16 : 0}px)`; });
        el.querySelectorAll('.pd').forEach((e, i) => e.style.background = i <= f ? 'var(--ciano)' : 'rgba(127,227,240,.25)');
        c.estadoFisico = { nivel_m: m, delta_m: delta, comporta_frente_aberta: aberta, comporta_tras_fechada: fechada, navio_x: nx, linha_dagua: superficie };
        // escada dos degraus reais: o navio percorre TODAS as câmaras na proporção do nível do esquema
        const dgn = el.querySelector('.dg-navio');
        if (dgn) { const N = +p.degraus, fr = clamp(subir ? m / D : 1 - m / D), w = 190 / N, h = 96 / N, i = Math.min(N - 1, Math.floor(fr * N)), ff = fr * N - i;
          dgn.setAttribute('cx', i * w + (w - 4) * (.15 + .7 * ff)); dgn.setAttribute('cy', 96 - (i + 1) * h - 9);
          el.querySelectorAll('.dg').forEach((r, j) => r.setAttribute('fill', j <= i ? 'rgba(63,208,224,.45)' : 'rgba(63,208,224,.12)'));
          aparece(el.querySelector('.esc-deg'), tl, .4, { dy: 10 }); }
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
        <div class="abs" data-g="ct" data-alinhamento="local" style="left:${C[0] - 100}px;width:200px;top:${C[1] + 30}px;text-align:center;font-family:var(--f-dado);font-weight:700;font-size:26px;color:#fff">${esc(p.centro || '')}</div>`,
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
