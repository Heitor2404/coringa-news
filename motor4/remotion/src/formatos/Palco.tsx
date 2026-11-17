// PALCO PERSISTENTE (gramática observada nas referências: o cenário fica, os elementos entram e saem sobre ele).
// mapa  = MapLibre real com Natural Earth/OSM (sem tiles externos), destaques de região e rota medida.
// tecnico = mapa técnico escuro (contorno + grade) para estrutura abstrata.  mesa = fundo de dossiê com luz e objetos.
// Troca de palco: dissolve de 0,5 s (mudança de cenário justificada pelo beat). Câmera do mapa muda só em keyframes.
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { continueRender, delayRender, useCurrentFrame, useVideoConfig } from 'remotion';
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

export function cameraEm(pk: PalcoKey[], t: number): { centro: [number, number]; zoom: number } {
  const ks = pk.filter(k => k.camera);
  if (!ks.length) return { centro: [0, 0], zoom: 2 };
  let a = ks[0];
  for (const k of ks) if (t >= k.t) a = k;
  const i = ks.indexOf(a);
  if (i > 0) {
    const ant = ks[i - 1], d = a.dur_camera ?? 1.2;
    if (d > 0 && t < a.t + d) {
      const e = easeIO(clamp((t - a.t) / d));
      return { centro: [lerp(ant.camera!.centro[0], a.camera!.centro[0], e), lerp(ant.camera!.centro[1], a.camera!.centro[1], e)], zoom: lerp(ant.camera!.zoom, a.camera!.zoom, e) };
    }
  }
  return a.camera!;
}

