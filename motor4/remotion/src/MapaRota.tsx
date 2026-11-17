// mapa.rota — MapLibre GL (render real, sem tiles externos) + Natural Earth/TopoJSON + Turf (rota medida) + D3 Geo (localizador).
// Padrões determinísticos do exemplo oficial Remotion+MapLibre: interactive:false, fadeDuration:0, delayRender até 'idle'
// a cada quadro, --gl=angle e concorrência 1. Câmera: FIXA, salvo keyframes explícitos com 'revela' (o contrato valida).
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { AbsoluteFill, continueRender, delayRender, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import type * as ML from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import * as turf from '@turf/turf';
import { feature } from 'topojson-client';
import { geoOrthographic, geoPath } from 'd3-geo';
import world from 'world-atlas/countries-110m.json';
import { C, FD, FT, Fontes, W, H, clamp, easeIO, lerp } from './ident';

// MapLibre 6 (ESM) carregado da pasta pública como módulo nativo (o webpack do Remotion quebra o worker em módulo
// separado: o mapa nunca disparava 'load'). Mesmos arquivos de node_modules/maplibre-gl/dist, versão fixada.
let _ml: Promise<typeof ML> | null = null;
export const carregarML = () => (_ml ??= import(/* webpackIgnore: true */ staticFile('maplibre/maplibre-gl.js')).then((m: any) => {
  m.setWorkerUrl(staticFile('maplibre/maplibre-gl-worker.js')); return m as typeof ML; }));

export type Ponto = { nome: string; lonlat: [number, number]; t: number; tipo?: 'cidade' | 'eclusa' | 'oceano' | 'lago' | 'destaque'; lado?: 'esq' | 'dir' };
export type MapaProps = {
  duracao: number;
  geo: { topo: any; meta: any };
  camera: { t: number; centro: [number, number]; zoom: number }[];
  rota?: { de: number; ate: number; rotulo_distancia?: string; rotulo_t?: number } | null;
  pontos: Ponto[];
  areas?: { nome: string; lonlat: [number, number]; t: number; estilo?: 'oceano' | 'lago' | 'pais' }[];
  localizador?: { lonlat: [number, number]; t: number } | null;
  titulo?: { texto: string; t: number } | null;
};

const STYLE = (fc: Record<string, any>): any => ({
  version: 8,
  sources: Object.fromEntries(Object.entries(fc).map(([k, v]) => [k, { type: 'geojson', data: v }])),
  layers: [
    { id: 'mar', type: 'background', paint: { 'background-color': C.mapa_mar } },
    { id: 'paises', type: 'fill', source: 'paises', paint: { 'fill-color': C.mapa_terra } },
    { id: 'paises-borda', type: 'line', source: 'paises', paint: { 'line-color': C.mapa_borda, 'line-width': 1.6, 'line-opacity': .7 } },
    { id: 'lagos', type: 'fill', source: 'lagos', paint: { 'fill-color': C.agua, 'fill-opacity': .95 } },
    { id: 'rios', type: 'line', source: 'rios', paint: { 'line-color': C.agua_clara, 'line-width': 2, 'line-opacity': .7 } },
    { id: 'rota-sombra', type: 'line', source: 'rota_viva', layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: { 'line-color': '#000', 'line-width': 24, 'line-opacity': .4, 'line-blur': 6 } },
    { id: 'rota', type: 'line', source: 'rota_viva', layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: { 'line-color': C.amarelo, 'line-width': 14 } },
  ],
});

export function camEm(cam: MapaProps['camera'], t: number) {
  if (cam.length === 1 || t <= cam[0].t) return cam[0];
  for (let i = 0; i < cam.length - 1; i++) {
    const a = cam[i], b = cam[i + 1];
    if (t <= b.t) { const k = easeIO(clamp((t - a.t) / Math.max(.001, b.t - a.t))); return { t, centro: [lerp(a.centro[0], b.centro[0], k), lerp(a.centro[1], b.centro[1], k)] as [number, number], zoom: lerp(a.zoom, b.zoom, k) }; }
  }
  return cam[cam.length - 1];
}

// ÁREA SEGURA dos rótulos (auditoria 16/11, c2: cidade cortada na borda e oceano sob a legenda): nada fora de x 60–1020 nem na
// faixa de legenda (y ≥ 1170); rótulos não se sobrepõem (o seguinte desce/sobe até achar lugar).
export const SEGURA = { x0: 60, x1: 1020, y0: 200, y1: 1150 };
type Caixa = { x: number; y: number; w: number; h: number };
const cruza = (a: Caixa, b: Caixa) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
export function arrumar(pedidas: Caixa[]): Caixa[] {
  const out: Caixa[] = [];
  for (const c0 of pedidas) {
    let c = { ...c0, x: Math.min(Math.max(c0.x, SEGURA.x0), SEGURA.x1 - c0.w), y: Math.min(Math.max(c0.y, SEGURA.y0), SEGURA.y1 - c0.h) };
    for (let k = 1; k < 24 && out.some(o => cruza(o, c)); k++) {
      const dy = (k % 2 ? 1 : -1) * Math.ceil(k / 2) * (c0.h * .6 + 6);
      c = { ...c, y: Math.min(Math.max(c0.y + dy, SEGURA.y0), SEGURA.y1 - c0.h) };
    }
    out.push(c);
  }
  return out;
}
const larguraTexto = (txt: string, px: number, esp = 0) => txt.length * (px * .62 + esp) + 36;

const Localizador: React.FC<{ lonlat: [number, number]; vis: number }> = ({ lonlat, vis }) => {
  const R = 118;
  const proj = geoOrthographic().rotate([-lonlat[0] + 18, -lonlat[1] + 8]).translate([R + 6, R + 6]).scale(R).clipAngle(90);
  const path = geoPath(proj);
  const paises = feature(world as any, (world as any).objects.countries) as any;
  const p = proj(lonlat);
  return (
    <svg width={2 * R + 12} height={2 * R + 12} style={{ position: 'absolute', right: 160, top: 360, opacity: vis }}>
      <circle cx={R + 6} cy={R + 6} r={R} fill={C.mapa_mar} stroke={C.mapa_borda} strokeWidth={2} />
      <path d={path(paises) || ''} fill={C.mapa_terra} stroke={C.mapa_borda} strokeWidth={.6} />
      {p && <circle cx={p[0]} cy={p[1]} r={9} fill={C.amarelo} stroke="#fff" strokeWidth={3} />}
    </svg>
  );
};

export const MapaRota: React.FC<MapaProps> = (P) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const ref = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<ML.Map | null>(null);
  const [h0] = useState(() => delayRender('mapa: carregando estilo'));
  const fc = useMemo(() => {
    const o = P.geo.topo.objects;
    const fx = (k: string) => (o[k] ? (feature(P.geo.topo, o[k]) as any) : turf.featureCollection([]));
    return { paises: fx('paises'), lagos: fx('lagos'), rios: fx('rios'), rota: fx('rota') };
  }, [P.geo]);
  const rota = fc.rota.features[0] as any;
  const km = rota ? turf.length(rota, { units: 'kilometers' }) : 0;

  useEffect(() => {
    const c0 = P.camera[0];
    let m: ML.Map | null = null;
    carregarML().then(ml => { m = new ml.Map({ container: ref.current!, style: STYLE({ ...fc, rota_viva: turf.featureCollection([]) }),
      center: c0.centro, zoom: c0.zoom, interactive: false, fadeDuration: 0, attributionControl: false,
      canvasContextAttributes: { preserveDrawingBuffer: true, antialias: true } as any } as any);
    m.on('error', (e: any) => console.log('MAPLIBRE_ERRO', String(e && (e.error?.message || e.message || e))));
    m.on('load', () => { setMap(m); continueRender(h0); }); });
    return () => { m && m.remove(); };
  }, []);

  const [, force] = useState(0);
  useEffect(() => {
    if (!map) return;
    const h = delayRender(`mapa: quadro ${frame}`);
    const c = camEm(P.camera, t);
    map.jumpTo({ center: c.centro, zoom: c.zoom });
    if (rota && P.rota) {
      const k = easeIO(clamp((t - P.rota.de) / Math.max(.01, P.rota.ate - P.rota.de)));
      const parte = k <= 0 ? turf.featureCollection([]) : turf.featureCollection([turf.lineSliceAlong(rota, 0, Math.max(.01, km * k), { units: 'kilometers' })]);
      (map.getSource('rota_viva') as ML.GeoJSONSource).setData(parte as any);
    }
    map.once('idle', () => { force(x => x + 1); continueRender(h); });
    map.triggerRepaint();
  }, [map, frame]);

  const proj = (ll: [number, number]) => (map ? map.project(ll) : { x: -999, y: -999 });
  const vis = (t0: number) => clamp((t - t0) / .35);
  return (
    <AbsoluteFill style={{ background: C.mapa_mar }}>
      <Fontes />
      <div ref={ref} style={{ position: 'absolute', width: W, height: H }} />
      {/* rótulos em HTML (fontes locais da identidade, sem servidor de glifos), legíveis no celular (≥ 30 px) */}
      {(() => {
        const areas = (P.areas || []).map(a => { const p = proj(a.lonlat); const fs = a.estilo === 'oceano' ? 38 : 34; const esp = a.estilo === 'oceano' ? 10 : 3;
          const w = larguraTexto(a.nome, fs, esp), h = fs + 14; return { tipo: 'area' as const, a, p, w, h, cx: { x: p.x - w / 2, y: p.y - h / 2, w, h } }; });
        const pts = P.pontos.map(pt => { const p = proj(pt.lonlat); const w = larguraTexto(pt.nome, 34), h = 56;
          let esq = pt.lado === 'esq' || pt.lado === ('esquerda' as any);
          if (!esq && p.x + 34 + w > SEGURA.x1) esq = true;           // não cabe à direita: vai para a esquerda
          if (esq && p.x - 34 - w < SEGURA.x0) esq = false;
          return { tipo: 'ponto' as const, pt, p, w, h, esq, cx: { x: esq ? p.x - 34 - w : p.x + 34, y: p.y - 26, w, h } }; });
        const todos = [...pts, ...areas];
        const pos = arrumar(todos.map(x => x.cx));
        return todos.map((x, i) => {
          const c = pos[i];
          if (x.tipo === 'area') { const a = x.a; return (
            <div key={'a' + i} data-rotulo="area" style={{ position: 'absolute', left: c.x, top: c.y, width: c.w, textAlign: 'center', opacity: vis(a.t),
              fontFamily: a.estilo === 'pais' ? FT : FD, fontWeight: a.estilo === 'pais' ? 800 : 700, fontSize: a.estilo === 'oceano' ? 38 : 34,
              letterSpacing: a.estilo === 'oceano' ? 10 : 3, color: a.estilo === 'lago' ? '#DDF3FF' : 'rgba(220,235,255,.86)', textTransform: 'uppercase',
              textShadow: '0 2px 12px rgba(0,0,0,.9)', whiteSpace: 'nowrap' }}>{a.nome}</div>); }
          const pt = x.pt, v = vis(pt.t);
          return (<React.Fragment key={'p' + i}>
            <div style={{ position: 'absolute', left: x.p.x - 15, top: x.p.y - 15, width: 30, height: 30, borderRadius: 15, opacity: v,
              background: pt.tipo === 'eclusa' ? C.amarelo : '#fff', border: `6px solid ${pt.tipo === 'eclusa' ? '#fff' : C.amarelo}`,
              boxShadow: '0 0 0 8px rgba(255,210,31,.28), 0 6px 18px rgba(0,0,0,.6)', transform: `scale(${.6 + .4 * v})` }} />
            <div data-rotulo="ponto" style={{ position: 'absolute', left: c.x, top: c.y, opacity: v, whiteSpace: 'nowrap', padding: '8px 16px', background: 'rgba(8,10,14,.84)',
              borderLeft: `6px solid ${C.amarelo}`, fontFamily: FT, fontWeight: 900, fontSize: 34, color: '#fff', textTransform: 'uppercase' }}>{pt.nome}</div>
          </React.Fragment>);
        });
      })()}
      {P.rota && P.rota.rotulo_distancia && rota && (() => {
        const meio = turf.along(rota, km / 2, { units: 'kilometers' }).geometry.coordinates as [number, number]; const p = proj(meio);
        return <div style={{ position: 'absolute', left: Math.min(SEGURA.x1 - 260, Math.max(SEGURA.x0, p.x + 60)), top: Math.min(SEGURA.y1 - 60, Math.max(SEGURA.y0, p.y - 40)), opacity: vis(P.rota.rotulo_t ?? P.rota.ate),
          fontFamily: FD, fontWeight: 700, fontSize: 40, color: C.amarelo, textShadow: '0 2px 14px #000', whiteSpace: 'nowrap' }}>{P.rota.rotulo_distancia}</div>;
      })()}
      {P.localizador && <Localizador lonlat={P.localizador.lonlat} vis={vis(P.localizador.t)} />}
      {P.titulo && <div style={{ position: 'absolute', left: 72, top: 400, maxWidth: 620, opacity: vis(P.titulo.t), fontFamily: FT, fontWeight: 900, fontSize: 64,
        lineHeight: 1.02, color: '#fff', textTransform: 'uppercase', textShadow: '0 4px 20px rgba(0,0,0,.8)' }}>{P.titulo.texto}</div>}
      <div data-medida="mapa" data-rota-km={km.toFixed(2)} style={{ display: 'none' }} />
    </AbsoluteFill>
  );
};
