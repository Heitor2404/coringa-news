// PALCO PERSISTENTE (direção de arte 17/11). O cenário fica; as camadas entram e saem sobre ele.
// mapa    = MapLibre com BASE RASTER licenciada (Natural Earth II no largo; Sentinel-2 cloudless 2016 no detalhe), trocada
//           pela escala (fade por zoom), destaques translúcidos com contorno, rota medida, escala gráfica e atribuição.
//           A câmera vem do plano: cada beat enquadra o SEU território (roi) dentro do quadro livre da composição
//           (foco + âncora em tela), com pan ponderado pela escala na transição e deriva lenta no beat.
// tecnico = planta técnica escura (estrutura abstrata).   mesa = mesa de investigação: madeira escura, luz de luminária, profundidade.
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Img, continueRender, delayRender, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import type * as ML from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import * as turf from '@turf/turf';
import { feature } from 'topojson-client';
import { geoMercator, geoPath } from 'd3-geo';
import { carregarML, arrumar } from '../MapaRota';
import { W, H, clamp, easeIO, lerp } from '../ident';
import type { FormatoProps, PalcoKey } from './tipos';

export const palcoEm = (pk: PalcoKey[], t: number) => {
  let i = 0;
  for (let k = 0; k < pk.length; k++) if (t >= pk[k].t) i = k;
  return i;
};

// ---------------------------------------------------------------- câmera (MESMA matemática de plano.camera_em)
const mercX = (lon: number) => (lon + 180) / 360;
const mercY = (lat: number) => { const s = Math.sin((Math.max(-85, Math.min(85, lat)) * Math.PI) / 180); return .5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI); };
const lonDe = (x: number) => x * 360 - 180;
const latDe = (y: number) => (Math.atan(Math.sinh(Math.PI * (1 - 2 * y))) * 180) / Math.PI;
type Cam = { foco: [number, number]; ancora: [number, number]; zoom: number };
const cam = (c: any): Cam => (c.foco ? c : { foco: c.centro, ancora: [W / 2, H / 2], zoom: c.zoom });

export function cameraEm(pk: PalcoKey[], t: number): { centro: [number, number]; zoom: number; fx: number; fy: number; ancora: [number, number] } {
  const ks = pk.filter(k => k.camera);
  if (!ks.length) return { centro: [0, 0], zoom: 2, fx: .5, fy: .5, ancora: [W / 2, H / 2] };
  let a = ks[0];
  for (const k of ks) if (t >= k.t) a = k;
  const i = ks.indexOf(a), ca = cam(a.camera), d = a.dur_camera ?? 1.2;
  let fx: number, fy: number, anc: [number, number], z: number;
  if (i > 0 && d > 0 && t < a.t + d) {
    const cb = cam(ks[i - 1].camera), e = easeIO(clamp((t - a.t) / d));
    z = lerp(cb.zoom, ca.zoom, e);
    const u = Math.abs(ca.zoom - cb.zoom) < 1e-3 ? e : (2 ** -cb.zoom - 2 ** -z) / (2 ** -cb.zoom - 2 ** -ca.zoom);
    fx = lerp(mercX(cb.foco[0]), mercX(ca.foco[0]), u); fy = lerp(mercY(cb.foco[1]), mercY(ca.foco[1]), u);
    anc = [lerp(cb.ancora[0], ca.ancora[0], e), lerp(cb.ancora[1], ca.ancora[1], e)];
  } else {
    fx = mercX(ca.foco[0]); fy = mercY(ca.foco[1]); anc = ca.ancora;
    z = ca.zoom + (a.deriva ?? 0) * Math.max(0, t - a.t - Math.max(0, d));
  }
  const ws = 512 * 2 ** z;
  const cx = fx - (anc[0] - W / 2) / ws, cy = fy - (anc[1] - H / 2) / ws;
  return { centro: [lonDe(cx), latDe(cy)], zoom: z, fx, fy, ancora: anc };
}

const vis = (t: number, t0: number, t1?: number, e = .45, s = .3) => clamp((t - t0) / e) * (t1 == null ? 1 : clamp((t1 - t) / s));
const rampa = (z: number, de?: number | null, ate?: number | null) => (de == null ? 1 : clamp((z - (de - .5)) / .8)) * (ate == null ? 1 : clamp(((ate + .3) - z) / .8));