const vis = (t: number, t0: number, t1?: number, e = .45, s = .3) => clamp((t - t0) / e) * (t1 == null ? 1 : clamp((t1 - t) / s));

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

  useEffect(() => {
    const c0 = cameraEm(P.palco, 0);
    let m: ML.Map | null = null;
    const sources: any = Object.fromEntries(Object.entries(fc).map(([k, v]) => [k, { type: 'geojson', data: v }]));
    (P.rotas || []).forEach((_, i) => { sources[`rota_${i}`] = { type: 'geojson', data: turf.featureCollection([]) }; });
    // graticulado de carta a cada 0,5° (o mar deixa de ser um vazio liso; é o "papel" do mapa)
    const grat: any[] = [];
    for (let lo = -90; lo <= -70; lo += .5) grat.push(turf.lineString([[lo, 0], [lo, 18]]));
    for (let la = 0; la <= 18; la += .5) grat.push(turf.lineString([[-90, la], [-70, la]]));
    sources.grat = { type: 'geojson', data: turf.featureCollection(grat) };
    const layers: any[] = [
      { id: 'mar', type: 'background', paint: { 'background-color': T.mar } },
      { id: 'grat', type: 'line', source: 'grat', paint: { 'line-color': T.borda, 'line-width': 1, 'line-opacity': .13 } },
      { id: 'costa-luz', type: 'line', source: 'paises', paint: { 'line-color': T.agua, 'line-width': 14, 'line-opacity': .16, 'line-blur': 10 } },
      { id: 'terra', type: 'fill', source: 'paises', paint: { 'fill-color': T.terra } },
      ...(P.destaques || []).map((d, i) => ({ id: `dest_${i}`, type: 'fill', source: d.fonte, filter: ['==', ['get', 'name'], d.nome],
        paint: { 'fill-color': cor(d.cor), 'fill-opacity': 0 } })),
      { id: 'borda', type: 'line', source: 'paises', paint: { 'line-color': T.borda, 'line-width': 2, 'line-opacity': .8 } },
      { id: 'lagos', type: 'fill', source: 'lagos', paint: { 'fill-color': T.agua, 'fill-opacity': .9 } },
      ...(P.destaques || []).filter(d => d.fonte === 'lagos').map((d, i) => ({ id: `destl_${i}`, type: 'line', source: 'lagos', filter: ['==', ['get', 'name'], d.nome],
        paint: { 'line-color': cor(d.cor), 'line-width': 6, 'line-opacity': 0 } })),
      ...(P.rotas || []).flatMap((r, i) => [
        { id: `rota_s_${i}`, type: 'line', source: `rota_${i}`, layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': '#000', 'line-width': 26, 'line-opacity': .45, 'line-blur': 6 } },
        { id: `rota_l_${i}`, type: 'line', source: `rota_${i}`, layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': cor(r.cor), 'line-width': 15 } }]),
    ];
    carregarML().then(ml => {
      m = new ml.Map({ container: ref.current!, style: { version: 8, sources, layers } as any, center: c0.centro, zoom: c0.zoom, interactive: false,
        fadeDuration: 0, attributionControl: false, canvasContextAttributes: { preserveDrawingBuffer: true, antialias: true } as any } as any);
      m.on('error', (e: any) => console.log('MAPLIBRE_ERRO', String(e && (e.error?.message || e.message || e))));
      m.on('load', () => { setMap(m); continueRender(h0); });
    });
    return () => { m && m.remove(); };
  }, []);

  const [, force] = useState(0);
  useEffect(() => {
    if (!map) return;
    const h = delayRender(`palco mapa ${frame}`);
    const c = cameraEm(P.palco, t);
    map.jumpTo({ center: c.centro, zoom: c.zoom });
    let li = 0;
    (P.destaques || []).forEach((d, i) => {
      const v = vis(t, d.t0, d.t1, .6, .5);
      map.setPaintProperty(`dest_${i}`, 'fill-opacity', .82 * v);
      if (d.fonte === 'lagos') map.setPaintProperty(`destl_${li++}`, 'line-opacity', v);
    });
    (P.rotas || []).forEach((r, i) => {
      const k = easeIO(clamp((t - r.t0) / Math.max(.01, r.t1 - r.t0))) * (r.ate ?? 1);
      const some = r.some != null ? clamp((r.some - t) / .4 + 1) : 1;
      const parte = !rota || k <= 0 || some <= 0 ? turf.featureCollection([]) : turf.featureCollection([turf.lineSliceAlong(rota, 0, Math.max(.01, km * k), { units: 'kilometers' })]);
      (map.getSource(`rota_${i}`) as ML.GeoJSONSource).setData(parte as any);
      map.setPaintProperty(`rota_l_${i}`, 'line-opacity', some);
    });
    map.once('idle', () => { force(x => x + 1); continueRender(h); });
    map.triggerRepaint();
  }, [map, frame]);

  const proj = (ll: [number, number]) => (map ? map.project(ll) : { x: -999, y: -999 });
  // rótulos do mapa em HTML (fontes locais), área segura + colisão (mesma regra do mapa.rota, ERR-056)
  const rots = (P.rotulos || []).filter(r => vis(t, r.t0, r.t1) > 0);
  const caixas = rots.map(r => { const p = proj(r.lonlat); const fs = r.estilo === 'oceano' ? 34 : 32; const w = r.nome.length * fs * .66 + 40;
    return r.estilo === 'ponto' ? { x: p.x + 30, y: p.y - 28, w, h: 56 } : { x: p.x - w / 2, y: p.y - 24, w, h: 48 }; });
  const pos = arrumar(caixas);
  return (
    <div style={{ position: 'absolute', inset: 0, opacity: opac }}>
      <div ref={ref} style={{ position: 'absolute', width: W, height: H }} />
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 42%, rgba(0,0,0,0) 45%, rgba(0,0,0,.55) 100%)' }} />
      {/* atribuição obrigatória dos dados (Natural Earth; OSM/ODbL quando há rota) — rodapé, fora da legenda e do crédito */}
      <div data-atribuicao="1" style={{ position: 'absolute', left: 72, top: 1206, fontFamily: P.tokens.fontes.dado, fontSize: 18, color: 'rgba(255,255,255,.55)',
        textShadow: '0 1px 4px #000', whiteSpace: 'nowrap' }}>{(P.geo?.meta?.atribuicao || ['Natural Earth']).join(' · ')}</div>
      {rots.map((r, i) => {
        const v = vis(t, r.t0, r.t1), p = proj(r.lonlat), c = pos[i];
        if (r.estilo === 'ponto') return (<React.Fragment key={i}>
          <div style={{ position: 'absolute', left: p.x - 13, top: p.y - 13, width: 26, height: 26, borderRadius: 13, background: P.tokens.cores.destaque,
            border: '5px solid #fff', boxShadow: '0 4px 14px rgba(0,0,0,.6)', opacity: v, transform: `scale(${.5 + .5 * v})` }} />
          <div data-rotulo="ponto" style={{ position: 'absolute', left: c.x, top: c.y, opacity: v, padding: '8px 16px', background: 'rgba(5,8,15,.86)',
            borderLeft: `6px solid ${P.tokens.cores.destaque}`, fontFamily: P.tokens.fontes.titulo, fontWeight: 900, fontSize: 32, color: '#fff',
            textTransform: 'uppercase', whiteSpace: 'nowrap' }}>{r.nome}</div></React.Fragment>);
        return <div key={i} data-rotulo="area" style={{ position: 'absolute', left: c.x, top: c.y, width: c.w, textAlign: 'center', opacity: v * .92,
          fontFamily: r.estilo === 'oceano' ? P.tokens.fontes.dado : P.tokens.fontes.titulo, fontWeight: 800, fontSize: r.estilo === 'oceano' ? 34 : 32,
          letterSpacing: r.estilo === 'oceano' ? 8 : 2, color: r.estilo === 'lago' ? '#DDF3FF' : 'rgba(225,236,255,.9)', textTransform: 'uppercase',
          textShadow: '0 2px 12px rgba(0,0,0,.95)', whiteSpace: 'nowrap' }}>{r.nome}</div>;
      })}
    </div>
  );
};

export const PalcoTecnico: React.FC<{ P: FormatoProps; opac: number }> = ({ P, opac }) => {
  const T = P.tokens.palco.tecnico;
  // planta técnica do assunto (lago + eixo da rota), não um recorte retangular de países
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
    <div style={{ position: 'absolute', inset: 0, opacity: opac, background: T.fundo }}>
      <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
        <defs><pattern id="grade" width="60" height="60" patternUnits="userSpaceOnUse"><path d="M60 0H0V60" fill="none" stroke={T.grade} strokeWidth="1.2" /></pattern></defs>
        <rect width={W} height={H} fill="url(#grade)" />
        {d && <path d={d} fill="rgba(127,227,240,.05)" stroke={T.linha} strokeOpacity={.3} strokeWidth={2.4} strokeDasharray="10 8" />}
      </svg>
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 40%, rgba(0,0,0,.6) 100%)' }} />
    </div>
  );
};

export const PalcoMesa: React.FC<{ P: FormatoProps; opac: number }> = ({ P, opac }) => {
  const T = P.tokens.palco.mesa;
  return (
    <div style={{ position: 'absolute', inset: 0, opacity: opac, background: T.fundo }}>
      <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(ellipse at 50% 38%, ${T.luz} 0%, rgba(0,0,0,0) 62%)` }} />
      <svg width={W} height={H} style={{ position: 'absolute', inset: 0, opacity: .5 }}>
        <defs><pattern id="pont" width="36" height="36" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.4" fill="rgba(255,255,255,.07)" /></pattern></defs>
        <rect width={W} height={H} fill="url(#pont)" />
      </svg>
    </div>
  );
};
