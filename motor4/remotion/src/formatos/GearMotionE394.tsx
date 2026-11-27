import React from 'react';import {AbsoluteFill,useCurrentFrame,useVideoConfig} from 'remotion';
import {Gear,gearState} from './Mechanism2DOtherModels';
import cfg from './mechanisms2d-probes.json';
import {editorialCamera} from './EditorialMotionE394';
export const GearMotionE394:React.FC<{private_review_only:boolean;probe?:boolean}>=({private_review_only,probe})=>{
 if(!private_review_only)throw Error('E394-PRIVATE');const t=useCurrentFrame()/useVideoConfig().fps,s=gearState(t),g=cfg.demo.gears.geometry;
 const d=g.driverCenter,e=g.drivenCenter;
 const focus=s.current.action==='drive'?{x:d[0],y:d[1]}:s.current.action==='ratio'||s.current.action==='result'?{x:e[0],y:e[1]}:{x:431,y:690};
 const c=editorialCamera(t,{left:196,top:485,right:815,bottom:925},{left:80,top:470,right:900,bottom:1165},focus,{x:500,y:690},s.current.at,1.27);
 const ref=React.useRef<SVGSVGElement>(null);React.useLayoutEffect(()=>{if(!probe||!ref.current)return;const rows=Array.from(ref.current.querySelectorAll<SVGGraphicsElement>('[data-text]')).map(e=>{const b=e.getBBox();return {text:e.textContent,fit:b.x>=65&&b.x+b.width<=910&&b.y>=290&&b.y+b.height<=1390}});console.log('E394_GEAR '+JSON.stringify({rotation:s.rotation,output:s.outputRotation,ratio:s.ratio,camera:c,rows,fit:rows.every(r=>r.fit),opaque:ref.current.querySelectorAll('[data-rigid="true"] > g[opacity="1"]').length===2}));},[t,probe]);
 const txt=(str:string,x:number,y:number,size:number,fill='#F5F5F5')=><text data-text="true" x={x} y={y} fontWeight="900" fontSize={size} fill={fill}>{str}</text>;
 return <AbsoluteFill style={{background:'#000'}}><svg ref={ref} viewBox="0 0 1080 1920" width="100%" height="100%" style={{fontFamily:'Inter,Arial,sans-serif'}}>
 <defs><linearGradient id="gear-gold" x1="0" y1="0" x2=".6" y2="1"><stop stopColor="#F3D3A3"/><stop offset=".45" stopColor="#B88743"/><stop offset="1" stopColor="#694421"/></linearGradient><linearGradient id="gear-steel" x1="0" y1="0" x2=".6" y2="1"><stop stopColor="#D8E5E7"/><stop offset=".48" stopColor="#6A8794"/><stop offset="1" stopColor="#293D49"/></linearGradient></defs>
 {txt('CORINGA',66,326,28)}{txt('EXPLICA',216,326,28,'#E9B949')}<rect x="66" y="346" width="140" height="5" fill="#E9B949"/>
 {txt('COMO AS ENGRENAGENS',66,405,48)}{txt('TRANSMITEM MOVIMENTO?',66,457,48)}
 <g transform={`translate(${c.tx} ${c.ty}) scale(${c.scale})`}>
 <path d="M222 918 H789" stroke="#66737C" strokeWidth="16" strokeLinecap="round"/><path d={`M${d[0]} ${d[1]} V918 M${e[0]} ${e[1]} V918`} stroke="#384753" strokeWidth="34"/>
 <g data-rigid="true"><Gear x={d[0]} y={d[1]} r={g.driverRadius} teeth={g.driverTeeth} angle={s.rotation} fill="url(#gear-gold)" highlight="#F0C77D" opacity={1}/></g>
 <g data-rigid="true"><Gear x={e[0]} y={e[1]} r={g.drivenRadius} teeth={g.drivenTeeth} angle={s.outputRotation} fill="url(#gear-steel)" highlight="#A4CAD3" opacity={1}/></g>
 </g>
 {txt('12 DENTES',66,1220,39,'#E9B949')}{txt('20 DENTES',540,1220,39,'#A4CAD3')}
 {txt(s.rotation>0?'SENTIDOS OPOSTOS':'DENTES CONECTADOS',66,1310,48)}
 {txt('MODELO IDEALIZADO · TESTE SEM NARRAÇÃO',66,1370,24,'#BABABA')}
 </svg></AbsoluteFill>;
};
