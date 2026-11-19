/** Mapa de direção DOCUMENTAL: país destacado, pin e rota configuráveis via roteiro.
 * Natural Earth/world-atlas local, SVG determinístico. Sem tiles de rede.
 * NÃO inventa roteiro ou posição. A rota é uma polilinha geográfica curada,
 * não simulação da trajetória real de um navio.
 */
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {feature} from 'topojson-client';
import {geoMercator,geoPath} from 'd3-geo';
import world from 'world-atlas/countries-110m.json';

export type GeoPoint={label:string;lonlat:[number,number];at?:number};
export type NarrativeMap={
  kind:'country'|'route';
  country_id:string; // ISO 3166-1 numeric (Natural Earth / world-atlas)
  center:[number,number]; // longitude, latitude (nunca latitude/longitude)
  scale:number;
  points:GeoPoint[];
  route?:{coords:[number,number][];label:string;at?:number};
  caption:string;
};
const GOLD='#FFD21F';
const clamp=(n:number,a=0,b=1)=>Math.max(a,Math.min(b,n));
const fade=(t:number,start=0)=>clamp((t-start)/.32);
const fc=feature(world as any,(world as any).objects.countries) as any;
const countries=fc.features as any[];
const id=(f:any)=>String(f.id??'').padStart(3,'0');

export const NarrativeMapStage:React.FC<{map:NarrativeMap;t:number}>=({map,t})=>{
  // Foco geográfico explícito — nunca deduzir escala de nomes de temas.
  const proj=geoMercator().center(map.center).translate([540,915]).scale(map.scale);
  const path=geoPath(proj);
  const highlighted=countries.find(f=>id(f)===map.country_id);
  const route=map.route?.coords?.map(c=>proj(c)).filter((p):p is [number,number]=>!!p);
  const d=route && route.length>=2 ? 'M'+route.map(p=>p.map(v=>v.toFixed(1)).join(',')).join('L') : '';
  const routeAt=map.route?.at??.4;
  const routeProgress=fade(t,routeAt)*clamp((t-routeAt)/1.9);
  return <AbsoluteFill style={{background:'#071421'}}>
    <svg viewBox="0 0 1080 1920" width="100%" height="100%" style={{fontFamily:'Inter,Arial,sans-serif'}}>
      <defs>
        <clipPath id="narrative-map-clip"><rect x="36" y="350" width="1008" height="1130" rx="12"/></clipPath>
        <pattern id="narrative-map-grid" width="90" height="90" patternUnits="userSpaceOnUse">
          <path d="M90 0H0V90" fill="none" stroke="#5A829A" strokeOpacity=".12"/>
        </pattern>
      </defs>
      <rect width="1080" height="1920" fill="#071421"/>
      <rect x="36" y="348" width="1008" height="1132" fill="#0E283C" stroke="#2E5268" strokeWidth="2" rx="12"/>
      <g clipPath="url(#narrative-map-clip)">
        <g opacity={1}>
        {countries.map((f,i)=><path key={i} d={path(f)||''} fill="#405A5E"
          stroke="#718E92" strokeWidth={1.5} strokeOpacity=".45"/>)}
        {highlighted&&<path d={path(highlighted)||''} fill="#B89B4A"
          stroke={GOLD} strokeWidth="5" strokeLinejoin="round"/>}
        </g>
        <rect x="36" y="350" width="1008" height="1130" fill="url(#narrative-map-grid)" pointerEvents="none"/>
        {d&&<g>
          <path d={d} stroke="#020B13" strokeWidth="16" strokeLinecap="round" strokeLinejoin="round" fill="none" opacity=".7"/>
          <path d={d} stroke={GOLD} strokeWidth="9" strokeLinecap="round"
            strokeLinejoin="round" fill="none" pathLength={1}
            strokeDasharray={routeProgress+' 1'} strokeDashoffset={0}/>
        </g>}
        {map.points.map((pt,i)=>{
          const xy=proj(pt.lonlat),visible=fade(t,pt.at??.25);
          if(!xy)return null;
          const [x,y]=xy;
          const bx=clamp(x+28,54,920),by=clamp(y-51,380,1365);
          return <g key={i} opacity={visible}>
            <line x1={x} y1={y} x2={bx} y2={by+22} stroke="#F3EBCB" strokeWidth="3" opacity=".75"/>
            <circle cx={x} cy={y} r="18" fill="#071421" stroke={GOLD} strokeWidth="7"/>
            <circle cx={x} cy={y} r="5" fill={GOLD}/>
            <rect x={bx} y={by} width={Math.min(350,pt.label.length*19+28)} height="49" rx="5" fill="#071421" fillOpacity=".9"/>
            <text x={bx+14} y={by+33} fontSize="28" fill="#F4F3EF" fontWeight="800">{pt.label.toUpperCase()}</text>
          </g>;
        })}
      </g>
      <rect x="52" y="1532" width="976" height="150" rx="12" fill="#091623"/>
      <path d="M82 1562H1000" stroke="#38586B" strokeWidth="2"/>
      <text x="82" y="1609" fill="#E8EDEB" fontSize="35" fontWeight="900">{map.caption.toUpperCase()}</text>
      <text x="82" y="1661" fill="#93AAB8" fontSize="23">
        {map.kind==='route'?'TRAJETO GEOGRÁFICO ESQUEMÁTICO · NÃO É RASTRO AIS':'BASE CARTOGRÁFICA · NATURAL EARTH / WORLD ATLAS'}
      </text>
      <text x="85" y="1710" fill="#94B1BF" fontSize="24">CARTOGRAFIA VETORIAL · COORDENADAS CURADAS</text>
      {map.route?.label&&<text x="82" y="1758" fill={GOLD} fontSize="27" fontWeight="800">
        {map.route.label.toUpperCase()}
      </text>}
    </svg>
  </AbsoluteFill>;
};
