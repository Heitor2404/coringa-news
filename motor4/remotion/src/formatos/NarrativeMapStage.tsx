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
type Rect={x:number;y:number;w:number;h:number};
const overlap=(a:Rect,b:Rect)=>a.x<b.x+b.w+10 && b.x<a.x+a.w+10 &&
  a.y<b.y+b.h+10 && b.y<a.y+a.h+10;

/** Evita que os nomes dos pontos próximos se cubram, independentemente do tema. */
export const placeMapLabels=(pts:{x:number;y:number;label:string}[]):Rect[]=>{
  const placed:Rect[]=[];
  for(const pt of pts){
    const w=Math.min(390,Math.max(136,pt.label.length*19+28));
    const x=clamp(pt.x+28,54,1032-w);
    const base=clamp(pt.y-51,380,1400);
    let candidate:Rect={x,y:base,w,h:49};
    for(let n=0;n<=16;n++){
      const offset=n===0?0:(n%2===1?-1:1)*Math.ceil(n/2)*66;
      const trial={x,y:clamp(base+offset,380,1400),w,h:49};
      if(!placed.some(p=>overlap(p,trial))){candidate=trial;break;}
    }
    placed.push(candidate);
  }
  return placed;
};

export const NarrativeMapStage:React.FC<{map:NarrativeMap;t:number}>=({map,t})=>{
  // Foco geográfico explícito — nunca deduzir escala de nomes de temas.
  const proj=geoMercator().center(map.center).translate([540,915]).scale(map.scale);
  const path=geoPath(proj);
  const highlighted=countries.find(f=>id(f)===map.country_id);
  const route=map.route?.coords?.map(c=>proj(c)).filter((p):p is [number,number]=>!!p);
  const d=route && route.length>=2 ? 'M'+route.map(p=>p.map(v=>v.toFixed(1)).join(',')).join('L') : '';
  const routeAt=map.route?.at??.4;
  const routeProgress=fade(t,routeAt)*clamp((t-routeAt)/1.9);
  const positions=map.points.map(pt=>({pt,xy:proj(pt.lonlat)}))
    .filter((p):p is {pt:GeoPoint;xy:[number,number]}=>!!p.xy);
  const labelBoxes=placeMapLabels(positions.map(p=>({x:p.xy[0],y:p.xy[1],label:p.pt.label})));
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
          stroke={GOLD} strokeWidth="5" strokeLinejoin="round" opacity={fade(t,.08)}/>} 
        </g>
        <rect x="36" y="350" width="1008" height="1130" fill="url(#narrative-map-grid)" pointerEvents="none"/>
        {d&&<g>
          <path d={d} stroke="#020B13" strokeWidth="16" strokeLinecap="round" strokeLinejoin="round" fill="none" opacity=".7"/>
          <path d={d} stroke={GOLD} strokeWidth="9" strokeLinecap="round"
            strokeLinejoin="round" fill="none" pathLength={1}
            strokeDasharray={routeProgress+' 1'} strokeDashoffset={0}/>
        </g>}
        {positions.map(({pt,xy},i)=>{
          const visible=fade(t,pt.at??.25);
          const [x,y]=xy;
          const {x:bx,y:by,w}=labelBoxes[i];
          return <g key={i} opacity={visible}>
            <line x1={x} y1={y} x2={bx} y2={by+22} stroke="#F3EBCB" strokeWidth="3" opacity=".75"/>
            <circle cx={x} cy={y} r="18" fill="#071421" stroke={GOLD} strokeWidth="7"/>
            <circle cx={x} cy={y} r="5" fill={GOLD}/>
            <rect x={bx} y={by} width={w} height="49" rx="5" fill="#071421" fillOpacity=".9"/>
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