// véu da composição (legibilidade sem cobrir o território): interpolado na troca de beat
const VEUS: Record<string, string> = {
  nenhum: 'linear-gradient(180deg, rgba(3,6,12,.55) 0%, rgba(3,6,12,0) 16%, rgba(3,6,12,0) 60%, rgba(3,6,12,.72) 100%)',
  topo: 'linear-gradient(180deg, rgba(3,6,12,.82) 0%, rgba(3,6,12,.55) 26%, rgba(3,6,12,0) 40%, rgba(3,6,12,0) 60%, rgba(3,6,12,.72) 100%)',
  base: 'linear-gradient(180deg, rgba(3,6,12,.5) 0%, rgba(3,6,12,0) 14%, rgba(3,6,12,0) 36%, rgba(3,6,12,.86) 46%, rgba(3,6,12,.9) 100%)',
  direita: 'linear-gradient(90deg, rgba(3,6,12,0) 0%, rgba(3,6,12,0) 50%, rgba(3,6,12,.86) 56%, rgba(3,6,12,.9) 100%), linear-gradient(180deg, rgba(3,6,12,0) 60%, rgba(3,6,12,.7) 100%)',
  documento: 'linear-gradient(180deg, rgba(3,6,12,.72) 0%, rgba(3,6,12,.62) 50%, rgba(3,6,12,.85) 100%)',
};

function escalaGrafica(lat: number, zoom: number) {
  const mpp = (40075016.686 * Math.cos((lat * Math.PI) / 180)) / (512 * 2 ** zoom);
  const alvo = 220 * mpp;
  const p = 10 ** Math.floor(Math.log10(alvo));
  const n = [5, 2, 1].map(k => k * p).find(v => v <= alvo) || p;
  return { px: n / mpp, txt: n >= 1000 ? `${(n / 1000).toLocaleString('pt-BR')} km` : `${n} m` };
}

