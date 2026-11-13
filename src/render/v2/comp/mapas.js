/* MAPAS V2 — MapLibre GL JS (BSD-3) + Natural Earth (domínio público), sem servidor de mapas: o Python recorta as
 * camadas do enquadramento (src/v2/geo.py) e a câmera é DETERMINÍSTICA (jumpTo por quadro + espera os tiles).
 * Rótulos em HTML posicionados com map.project(): tipografia do Coringa, sem depender de fontes de glifos.          */
(function () {
  const { esc, hl, clamp, lerp, eo, eo5, eio, back, aparece, caber, fmt } = V2.U;
  const H = V2.H;
  const COR = { mar: '#0a1a2f', mar2: '#0d2340', terra: '#26344b', terra2: '#2d3d57', borda: '#5d7598', costa: '#8fa9cf', rio: '#4f86c6', lago: '#0f2a4c', alvo: '#FFD21F', rota: '#FFD21F' };
  const PAD = { top: 540, bottom: 760, left: 100, right: 170 };     // área útil do mapa: y 540–1160, x 100–910 (V2.1: abaixo do cabeçalho de 2 linhas)
  const CORES_ROTA = ['#FFD21F', '#3FD0E0', '#FF6B5A'];

  function estilo(geo, p) {
    const fc = x => x || { type: 'FeatureCollection', features: [] };
    return {
      version: 8, sources: {
        paises: { type: 'geojson', data: fc(geo.paises), maxzoom: 8, tolerance: .25 },
        lagos: { type: 'geojson', data: fc(geo.lagos), maxzoom: 9, tolerance: .2 },
        rios: { type: 'geojson', data: fc(geo.rios), maxzoom: 9, tolerance: .2 },
        alvo: { type: 'geojson', data: p.pais_geo ? { type: 'FeatureCollection', features: [p.pais_geo] } : fc(null), maxzoom: 8 },
        ...Object.fromEntries([0, 1, 2].map(i => [`rota${i}`, { type: 'geojson', data: { type: 'Feature', geometry: { type: 'LineString', coordinates: [] } }, maxzoom: 10 }])),
      },
      layers: [
        { id: 'mar', type: 'background', paint: { 'background-color': COR.mar } },
        { id: 'terra', type: 'fill', source: 'paises', paint: { 'fill-color': COR.terra, 'fill-antialias': true } },
        { id: 'alvo', type: 'fill', source: 'alvo', paint: { 'fill-color': COR.alvo, 'fill-opacity': 0 } },
        { id: 'lagos', type: 'fill', source: 'lagos', paint: { 'fill-color': COR.lago } },
        { id: 'rios', type: 'line', source: 'rios', paint: { 'line-color': COR.rio, 'line-width': ['interpolate', ['linear'], ['zoom'], 3, .8, 8, 2.4], 'line-opacity': .8 } },
        { id: 'fronteira', type: 'line', source: 'paises', paint: { 'line-color': COR.borda, 'line-width': ['interpolate', ['linear'], ['zoom'], 2, .8, 8, 1.8], 'line-opacity': .9 } },
        { id: 'alvo-borda-brilho', type: 'line', source: 'alvo', paint: { 'line-color': COR.alvo, 'line-width': 14, 'line-blur': 10, 'line-opacity': 0 } },
        { id: 'alvo-borda', type: 'line', source: 'alvo', paint: { 'line-color': COR.alvo, 'line-width': 3.5, 'line-opacity': 0 } },
        // rotas: 12 px + contorno escuro + brilho (legível no celular sobre terra e sobre mar)
        ...[0, 1, 2].flatMap(i => [
          { id: `rota${i}-brilho`, type: 'line', source: `rota${i}`, layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': (p.rotas && p.rotas[i] && p.rotas[i].cor) || CORES_ROTA[i], 'line-width': 34, 'line-blur': 18, 'line-opacity': .45 } },
          { id: `rota${i}-contorno`, type: 'line', source: `rota${i}`, layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': '#05080f', 'line-width': 18 } },
          { id: `rota${i}`, type: 'line', source: `rota${i}`, layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': (p.rotas && p.rotas[i] && p.rotas[i].cor) || CORES_ROTA[i], 'line-width': 12 } }]),
      ],
    };
  }

  // espera o quadro estar realmente desenhado (tiles prontos): sem isso, quadros sairiam com terra faltando
  function desenhado(map) {
    return new Promise(res => {
      let n = 0; const ok = () => { if ((map.areTilesLoaded() && map.loaded()) || ++n > 200) res(); else map.once('render', ok); };
      map.once('render', ok); map.triggerRepaint();
    });
  }
  const cam = (map, bb, pad = PAD) => { const c = map.cameraForBounds([[bb[0], bb[1]], [bb[2], bb[3]]], { padding: pad });
    if (!c) return { center: [(bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2], zoom: 3 };
    const ce = c.center && (Array.isArray(c.center) ? c.center : [c.center.lng, c.center.lat]); return { center: ce, zoom: c.zoom }; };
  function camLerp(a, b, k) {
    // voo com arco de zoom (afasta no meio quando o deslocamento é grande), igual ao flyTo, mas determinístico
    const dz = Math.hypot(b.center[0] - a.center[0], b.center[1] - a.center[1]);
    const arco = dz > 4 ? Math.sin(k * Math.PI) * Math.min(1.6, dz / 12) : 0;
    return { center: [lerp(a.center[0], b.center[0], k), lerp(a.center[1], b.center[1], k)], zoom: lerp(a.zoom, b.zoom, k) - arco, bearing: lerp(a.bearing || 0, b.bearing || 0, k), pitch: lerp(a.pitch || 0, b.pitch || 0, k) };
  }
  const coord = (lon, lat) => `${Math.abs(lat).toFixed(2)}° ${lat >= 0 ? 'N' : 'S'} · ${Math.abs(lon).toFixed(2)}° ${lon >= 0 ? 'L' : 'O'}`;
  function hav(a, b) { const R = 6371, r = Math.PI / 180, dl = (b[1] - a[1]) * r, dg = (b[0] - a[0]) * r; const h = Math.sin(dl / 2) ** 2 + Math.cos(a[1] * r) * Math.cos(b[1] * r) * Math.sin(dg / 2) ** 2; return 2 * R * Math.asin(Math.sqrt(h)); }

  /* motor comum dos 3 mapas: cria o mapa, calcula câmera inicial/final, posiciona rótulos */
  function motorMapa(p, ctx, tipo) {
    let map, A, B, rotulosMar = [], rotulosPais = [];
    const pts = (p.pontos || []).map(x => ({ ...x, lon: +x.lon, lat: +x.lat }));
    // TRILHAS: uma rota (p.rota ou os pontos) ou várias para comparar (p.rotas). Trechos longos seguem o círculo
    // máximo (d3.geoInterpolate): uma linha reta no Mercator atravessaria regiões erradas.
    const densa = cs => { const out = []; for (let i = 0; i < cs.length; i++) { if (i) { const d = hav(cs[i - 1], cs[i]); if (d > 250) { const f = d3.geoInterpolate(cs[i - 1], cs[i]); const n = Math.ceil(d / 120); for (let k = 1; k < n; k++) out.push(f(k / n)); } } out.push(cs[i]); } return out; };
    const brutas = p.rotas ? p.rotas.map(r => r.rota || (r.pontos || []).map(x => [x.lon, x.lat])) : [p.rota || (tipo === 'rota' ? pts.map(x => [x.lon, x.lat]) : [])];
    const trilhas = brutas.slice(0, 3).map(cs => { const c = densa(cs.map(([a, b]) => [+a, +b])); const cum = [0]; for (let i = 1; i < c.length; i++) cum.push(cum[i - 1] + hav(c[i - 1], c[i])); return { c, cum, total: cum[cum.length - 1] || 0 }; });
    const rota = (trilhas[0] || { c: [] }).c, total = (trilhas[0] || { total: 0 }).total;
    function parcial(k, j = 0) {   // a trilha j até a fração k do comprimento
      const T = trilhas[j]; if (!T || T.c.length < 2) return { coords: T ? T.c : [], ponta: T && T.c[0] };
      const alvo = T.total * k; let i = T.cum.findIndex(c => c >= alvo); if (i < 1) i = k <= 0 ? 1 : T.cum.length - 1;
      const f = (alvo - T.cum[i - 1]) / ((T.cum[i] - T.cum[i - 1]) || 1), ponta = [lerp(T.c[i - 1][0], T.c[i][0], clamp(f)), lerp(T.c[i - 1][1], T.c[i][1], clamp(f))];
      return { coords: [...T.c.slice(0, i), ponta], ponta };
    }
    return {
      pts, rota, total, parcial, trilhas,
      async montar(el) {
        const host = el.querySelector('.mapa-host');
        map = new maplibregl.Map({ container: host, style: estilo(p.geo || {}, p), interactive: false, attributionControl: false, fadeDuration: 0,
          canvasContextAttributes: { preserveDrawingBuffer: true, antialias: true }, center: [0, 0], zoom: 1, renderWorldCopies: false, maxPitch: 60 });
        host._map = map; await new Promise(r => map.once('load', r));
        const bb = p.bbox; let pad = { ...PAD, ...(p._pad || {}) };
        // Num quadro vertical de 1920 px o MapLibre não afasta além do zoom em que o mundo cobre a altura (z≈1,9):
        // rotas que descem ao Cabo Horn ou sobem ao Ártico ficariam fora do quadro. Se o enquadramento pedir zoom
        // menor, o mapa encolhe na vertical (com esmaecimento na borda) até a caixa caber na área útil.
        const ajuste = (() => {
          const c = map.cameraForBounds([[bb[0], bb[1]], [bb[2], bb[3]]], { padding: pad }); if (!c) return null;
          const W = 512 * 2 ** c.zoom, my = l => Math.log(Math.tan(Math.PI / 4 + Math.max(-85, Math.min(85, l)) * Math.PI / 360));
          const acima = (Math.PI - my(bb[3])) / (2 * Math.PI) * W, abaixo = (my(bb[1]) + Math.PI) / (2 * Math.PI) * W;
          const H = host.clientHeight || 1920, topo = Math.max(0, Math.ceil(pad.top - acima + 4)), fundo = Math.min(H, Math.floor(H - pad.bottom + abaixo - 4));
          if (topo <= 0 && fundo >= H) return null;
          return { topo, fundo, H };
        })();
        if (ajuste) {
          Object.assign(host.style, { top: ajuste.topo + 'px', height: (ajuste.fundo - ajuste.topo) + 'px', bottom: 'auto',
            maskImage: `linear-gradient(180deg,${ajuste.topo ? 'transparent 0,#000 90px' : '#000 0'},#000 calc(100% - 110px),${ajuste.fundo < ajuste.H ? 'transparent' : '#000'} 100%)` });
          host.style.webkitMaskImage = host.style.maskImage;
          map.resize(); pad = { ...pad, top: pad.top - ajuste.topo, bottom: pad.bottom - (ajuste.H - ajuste.fundo) };
          // o resto do código posiciona rótulos em coordenadas do palco: project() devolve y do palco
          const proj = map.project.bind(map), dy = ajuste.topo; map.project = ll => { const q = proj(ll); return { x: q.x, y: q.y + dy }; };
          p._ajusteHost = ajuste;
        }
        B = cam(map, bb, pad); B.bearing = p.bearing || 0; B.pitch = p.pitch || 0;
        const w = bb[2] - bb[0], h = bb[3] - bb[1], f = p.contexto_fator || 6;
        A = p.camera_inicial || cam(map, [bb[0] - w * f / 2, Math.max(-80, bb[1] - h * f / 2), bb[2] + w * f / 2, Math.min(80, bb[3] + h * f / 2)]);
        if (A.zoom > B.zoom - 1.2) A.zoom = Math.max(0.5, B.zoom - 2.2);
        A.bearing = p.bearing_inicial ?? -8; A.pitch = 0;
        // rótulos de mar/oceano e de países vizinhos: centro do polígono (d3.geoCentroid), só os maiores do quadro
        const mares = (p.geo.mares || { features: [] }).features.map(f2 => ({ nome: f2.properties.name_pt || f2.properties.name, c: d3.geoCentroid(f2), area: d3.geoArea(f2) }))
          .filter(x => x.nome && x.c[0] > bb[0] - w * 1.2 && x.c[0] < bb[2] + w * 1.2 && x.c[1] > bb[1] - h * 1.2 && x.c[1] < bb[3] + h * 1.2).sort((a, b2) => b2.area - a.area).slice(0, p.max_mares ?? 2);
        rotulosMar = mares.map(m => ({ ...m, ...(p.mares_pos || {})[m.nome] && { c: p.mares_pos[m.nome] } }));
        const alvoNome = String(p.pais_nome || '').toLowerCase();
        rotulosPais = (p.geo.paises || { features: [] }).features.map(f2 => ({ nome: f2.properties.name_pt || f2.properties.name, c: [f2.properties.label_x ?? d3.geoCentroid(f2)[0], f2.properties.label_y ?? d3.geoCentroid(f2)[1]], area: d3.geoArea(f2) }))
          .filter(x => x.nome && x.nome.toLowerCase() !== alvoNome).sort((a, b2) => b2.area - a.area).slice(0, p.max_paises ?? 3);
        const html = [...rotulosMar.map((m, i) => `<div class="rot-mapa mar rm${i}" data-g="mar${i}" data-opcional="1">${esc(m.nome)}</div>`),
          ...rotulosPais.map((m, i) => `<div class="rot-mapa pais rp${i}" data-g="pais${i}" data-opcional="1">${esc(m.nome)}</div>`)].join('');
        el.querySelector('.rotulos').insertAdjacentHTML('beforeend', html);
        map.jumpTo(A); await desenhado(map);
      },
      async upd(tl, el, kcam, extra) {
        if (!map) return;
        const c = camLerp(A, B, kcam); map.jumpTo(c);
        const r = extra && extra(map);
        await desenhado(map);
        const pos = (lonlat, e, dx = 0, dy = 0) => { if (!e) return; const q = map.project(lonlat); e.style.left = (q.x + dx) + 'px'; e.style.top = (q.y + dy) + 'px'; return q; };
        rotulosMar.forEach((m, i) => { const e = el.querySelector('.rm' + i); const q = pos(m.c, e); e.style.transform = 'translate(-50%,-50%)'; e.style.opacity = clamp((tl - .3) / .5) * (q.y > 420 && q.y < 1100 && q.x > 120 && q.x < 880 ? 1 : 0); });
        rotulosPais.forEach((m, i) => { const e = el.querySelector('.rp' + i); const q = pos(m.c, e); e.style.transform = 'translate(-50%,-50%)'; e.style.opacity = clamp((tl - .5) / .5) * (q.y > 420 && q.y < 1100 && q.x > 160 && q.x < 860 ? .9 : 0); });
        return { map, pos, colisao: () => colisao(el) };
      },
    };
  }
  // rótulos do mapa não cobrem a interface (cabeçalho, pinos, distância) nem uns aos outros: o primeiro da fila fica
  function colisao(el) {
    const caixa = e => { const r = e.getBoundingClientRect(); return { x0: r.left - 10, x1: r.right + 10, y0: r.top - 6, y1: r.bottom + 6 }; };
    const cruza = (a, b) => a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1;
    const fixos = [...el.querySelectorAll('.cab,.dist,.dd,.nmp,.rot-mapa.destaque,.pino,.atr')].filter(e => parseFloat(e.style.opacity || 1) > .05).map(caixa);
    for (const e of el.querySelectorAll('.rotulos .rot-mapa')) {
      if (parseFloat(e.style.opacity || 0) <= .01) continue; const b = caixa(e);
      if (fixos.some(f => cruza(f, b))) e.style.opacity = 0; else fixos.push(b);
    }
  }
  const cabecalho = (p, rot) => `<div class="abs cab" data-g="cab" style="left:72px;right:150px;top:340px;padding:22px 28px 24px;background:rgba(7,12,22,.82);backdrop-filter:blur(10px);border-top:6px solid var(--amarelo)">
      <div class="kicker" style="font-size:26px;color:var(--amarelo)">${esc(rot)}</div>
      ${p.titulo ? `<div class="tt" data-txt="1" style="font-weight:900;font-size:50px;line-height:1.05;margin-top:8px;text-transform:uppercase">${hl(p.titulo)}</div>` : ''}</div>`;
  const moldura = `<div class="abs" data-deco="1" style="inset:0;pointer-events:none;background:linear-gradient(180deg,rgba(7,11,18,.65) 0%,rgba(7,11,18,0) 24%,rgba(7,11,18,0) 56%,rgba(7,11,18,.85) 80%,rgba(7,11,18,.95) 100%)"></div>`;
  const ATR = '<div class="abs atr" data-g="atr" data-opcional="1" style="right:160px;top:1198px;font-family:var(--f-dado);font-size:26px;color:rgba(255,255,255,.6)">Natural Earth · MapLibre</div>';
  const pinoHTML = (i, nome, sub) => `<div class="pino pn${i}" style="opacity:0"><div class="onda"></div><div class="onda o2"></div><div class="nucleo"></div></div>
     <div class="abs rot-mapa destaque lb${i}" data-g="pt${i}" style="opacity:0">${esc(nome)}${sub ? `<div style="font-family:var(--f-dado);font-weight:400;font-size:26px;letter-spacing:1px;margin-top:4px;color:#3a4558">${esc(sub)}</div>` : ''}</div>`;
  function animPino(el, i, tl, t0, q, cima, vizinhos) {
    const pn = el.querySelector('.pn' + i), lb = el.querySelector('.lb' + i); if (!pn || !q) return;
    if (i === 0) el.querySelectorAll('.rot-mapa.destaque').forEach(e => { e._t = null; });   // nova passada: nenhum nome posicionado ainda
    const k = back((tl - t0) / .45); pn.style.left = q.x + 'px'; pn.style.top = q.y + 'px'; pn.style.opacity = clamp((tl - t0) / .1);
    pn.querySelector('.nucleo').style.transform = `scale(${clamp(k, 0, 1.3)})`;
    pn.querySelectorAll('.onda').forEach((o, j) => { const ph = ((tl - t0 + j * .6) % 1.2) / 1.2; o.style.transform = `scale(${1 + ph * 4})`; o.style.opacity = tl > t0 ? (1 - ph) * .8 : 0; });
    // posição do nome: a preferida (acima/abaixo), a oposta, à direita, à esquerda — a primeira que não cobre
    // cabeçalho, painel de distância, atribuição nem outro nome de pino; sem nenhuma livre, fica a preferida.
    const w = lb.offsetWidth, hh = lb.offsetHeight;
    // outro pino a menos de 300 px: o nome vai para o lado oposto a ele (senão os nomes se cruzam)
    // vizinhos: posições DESTE quadro passadas por quem chama (o DOM ainda guarda o quadro anterior)
    const viz = (vizinhos || [...el.querySelectorAll('.pino')].filter(e => e !== pn && parseFloat(e.style.opacity || 0) > .05).map(e => [parseFloat(e.style.left), parseFloat(e.style.top)]))
      .filter(v => Math.hypot(v[0] - q.x, v[1] - q.y) < 300);
    let ordem = [cima ? 'cima' : 'baixo', cima ? 'baixo' : 'cima', 'dir', 'esq'];
    if (viz.length) { const vx = viz[0][0] - q.x, vy = viz[0][1] - q.y; const lado = vx > 0 ? 'esq' : 'dir', vert = vy > 0 ? 'cima' : 'baixo';
      ordem = Math.abs(vx) >= Math.abs(vy) ? [lado, vert, vert === 'cima' ? 'baixo' : 'cima', lado === 'esq' ? 'dir' : 'esq'] : [vert, lado, lado === 'esq' ? 'dir' : 'esq', vert === 'cima' ? 'baixo' : 'cima']; }
    const cands = ordem.map(k => {
      const x = k === 'dir' ? q.x + 46 : k === 'esq' ? q.x - 46 - w : clamp(q.x - w / 2, 90, 920 - w);
      const y = k === 'cima' ? q.y - hh - 44 : k === 'baixo' ? q.y + 40 : q.y - hh / 2;
      return { k, x, y };
    });
    // ocupado: interface fixa, nomes JÁ posicionados neste quadro (ordem dos pinos) e os outros pinos
    const ocup = [...el.querySelectorAll('.cab,.dist,.cmpd,.atr,.rot-mapa.destaque')].filter(e => e !== lb && parseFloat(getComputedStyle(e).opacity) > .05 && !(e.classList.contains('destaque') && e._t == null))
      .map(e => { const r = e.getBoundingClientRect(); return [r.left - 8, r.top - 8, r.right + 8, r.bottom + 8]; })
      .concat(viz.map(v => [v[0] - 26, v[1] - 26, v[0] + 26, v[1] + 26]));
    const dentro = c => c.x >= 60 && c.x + w <= 1000 && c.y >= 330 && c.y + hh <= 1225;
    const sobre = c => ocup.reduce((s2, o) => s2 + Math.max(0, Math.min(c.x + w, o[2]) - Math.max(c.x, o[0])) * Math.max(0, Math.min(c.y + hh, o[3]) - Math.max(c.y, o[1])), 0);
    // sem posição livre: a de menor sobreposição dentro da tela (nunca escondida atrás do cabeçalho)
    const esc = cands.find(c => dentro(c) && !sobre(c)) || cands.filter(dentro).sort((x, y) => sobre(x) - sobre(y))[0] || cands[0];
    lb.style.left = esc.x + 'px'; lb.style.top = esc.y + 'px'; lb._pos = esc.k; lb._t = 1; lb.dataset.pos = esc.k;
    const kl = eo5((tl - t0 - .25) / .4); lb.style.opacity = kl;
    const d = (1 - kl) * 16; lb.style.transform = esc.k === 'cima' ? `translateY(${d}px)` : esc.k === 'baixo' ? `translateY(${-d}px)` : `translateX(${esc.k === 'dir' ? -d : d}px)`;
  }

  /* 9. mapa.localizacao */
  V2.registrar({
    id: 'mapa.localizacao', nome: 'Mapa de localização', tratamento: 'mapa', tom: 'escuro',
    objetivo: 'Responder "onde fica?": do contexto (continente) ao lugar exato, com pino, nome e coordenadas.',
    funcoes: ['onde', 'localizacao'],
    params: { titulo: '≤ 36 (opcional)', pontos: '1–3 × {nome ≤ 22, lon, lat, sub ≤ 28}', pais: 'país a destacar (opcional)', kicker: "padrão 'ONDE FICA'" },
    fundo: 'próprio (MapLibre + Natural Earth recortado pelo geo.py)', layout: 'cabeçalho em vidro 340–480; mapa útil 430–1060; pino com rótulo acima; atribuição discreta',
    paleta: 'mar #0a1a2f, terra #26344b, fronteiras azul-acinzentadas, destaque amarelo', animacao: 'câmera aproxima do contexto ao lugar (arco de zoom), pino cai com ondas, rótulos de mares e vizinhos surgem',
    duracao: [3, 4, 6], limites: { titulo: 36, nome: 22 }, legenda: 'livre',
    area_segura: 'conteúdo entre y 340 e 1100; rótulos limitados a x 90–920', legibilidade: 'pino 34 px 800 em placa branca; mares 38 px serifa itálica',
    rejeicao: ['coordenadas ausentes ou fora do país citado', 'lugar que a fala não menciona'],
    transicao: 'zoom',
    exemplo: { params: { kicker: 'ONDE FICA', titulo: 'O atalho entre *dois oceanos*', pontos: [{ nome: 'Canal do Panamá', lon: -79.68, lat: 9.08, sub: '9,08° N · 79,68° O' }], folga: 4, minimo: 1.2 }, dur: 4.5, fala: 'O canal corta o Panamá e liga dois oceanos.' },
  }, (p, ctx) => {
    const m = motorMapa(p, ctx, 'local');
    return {
      html: `<div class="mapa-host" data-ocupa="1"></div>${moldura}<div class="rotulos abs" style="inset:0"></div>${m.pts.map((x, i) => pinoHTML(i, x.nome, x.sub || coord(x.lon, x.lat))).join('')}${cabecalho(p, p.kicker || 'ONDE FICA')}${ATR}`,
      montar: el => m.montar(el),
      async upd(tl, el, c) {
        const kc = eio((tl - .1) / Math.min(2.2, c.dur * .45));   // chega e PERMANECE (fim legível)
        const r = await m.upd(tl, el, kc); if (!r) return;
        aparece(el.querySelector('.cab'), tl, .05, { dy: -20 });
        m.pts.forEach((x, i) => animPino(el, i, tl, Math.min(2.2, c.dur * .45) + .05 + i * .3, r.map.project([x.lon, x.lat]), true));
        r.colisao();
      },
      textos: () => [p.titulo, ...m.pts.map(x => x.nome)],
    };
  });

  /* 10. mapa.rota — V2.1: uma rota OU comparação de até 3 rotas (distâncias), círculo máximo nos trechos longos,
   * permanência no enquadramento final, rota 12 px com contorno, pinos 40 px, rótulos 42 px. */
  V2.registrar({
    id: 'mapa.rota', nome: 'Mapa com rota animada (e comparação de distâncias)', tratamento: 'mapa', tom: 'escuro',
    objetivo: 'Mostrar um trajeto, deslocamento ou ligação — ou comparar trajetos: a linha se desenha no ritmo da fala, com a distância.',
    funcoes: ['rota', 'trajeto', 'deslocamento', 'ligacao', 'comparar_distancias'],
    params: { titulo: '≤ 36', pontos: 'origem/destino {nome, lon, lat}', rota: 'opcional: [[lon,lat],…] do trajeto real', distancia_km: 'distância oficial (sem ela: "≈ calculada pelo traçado")',
      rotas: 'comparação: 2–3 × {nome ≤ 18, rota [[lon,lat]…], distancia_km?, cor?}', tipo: "'maritima' | 'terrestre' | 'aerea' | 'canal' (o geo.py valida se a rota marítima atravessa terra)", kicker: "padrão 'TRAJETO'", nota: 'fonte/observação ≤ 60' },
    fundo: 'próprio (MapLibre)', layout: 'cabeçalho 340–470; rotas enquadradas em 470–1160; distância (ou barras de comparação) em 1010–1190, sem cobrir a rota',
    paleta: 'rota 1 amarela, 2 ciano, 3 coral; 12 px + contorno escuro + brilho; pinos 40 px', animacao: 'câmera vai do contexto ao enquadramento das rotas e PARA (últimos 35%); cada rota se desenha com ponto na ponta; distância conta junto',
    duracao: [3.5, 6, 9], limites: { titulo: 36, nome: 18, rotas: 3 }, legenda: 'livre',
    area_segura: 'y 340–1200', legibilidade: 'distância 64 px mono; nomes 42 px',
    rejeicao: ['rota inventada (sem pontos nos fatos)', 'rota marítima que atravessa continente (geo.validar_rota)', 'distância calculada apresentada como oficial'],
    transicao: 'zoom',
    exemplo: { params: { kicker: 'TRAJETO', titulo: 'Do *Caribe* ao *Pacífico*', distancia_km: 80, tipo: 'canal', pontos: [{ nome: 'Colón', lon: -79.9, lat: 9.36 }, { nome: 'Cidade do Panamá', lon: -79.53, lat: 8.96 }],
      rota: [[-79.915, 9.37], [-79.92, 9.27], [-79.87, 9.2], [-79.8, 9.16], [-79.72, 9.13], [-79.68, 9.1], [-79.64, 9.05], [-79.6, 9.01], [-79.57, 8.96], [-79.55, 8.9]], folga: .45, nota: 'Distância: Wikipédia' }, dur: 6, fala: 'São oitenta quilômetros do Caribe ao Pacífico.' },
  }, (p, ctx) => {
    const comp = !!p.rotas;
    p._pad = comp ? { bottom: 1920 - (985 - 20 * Math.max(0, (p.rotas.length - 2))) } : { bottom: 1920 - 1070 };   // painel/distância não cobrem a rota
    const m = motorMapa(p, ctx, 'rota');
    const rs = comp ? p.rotas.slice(0, 3).map((r, i) => ({ nome: r.nome, km: r.distancia_km ? +r.distancia_km : m.trilhas[i].total, oficial: !!r.distancia_km, cor: r.cor || CORES_ROTA[i] }))
      : [{ nome: '', km: p.distancia_km ? +p.distancia_km : m.total, oficial: !!p.distancia_km, cor: CORES_ROTA[0] }];
    const mx = Math.max(...rs.map(r => r.km), 1);
    const painel = comp ? `<div class="abs cmpd" data-g="cmpd" data-txt="1" style="left:72px;right:150px;top:${1000 - 40 * Math.max(0, rs.length - 2)}px;padding:16px 22px;background:rgba(7,12,22,.88)">
        ${rs.map((r, i) => `<div style="display:flex;align-items:center;gap:16px;margin:${i ? 12 : 0}px 0 0"><span style="flex:none;width:230px;font-weight:800;font-size:30px;color:${r.cor};text-transform:uppercase">${esc(r.nome)}</span>
          <div style="flex:1;height:22px;background:rgba(255,255,255,.08)"><div class="bk bk${i}" style="height:100%;width:0;background:${r.cor}"></div></div>
          <span class="kv kv${i}" style="flex:none;width:200px;text-align:right;font-family:var(--f-dado);font-weight:700;font-size:34px;color:#fff">0 km</span></div>`).join('')}
        <div style="font-family:var(--f-dado);font-size:26px;color:rgba(255,255,255,.65);margin-top:10px">${rs.some(r => !r.oficial) ? '≈ calculado pelo traçado desenhado' : ''}${p.nota ? ' · ' + esc(p.nota) : ''}</div></div>`
      : `<div class="abs dist" data-g="dist" data-txt="1" style="left:72px;top:1092px;display:flex;align-items:baseline;gap:14px;background:rgba(7,12,22,.88);padding:10px 22px;border-left:8px solid var(--amarelo)">
          <span class="dv" style="font-family:var(--f-dado);font-weight:700;font-size:64px;color:#fff">0</span><span style="font-family:var(--f-dado);font-size:32px;color:var(--amarelo)">km${rs[0].oficial ? '' : ' (≈ pelo traçado)'}</span></div>`;
    return {
      html: `<div class="mapa-host" data-ocupa="1"></div>${moldura}<div class="rotulos abs" style="inset:0"></div>
        ${m.trilhas.map((t, i) => `<div class="abs bolinha b${i}" style="width:34px;height:34px;margin:-17px 0 0 -17px;border-radius:50%;background:#fff;box-shadow:0 0 0 9px ${rs[i] ? rs[i].cor : '#FFD21F'}88,0 0 30px ${rs[i] ? rs[i].cor : '#FFD21F'};opacity:0"></div>`).join('')}
        ${m.pts.map((x, i) => pinoHTML(i, x.nome, '')).join('')}${cabecalho(p, p.kicker || (comp ? 'DISTÂNCIAS' : 'TRAJETO'))}${painel}${ATR}`,
      montar: el => m.montar(el),
      async upd(tl, el, c) {
        // câmera: chega ao enquadramento final em 40% da cena e fica (só um empurrão de 3% para não congelar)
        const tc = Math.min(1.6, c.dur * .3), kc = eio(tl / tc);
        const desenho = [.9, Math.max(1.6, c.dur * .62)], n = m.trilhas.length, fatia = (desenho[1] - desenho[0]) / n;
        const kr = m.trilhas.map((_, i) => eio((tl - desenho[0] - i * fatia) / Math.max(1.2, fatia)));
        const pontas = [];
        const r = await m.upd(tl, el, kc, map => { m.trilhas.forEach((_, i) => { const pr = m.parcial(kr[i], i); pontas[i] = pr.ponta;
          map.getSource(`rota${i}`).setData({ type: 'Feature', geometry: { type: 'LineString', coordinates: kr[i] > 0 ? pr.coords : [] } }); }); });
        if (!r) return;
        aparece(el.querySelector('.cab'), tl, .05, { dy: -20 });
        m.trilhas.forEach((_, i) => { const b = el.querySelector('.b' + i); if (pontas[i]) { const q = r.map.project(pontas[i]); b.style.left = q.x + 'px'; b.style.top = q.y + 'px'; } b.style.opacity = kr[i] > 0 && kr[i] < 1 ? 1 : 0; });
        const t0s = m.pts.map((_, i) => i === 0 ? .7 : desenho[0] + fatia * n * .95), qs = m.pts.map(x => r.map.project([x.lon, x.lat]));
        m.pts.forEach((x, i) => animPino(el, i, tl, t0s[i], qs[i], i === 0, qs.filter((q2, j) => j !== i).map(q2 => [q2.x, q2.y])));
        if (comp) { aparece(el.querySelector('.cmpd'), tl, .8, { dy: 20 }); rs.forEach((x, i) => { el.querySelector('.bk' + i).style.width = (100 * x.km / mx * kr[i]) + '%'; el.querySelector('.kv' + i).textContent = fmt(x.km * kr[i], 0) + ' km'; }); }
        else { el.querySelector('.dv').textContent = fmt(rs[0].km * kr[0], 0); aparece(el.querySelector('.dist'), tl, .8, { dx: -20, dy: 0 }); }
        r.colisao();
      },
      textos: () => [p.titulo, ...rs.map(x => String(Math.round(x.km)) + ' ' + x.nome), ...m.pts.map(x => x.nome)],
    };
  });

  /* 11. mapa.territorio */
  V2.registrar({
    id: 'mapa.territorio', nome: 'Mapa com zoom e destaque territorial', tratamento: 'mapa', tom: 'escuro',
    objetivo: 'Destacar um país/território inteiro, sua forma e vizinhança, aproximando do contexto continental.',
    funcoes: ['territorio', 'pais', 'fronteira', 'regiao'],
    params: { pais: 'nome PT/EN ou ISO-A3 (Natural Earth)', titulo: '≤ 36', dado: 'linha curta sobre o território ≤ 40 (opcional)', kicker: "padrão 'TERRITÓRIO'" },
    fundo: 'próprio (MapLibre)', layout: 'cabeçalho 340–480; território enquadrado em 430–1060; nome do país no centróide; dado em faixa embaixo',
    paleta: 'território amarelo 85% com borda brilhante; vizinhos e mares rotulados', animacao: 'aproxima com leve rotação; território acende (preenchimento + brilho da borda); vizinhos aparecem',
    duracao: [3, 4.5, 6], limites: { titulo: 36, dado: 40 }, legenda: 'livre',
    area_segura: 'y 340–1100', legibilidade: 'nome do território 44 px 900',
    rejeicao: ['país não encontrado no Natural Earth', 'território histórico diferente das fronteiras atuais sem aviso'],
    transicao: 'zoom',
    exemplo: { params: { pais: 'Panama', kicker: 'TERRITÓRIO', titulo: 'Um país *cortado* ao meio', dado: '75 mil km² · 4,4 milhões de habitantes', folga: .25, max_paises: 2 }, dur: 4.5, fala: 'O Panamá é um país estreito, cortado pelo canal.' },
  }, (p, ctx) => {
    const m = motorMapa(p, ctx, 'territorio');
    const c0 = p.pais_geo ? [p.pais_geo.properties.label_x, p.pais_geo.properties.label_y] : null;
    return {
      html: `<div class="mapa-host" data-ocupa="1"></div>${moldura}<div class="rotulos abs" style="inset:0"></div>
        <div class="abs nmp" data-g="nmp" data-txt="1" style="font-weight:900;font-size:46px;letter-spacing:4px;color:#0b0f17;background:var(--amarelo);padding:6px 18px;text-transform:uppercase;opacity:0;white-space:nowrap">${esc(p.pais_nome || p.pais || '')}</div>
        ${cabecalho(p, p.kicker || 'TERRITÓRIO')}
        ${p.dado ? `<div class="abs dd" data-g="dd" data-txt="1" style="left:72px;top:1090px;font-family:var(--f-dado);font-weight:700;font-size:34px;color:#fff;background:rgba(7,12,22,.85);padding:12px 22px;border-left:6px solid var(--amarelo)">${esc(p.dado)}</div>` : ''}${ATR}`,
      montar: el => m.montar(el),
      async upd(tl, el, c) {
        const ka = eo5((tl - 1.0) / .8);
        const r = await m.upd(tl, el, eio(tl / Math.min(2.0, c.dur * .45)), map => {
          map.setPaintProperty('alvo', 'fill-opacity', .82 * ka); map.setPaintProperty('alvo-borda', 'line-opacity', ka);
          map.setPaintProperty('alvo-borda-brilho', 'line-opacity', .9 * ka * (.7 + .3 * Math.sin(tl * 4))); });
        if (!r) return;
        aparece(el.querySelector('.cab'), tl, .05, { dy: -20 });
        const nm = el.querySelector('.nmp'); if (c0) { const q = r.map.project(c0); nm.style.left = clamp(q.x - nm.offsetWidth / 2, 90, 920 - nm.offsetWidth) + 'px'; nm.style.top = clamp(q.y - nm.offsetHeight / 2 - 70, 500, 960) + 'px'; }
        nm.style.opacity = eo5((tl - 1.4) / .4);
        aparece(el.querySelector('.dd'), tl, 1.8, { dx: -20, dy: 0 });
        r.colisao();
      },
      textos: () => [p.titulo, p.pais_nome, p.dado],
    };
  });
})();
