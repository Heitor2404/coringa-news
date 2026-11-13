/* MAPAS V2 — MapLibre GL JS (BSD-3) + Natural Earth (domínio público), sem servidor de mapas: o Python recorta as
 * camadas do enquadramento (src/v2/geo.py) e a câmera é DETERMINÍSTICA (jumpTo por quadro + espera os tiles).
 * Rótulos em HTML posicionados com map.project(): tipografia do Coringa, sem depender de fontes de glifos.          */
(function () {
  const { esc, hl, clamp, lerp, eo, eo5, eio, back, aparece, caber, fmt } = V2.U;
  const H = V2.H;
  const COR = { mar: '#0a1a2f', mar2: '#0d2340', terra: '#26344b', terra2: '#2d3d57', borda: '#5d7598', costa: '#8fa9cf', rio: '#4f86c6', lago: '#0f2a4c', alvo: '#FFD21F', rota: '#FFD21F' };
  const PAD = { top: 430, bottom: 860, left: 110, right: 190 };     // área útil do mapa: y 430–1060, x 110–890

  function estilo(geo, p) {
    const fc = x => x || { type: 'FeatureCollection', features: [] };
    return {
      version: 8, sources: {
        paises: { type: 'geojson', data: fc(geo.paises), maxzoom: 8, tolerance: .25 },
        lagos: { type: 'geojson', data: fc(geo.lagos), maxzoom: 9, tolerance: .2 },
        rios: { type: 'geojson', data: fc(geo.rios), maxzoom: 9, tolerance: .2 },
        alvo: { type: 'geojson', data: p.pais_geo ? { type: 'FeatureCollection', features: [p.pais_geo] } : fc(null), maxzoom: 8 },
        rota: { type: 'geojson', data: { type: 'Feature', geometry: { type: 'LineString', coordinates: [] } }, maxzoom: 10 },
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
        { id: 'rota-brilho', type: 'line', source: 'rota', layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': COR.rota, 'line-width': 22, 'line-blur': 14, 'line-opacity': .55 } },
        { id: 'rota', type: 'line', source: 'rota', layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': COR.rota, 'line-width': 8 } },
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
  const cam = (map, bb) => { const c = map.cameraForBounds([[bb[0], bb[1]], [bb[2], bb[3]]], { padding: PAD });
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
    const rota = (p.rota || (tipo === 'rota' ? pts.map(x => [x.lon, x.lat]) : [])).map(([a, b]) => [+a, +b]);
    const cum = [0]; for (let i = 1; i < rota.length; i++) cum.push(cum[i - 1] + hav(rota[i - 1], rota[i]));
    const total = cum[cum.length - 1] || 0;
    function parcial(k) {   // a rota até a fração k do comprimento
      if (rota.length < 2) return { coords: rota, ponta: rota[0] };
      const alvo = total * k; let i = cum.findIndex(c => c >= alvo); if (i < 1) i = k <= 0 ? 1 : cum.length - 1;
      const f = (alvo - cum[i - 1]) / ((cum[i] - cum[i - 1]) || 1), ponta = [lerp(rota[i - 1][0], rota[i][0], clamp(f)), lerp(rota[i - 1][1], rota[i][1], clamp(f))];
      return { coords: [...rota.slice(0, i), ponta], ponta };
    }
    return {
      pts, rota, total, parcial,
      async montar(el) {
        const host = el.querySelector('.mapa-host');
        map = new maplibregl.Map({ container: host, style: estilo(p.geo || {}, p), interactive: false, attributionControl: false, fadeDuration: 0,
          canvasContextAttributes: { preserveDrawingBuffer: true, antialias: true }, center: [0, 0], zoom: 1, renderWorldCopies: false, maxPitch: 60 });
        await new Promise(r => map.once('load', r));
        const bb = p.bbox; B = cam(map, bb); B.bearing = p.bearing || 0; B.pitch = p.pitch || 0;
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
      <div class="kicker" style="font-size:24px;color:var(--amarelo)">${esc(rot)}</div>
      ${p.titulo ? `<div class="tt" data-txt="1" style="font-weight:900;font-size:50px;line-height:1.05;margin-top:8px;text-transform:uppercase">${hl(p.titulo)}</div>` : ''}</div>`;
  const moldura = `<div class="abs" data-deco="1" style="inset:0;pointer-events:none;background:linear-gradient(180deg,rgba(7,11,18,.65) 0%,rgba(7,11,18,0) 24%,rgba(7,11,18,0) 56%,rgba(7,11,18,.85) 80%,rgba(7,11,18,.95) 100%)"></div>`;
  const ATR = '<div class="abs atr" data-g="atr" data-opcional="1" style="right:160px;top:1112px;font-family:var(--f-dado);font-size:24px;color:rgba(255,255,255,.55)">Natural Earth · MapLibre</div>';
  const pinoHTML = (i, nome, sub) => `<div class="pino pn${i}" style="opacity:0"><div class="onda"></div><div class="onda o2"></div><div class="nucleo"></div></div>
     <div class="abs rot-mapa destaque lb${i}" data-g="pt${i}" style="opacity:0">${esc(nome)}${sub ? `<div style="font-family:var(--f-dado);font-weight:400;font-size:24px;letter-spacing:1px;margin-top:4px;color:#3a4558">${esc(sub)}</div>` : ''}</div>`;
  function animPino(el, i, tl, t0, q, cima) {
    const pn = el.querySelector('.pn' + i), lb = el.querySelector('.lb' + i); if (!pn || !q) return;
    const k = back((tl - t0) / .45); pn.style.left = q.x + 'px'; pn.style.top = q.y + 'px'; pn.style.opacity = clamp((tl - t0) / .1);
    pn.querySelector('.nucleo').style.transform = `scale(${clamp(k, 0, 1.3)})`;
    pn.querySelectorAll('.onda').forEach((o, j) => { const ph = ((tl - t0 + j * .6) % 1.2) / 1.2; o.style.transform = `scale(${1 + ph * 4})`; o.style.opacity = tl > t0 ? (1 - ph) * .8 : 0; });
    const w = lb.offsetWidth, hh = lb.offsetHeight; lb.style.left = clamp(q.x - w / 2, 90, 920 - w) + 'px'; lb.style.top = (cima ? q.y - hh - 44 : q.y + 40) + 'px';
    const kl = eo5((tl - t0 - .25) / .4); lb.style.opacity = kl; lb.style.transform = `translateY(${(1 - kl) * (cima ? 16 : -16)}px)`;
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
      html: `<div class="mapa-host"></div>${moldura}<div class="rotulos abs" style="inset:0"></div>${m.pts.map((x, i) => pinoHTML(i, x.nome, x.sub || coord(x.lon, x.lat))).join('')}${cabecalho(p, p.kicker || 'ONDE FICA')}${ATR}`,
      montar: el => m.montar(el),
      async upd(tl, el, c) {
        const kc = eio((tl - .1) / Math.min(2.4, c.dur * .6));
        const r = await m.upd(tl, el, kc); if (!r) return;
        aparece(el.querySelector('.cab'), tl, .05, { dy: -20 });
        m.pts.forEach((x, i) => animPino(el, i, tl, Math.min(2.4, c.dur * .6) + .05 + i * .3, r.map.project([x.lon, x.lat]), true));
        r.colisao();
      },
      textos: () => [p.titulo, ...m.pts.map(x => x.nome)],
    };
  });

  /* 10. mapa.rota */
  V2.registrar({
    id: 'mapa.rota', nome: 'Mapa com rota animada', tratamento: 'mapa', tom: 'escuro',
    objetivo: 'Mostrar um trajeto, deslocamento ou ligação: a linha se desenha no ritmo da fala, com distância.',
    funcoes: ['rota', 'trajeto', 'deslocamento', 'ligacao'],
    params: { titulo: '≤ 36', pontos: 'origem/destino {nome, lon, lat}', rota: 'opcional: [[lon,lat],…] do trajeto real', distancia_km: 'distância oficial (se não vier, mostra ≈ calculada)', kicker: "padrão 'TRAJETO'" },
    fundo: 'próprio (MapLibre)', layout: 'cabeçalho 340–480; rota enquadrada em 430–1060; contador de distância no canto inferior esquerdo (1000–1100)',
    paleta: 'rota amarela 8 px com brilho; pinos de origem/destino', animacao: 'câmera assenta; a linha avança com um ponto na ponta; distância conta junto',
    duracao: [3.5, 5, 7], limites: { titulo: 36 }, legenda: 'livre',
    area_segura: 'y 340–1100', legibilidade: 'distância 64 px mono',
    rejeicao: ['rota inventada (sem pontos nos fatos)', 'distância sem fonte apresentada como exata'],
    transicao: 'zoom',
    exemplo: { params: { kicker: 'TRAJETO', titulo: 'Do *Caribe* ao *Pacífico*', distancia_km: 80, pontos: [{ nome: 'Colón', lon: -79.9, lat: 9.36 }, { nome: 'Cidade do Panamá', lon: -79.53, lat: 8.96 }],
      rota: [[-79.915, 9.37], [-79.92, 9.27], [-79.87, 9.2], [-79.8, 9.16], [-79.72, 9.13], [-79.68, 9.1], [-79.64, 9.05], [-79.6, 9.01], [-79.57, 8.96], [-79.55, 8.9]], folga: .45 }, dur: 5.5, fala: 'São oitenta quilômetros do Caribe ao Pacífico.' },
  }, (p, ctx) => {
    const m = motorMapa(p, ctx, 'rota'), km = p.distancia_km ? +p.distancia_km : m.total;
    return {
      html: `<div class="mapa-host"></div>${moldura}<div class="rotulos abs" style="inset:0"></div>
        <div class="abs bolinha" style="width:30px;height:30px;margin:-15px 0 0 -15px;border-radius:50%;background:#fff;box-shadow:0 0 0 8px rgba(255,210,31,.45),0 0 30px var(--amarelo);opacity:0"></div>
        ${m.pts.map((x, i) => pinoHTML(i, x.nome, '')).join('')}${cabecalho(p, p.kicker || 'TRAJETO')}
        <div class="abs dist" data-g="dist" data-txt="1" style="left:72px;top:1010px;display:flex;align-items:baseline;gap:14px;background:rgba(7,12,22,.82);padding:10px 22px;border-left:6px solid var(--amarelo)">
          <span class="dv" style="font-family:var(--f-dado);font-weight:700;font-size:64px;color:#fff">0</span><span style="font-family:var(--f-dado);font-size:30px;color:var(--amarelo)">km${p.distancia_km ? '' : ' (≈)'}</span></div>${ATR.replace('right:160px', 'right:160px')}`,
      montar: el => m.montar(el),
      async upd(tl, el, c) {
        const kc = eio((tl) / 1.2), kr = eio((tl - .9) / Math.max(1.5, c.dur - 2.2));
        let ponta = null;
        const r = await m.upd(tl, el, kc, map => { const pr = m.parcial(kr); ponta = pr.ponta; map.getSource('rota').setData({ type: 'Feature', geometry: { type: 'LineString', coordinates: kr > 0 ? pr.coords : [] } }); });
        if (!r) return;
        aparece(el.querySelector('.cab'), tl, .05, { dy: -20 });
        const b = el.querySelector('.bolinha'); if (ponta) { const q = r.map.project(ponta); b.style.left = q.x + 'px'; b.style.top = q.y + 'px'; } b.style.opacity = kr > 0 && kr < 1 ? 1 : 0;
        m.pts.forEach((x, i) => animPino(el, i, tl, i === 0 ? .8 : .9 + Math.max(1.5, c.dur - 2.2) * .95, r.map.project([x.lon, x.lat]), i === 0));
        el.querySelector('.dv').textContent = fmt(km * kr, 0); aparece(el.querySelector('.dist'), tl, .8, { dx: -20, dy: 0 });
        r.colisao();
      },
      textos: () => [p.titulo, String(km), ...m.pts.map(x => x.nome)],
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
      html: `<div class="mapa-host"></div>${moldura}<div class="rotulos abs" style="inset:0"></div>
        <div class="abs nmp" data-g="nmp" data-txt="1" style="font-weight:900;font-size:46px;letter-spacing:4px;color:#0b0f17;background:var(--amarelo);padding:6px 18px;text-transform:uppercase;opacity:0;white-space:nowrap">${esc(p.pais_nome || p.pais || '')}</div>
        ${cabecalho(p, p.kicker || 'TERRITÓRIO')}
        ${p.dado ? `<div class="abs dd" data-g="dd" data-txt="1" style="left:72px;top:1020px;font-family:var(--f-dado);font-weight:700;font-size:32px;color:#fff;background:rgba(7,12,22,.85);padding:12px 22px;border-left:6px solid var(--amarelo)">${esc(p.dado)}</div>` : ''}${ATR}`,
      montar: el => m.montar(el),
      async upd(tl, el, c) {
        const ka = eo5((tl - 1.0) / .8);
        const r = await m.upd(tl, el, eio(tl / Math.min(2.2, c.dur * .55)), map => {
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