export const PalcoMapa: React.FC<{ P: FormatoProps; opac: number }> = ({ P, opac }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const T = P.tokens.palco.mapa;
  const ref = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<ML.Map | null>(null);
  const [h0] = useState(() => delayRender('palco: mapa'));
  const fc = useMemo(() => {
    const o = P.geo?.topo?.objects || {};
    const fx = (k: string) => (o[k] ? (feature(P.geo!.topo, o[k]) as any) : turf.featureCollection([]));
    return { paises: fx('paises'), lagos: fx('lagos'), rios: fx('rios'), rota: fx('rota') };
  }, [P.geo]);
  const rota = fc.rota.features[0] as any;
  const km = rota ? turf.length(rota, { units: 'kilometers' }) : 0;
  const cor = (c?: string) => (c === 'agua' ? T.agua : c === 'destaque2' ? T.destaque2 : T.destaque);
  const rasters = P.rasters || [];

  useEffect(() => {
    const c0 = cameraEm(P.palco, 0);
    let m: ML.Map | null = null;
    const sources: any = Object.fromEntries(Object.entries(fc).map(([k, v]) => [k, { type: 'geojson', data: v }]));
    rasters.forEach(r => { sources[`r_${r.nome}`] = { type: 'image', url: staticFile(r.src), coordinates: r.cantos }; });
    (P.rotas || []).forEach((_, i) => { sources[`rota_${i}`] = { type: 'geojson', data: turf.featureCollection([]) }; });
    const grat: any[] = [];
    for (let lo = -100; lo <= -60; lo += 1) grat.push(turf.lineString([[lo, -10], [lo, 30]]));
    for (let la = -10; la <= 30; la += 1) grat.push(turf.lineString([[-100, la], [-60, la]]));
    sources.grat = { type: 'geojson', data: turf.featureCollection(grat) };
    const temRaster = rasters.length > 0;
    const layers: any[] = [
      { id: 'mar', type: 'background', paint: { 'background-color': T.mar } },
      ...(temRaster ? [] : [{ id: 'terra', type: 'fill', source: 'paises', paint: { 'fill-color': T.terra } }]),
      ...rasters.map(r => ({ id: `r_${r.nome}`, type: 'raster', source: `r_${r.nome}`, paint: {
        'raster-opacity': 0, 'raster-fade-duration': 0, 'raster-resampling': 'linear',
        'raster-saturation': r.ajuste?.saturacao ?? 0, 'raster-contrast': r.ajuste?.contraste ?? 0,
        'raster-brightness-min': r.ajuste?.brilho_min ?? 0, 'raster-brightness-max': r.ajuste?.brilho_max ?? 1 } })),
      { id: 'grat', type: 'line', source: 'grat', paint: { 'line-color': '#DCE8FF', 'line-width': 1, 'line-opacity': 0 } },
      ...(P.destaques || []).map((d, i) => ({ id: `dest_${i}`, type: 'fill', source: d.fonte, filter: ['==', ['get', 'name'], d.nome],
        paint: { 'fill-color': cor(d.cor), 'fill-opacity': 0 } })),
      { id: 'borda', type: 'line', source: 'paises', paint: { 'line-color': temRaster ? '#F4F1EA' : T.borda, 'line-width': 1.6, 'line-opacity': temRaster ? .42 : .8, 'line-dasharray': temRaster ? [3, 2] : [1, 0] } },
      ...(temRaster ? [] : [{ id: 'lagos', type: 'fill', source: 'lagos', paint: { 'fill-color': T.agua, 'fill-opacity': .9 } }]),
      ...(P.destaques || []).flatMap((d, i) => [
        { id: `destg_${i}`, type: 'line', source: d.fonte, filter: ['==', ['get', 'name'], d.nome], paint: { 'line-color': cor(d.cor), 'line-width': 16, 'line-blur': 12, 'line-opacity': 0 } },
        { id: `destl_${i}`, type: 'line', source: d.fonte, filter: ['==', ['get', 'name'], d.nome], layout: { 'line-join': 'round' }, paint: { 'line-color': cor(d.cor), 'line-width': 4.5, 'line-opacity': 0 } }]),
      ...(P.rotas || []).flatMap((r, i) => [
        { id: `rota_s_${i}`, type: 'line', source: `rota_${i}`, layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': '#000', 'line-width': 24, 'line-opacity': .5, 'line-blur': 8 } },
        { id: `rota_c_${i}`, type: 'line', source: `rota_${i}`, layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': '#0B0F17', 'line-width': 15 } },
        { id: `rota_l_${i}`, type: 'line', source: `rota_${i}`, layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': cor(r.cor), 'line-width': 9 } }]),
    ];
    carregarML().then(ml => {
      m = new ml.Map({ container: ref.current!, style: { version: 8, sources, layers } as any, center: c0.centro, zoom: c0.zoom, interactive: false,
        fadeDuration: 0, attributionControl: false, maxZoom: 18, canvasContextAttributes: { preserveDrawingBuffer: true, antialias: true } as any } as any);
      m.on('error', (e: any) => console.log('MAPLIBRE_ERRO', String(e && (e.error?.message || e.message || e))));
      m.on('load', () => { setMap(m); continueRender(h0); });
    });
    return () => { m && m.remove(); };
  }, []);

  const c = cameraEm(P.palco, t);
  // o quadro só é liberado DEPOIS que rótulos/território foram recalculados com a câmera deste quadro (sem atraso de 1 quadro)
  const [pronto, setPronto] = useState(-1);
  const pend = useRef<number | null>(null);
  useEffect(() => {
    if (pronto !== frame || pend.current == null) return;
    (window as any).__mapaQuadro = frame;
    const h = pend.current; pend.current = null; continueRender(h);
  }, [pronto, frame]);
  useEffect(() => {
    if (!map) return;
    const h = delayRender(`palco mapa ${frame}`);
    pend.current = h;
    map.jumpTo({ center: c.centro, zoom: c.zoom });
    rasters.forEach(r => map.setPaintProperty(`r_${r.nome}`, 'raster-opacity', rampa(c.zoom, r.de, r.ate)));
    map.setPaintProperty('grat', 'line-opacity', .09 * clamp((7.6 - c.zoom) / 1.2));
    (P.destaques || []).forEach((d, i) => {
      const v = vis(t, d.t0, d.t1, .6, .5);
      map.setPaintProperty(`dest_${i}`, 'fill-opacity', (d.fonte === 'lagos' ? .38 : .26) * v);
      map.setPaintProperty(`destg_${i}`, 'line-opacity', .55 * v);
      map.setPaintProperty(`destl_${i}`, 'line-opacity', v);
    });
    (P.rotas || []).forEach((r, i) => {
      const k = easeIO(clamp((t - r.t0) / Math.max(.01, r.t1 - r.t0))) * (r.ate ?? 1);
      const some = r.some != null ? clamp((r.some - t) / .4 + 1) : 1;
      const parte = !rota || k <= 0 || some <= 0 ? turf.featureCollection([]) : turf.featureCollection([turf.lineSliceAlong(rota, 0, Math.max(.01, km * k), { units: 'kilometers' })]);
      (map.getSource(`rota_${i}`) as ML.GeoJSONSource).setData(parte as any);
      ['rota_l_', 'rota_c_'].forEach(id => map.setPaintProperty(`${id}${i}`, 'line-opacity', some));
      map.setPaintProperty(`rota_s_${i}`, 'line-opacity', .5 * some);
    });
    map.once('idle', () => setPronto(frame));
    map.triggerRepaint();
  }, [map, frame]);

  // véu: composição atual × anterior (dissolve 0,6 s)
  const ki = palcoEm(P.palco, t), ka = P.palco[ki], kb = ki > 0 ? P.palco[ki - 1] : null;
  const kv = clamp((t - ka.t) / .6);
  const veuA = VEUS[ka.veu || 'nenhum'], veuB = kb ? VEUS[kb.veu || 'nenhum'] : null;
  const desfoque = ((ka.veu === 'documento' ? kv : 0) + (kb?.veu === 'documento' ? 1 - kv : 0)) * 5;

  const proj = (ll: [number, number]) => (map ? map.project(ll) : { x: -999, y: -999 });
  const rots = (P.rotulos || []).filter(r => vis(t, r.t0, r.t1) > 0);
  const caixas = rots.map(r => { const p = proj(r.lonlat); const fs = r.estilo === 'oceano' ? 30 : 32; const w = r.nome.length * fs * .68 + 44;
    return r.estilo === 'ponto' ? { x: p.x + 30, y: p.y - 28, w, h: 56 } : { x: p.x - w / 2, y: p.y - 24, w, h: 48 }; });
  const pos = arrumar(caixas);
  // território do beat em tela (para a medição nos quadros renderizados: nada de camada por cima)
  const roi = ka.roi && map ? (() => { const a = proj([ka.roi![0], ka.roi![3]]), b = proj([ka.roi![2], ka.roi![1]]); return { x: a.x, y: a.y, w: b.x - a.x, h: b.y - a.y }; })() : null;
  const esc = escalaGrafica(c.centro[1], c.zoom);
  const atrib = [...new Set([...rasters.filter(r => rampa(c.zoom, r.de, r.ate) > .02).map(r => r.atribuicao), ...(P.geo?.meta?.atribuicao || [])])];
  return (
    <div style={{ position: 'absolute', inset: 0, opacity: opac }}>
      <div ref={ref} style={{ position: 'absolute', width: W, height: H, filter: desfoque > .05 ? `blur(${desfoque}px)` : undefined }} />
      {veuB && <div style={{ position: 'absolute', inset: 0, background: veuB, opacity: 1 - kv }} />}
      <div style={{ position: 'absolute', inset: 0, background: veuA, opacity: kb ? kv : 1 }} />
      {roi && <div data-roi="1" style={{ position: 'absolute', left: roi.x, top: roi.y, width: roi.w, height: roi.h, pointerEvents: 'none' }} />}
      {/* escala gráfica: o espectador lê a distância (direção de arte: "escala legível") */}
      {c.zoom >= 6.5 && ka.veu !== 'documento' && (
        <div data-meta="escala" style={{ position: 'absolute', left: 1008 - esc.px, top: 318, width: esc.px, opacity: .92 }}>
          <div style={{ height: 8, borderLeft: '3px solid #fff', borderRight: '3px solid #fff', borderBottom: '3px solid #fff', boxShadow: '0 2px 6px rgba(0,0,0,.7)' }} />
          <div style={{ position: 'absolute', right: 0, top: -28, fontFamily: P.tokens.fontes.dado, fontWeight: 700, fontSize: 20, color: '#fff', textShadow: '0 1px 6px #000', whiteSpace: 'nowrap' }}>{esc.txt}</div>
        </div>)}
      {/* atribuição obrigatória (CC BY / ODbL): inteira, em até 2 linhas, acima da faixa de legenda */}
      <div data-atribuicao="1" data-meta="atribuicao" style={{ position: 'absolute', left: 72, top: 1174, width: 936, fontFamily: P.tokens.fontes.dado, fontSize: 18, lineHeight: '21px',
        color: 'rgba(255,255,255,.7)', textShadow: '0 1px 4px #000' }}>{atrib.join(' · ')}</div>
      {rots.map((r, i) => {
        const v = vis(t, r.t0, r.t1), p = proj(r.lonlat), q = pos[i];
        if (r.estilo === 'ponto') return (<React.Fragment key={i}>
          <div style={{ position: 'absolute', left: p.x - 12, top: p.y - 12, width: 24, height: 24, borderRadius: 12, background: P.tokens.cores.destaque,
            border: '4px solid #0B0F17', boxShadow: '0 0 0 3px #fff, 0 4px 14px rgba(0,0,0,.6)', opacity: v, transform: `scale(${.5 + .5 * v})` }} />
          <div data-rotulo="ponto" style={{ position: 'absolute', left: q.x, top: q.y, opacity: v, padding: '7px 16px', background: '#0B0F17',
            borderLeft: `6px solid ${P.tokens.cores.destaque}`, fontFamily: P.tokens.fontes.titulo, fontWeight: 900, fontSize: 30, color: '#fff',
            textTransform: 'uppercase', whiteSpace: 'nowrap', boxShadow: '0 6px 18px rgba(0,0,0,.5)' }}>{r.nome}</div></React.Fragment>);
        return <div key={i} data-rotulo="area" style={{ position: 'absolute', left: q.x, top: q.y, width: q.w, textAlign: 'center', opacity: v,
          fontFamily: r.estilo === 'oceano' ? P.tokens.fontes.dado : P.tokens.fontes.titulo, fontWeight: 800, fontSize: r.estilo === 'oceano' ? 30 : 32,
          letterSpacing: r.estilo === 'oceano' ? 7 : 2, color: r.estilo === 'lago' ? '#E6F7FF' : '#F4F1EA', textTransform: 'uppercase',
          textShadow: '0 0 10px rgba(0,0,0,.9), 0 2px 14px rgba(0,0,0,.95)', whiteSpace: 'nowrap', fontStyle: r.estilo === 'oceano' ? 'italic' : undefined }}>{r.nome}</div>;
      })}
    </div>
  );
};

export const PalcoTecnico: React.FC<{ P: FormatoProps; opac: number }> = ({ P, opac }) => {
  const T = P.tokens.palco.tecnico;
  const d = useMemo(() => {
    const o = P.geo?.topo?.objects;
    if (!o) return '';
    const lagos = o.lagos ? (feature(P.geo!.topo, o.lagos) as any) : null;
    const rota = o.rota ? (feature(P.geo!.topo, o.rota) as any) : null;
    const alvo = { type: 'FeatureCollection', features: [...(rota?.features || []), ...((lagos?.features || []).filter((f: any) => !rota || turf.booleanIntersects(f, rota.features[0])))] } as any;
    if (!alvo.features.length) return '';
    const pr = geoMercator().fitExtent([[120, 420], [W - 120, 1120]], alvo);
    return geoPath(pr)(alvo) || '';
  }, [P.geo]);
  return (
    <div style={{ position: 'absolute', inset: 0, opacity: opac, background: `radial-gradient(ellipse at 50% 40%, #0C2230 0%, ${T.fundo} 70%)` }}>
      <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <pattern id="grade" width="60" height="60" patternUnits="userSpaceOnUse"><path d="M60 0H0V60" fill="none" stroke={T.grade} strokeWidth="1.2" /></pattern>
          <pattern id="grade5" width="300" height="300" patternUnits="userSpaceOnUse"><path d="M300 0H0V300" fill="none" stroke={T.grade} strokeWidth="2.4" /></pattern>
        </defs>
        <rect width={W} height={H} fill="url(#grade)" />
        <rect width={W} height={H} fill="url(#grade5)" />
        {d && <path d={d} fill="rgba(127,227,240,.04)" stroke={T.linha} strokeOpacity={.22} strokeWidth={2.4} strokeDasharray="10 8" />}
      </svg>
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 45%, rgba(0,0,0,.6) 100%)' }} />
    </div>
  );
};

// MESA DE INVESTIGAÇÃO: madeira escura com veio e objetos fora de foco (imagem estática gerada por
// scripts/formatos_mesa.py — o filtro SVG por quadro estourou o tempo de render no Actions, 44114805861), luz de
// luminária, vinheta e aproximação lenta. Nada aleatório por quadro.
export const PalcoMesa: React.FC<{ P: FormatoProps; opac: number }> = ({ P, opac }) => {
  const T = P.tokens.palco.mesa as any;
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const resp = 1.03 + .025 * Math.sin((t / Math.max(1, P.duracao)) * Math.PI);
  return (
    <div style={{ position: 'absolute', inset: 0, opacity: opac, background: T.fundo, overflow: 'hidden' }}>
      <Img src={staticFile('formatos/mesa_madeira.jpg')} style={{ position: 'absolute', left: -60, top: -60, width: W + 120, height: H + 120,
        transform: `scale(${resp})`, transformOrigin: '50% 40%' }} />
      <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(ellipse 85% 55% at 50% 40%, ${T.luz} 0%, rgba(255,214,150,.05) 45%, rgba(0,0,0,0) 70%)`, mixBlendMode: 'screen' }} />
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 95% 70% at 50% 42%, rgba(0,0,0,0) 40%, rgba(0,0,0,.78) 100%)' }} />
      <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(0,0,0,.45) 0%, rgba(0,0,0,0) 18%, rgba(0,0,0,0) 62%, rgba(0,0,0,.7) 100%)' }} />
    </div>
  );
};
