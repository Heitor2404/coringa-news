import React from 'react';import {AbsoluteFill,useCurrentFrame,useVideoConfig} from 'remotion';
import {Gear,gearState} from './Mechanism2DOtherModels';
import cfg from './mechanisms2d-probes.json';
import {detailAt,svgCamera} from './CinematicDirectorE395';
import {editorialCamera} from './EditorialMotionE394';
export const GearMotionE394:React.FC<{private_review_only:boolean;probe?:boolean;visualRevision?:'E395'}>=({private_review_only,probe,visualRevision})=>{
 if(!private_review_only)throw Error('E394-PRIVATE');const t=useCurrentFrame()/useVideoConfig().fps,s=gearState(t),g=cfg.demo.gears.geometry;
 const d=g.driverCenter,e=g.drivenCenter;
 const focus=s.current.action==='drive'?{x:d[0],y:d[1]}:s.current.action==='ratio'||s.current.action==='result'?{x:e[0],y:e[1]}:{x:431,y:690};
 const c=editorialCamera(t,{left:196,top:485,right:815,bottom:925},{left:80,top:470,right:900,bottom:1165},focus,{x:500,y:690},s.current.at,1.27);
 const cinematic=visualRevision==='E395',detail=cinematic?detailAt(t,[{id:'mesh',start:1.15,end:3.5,roi:{left:350,top:586,right:505,bottom:790}}],{left:100,top:500,right:677,bottom:1030},2.5):null;
 const active=detail?.camera??c;
 const ref=React.useRef<SVGSVGElement>(null);React.useLayoutEffect(()=>{if(!probe||!ref.current)return;const rows=Array.from(ref.current.querySelectorAll<SVGGraphicsElement>('[data-text]')).map(e=>{const b=e.getBBox();return {text:e.textContent,fit:b.x>=65&&b.x+b.width<=910&&b.y>=290&&b.y+b.height<=1390}});console.log('E394_GEAR '+JSON.stringify({rotation:s.rotation,output:s.outputRotation,ratio:s.ratio,camera:c,detail:detail?{id:detail.id,roi:detail.roi,camera:detail.camera}:null,rows,fit:rows.every(r=>r.fit),opaque:ref.current.querySelectorAll('[data-rigid="true"] > g[opacity="1"]').length===2}));},[t,probe]);
 const txt=(str:string,x:number,y:number,size:number,fill='#F5F5F5')=><text data-text="true" x={x} y={y} fontWeight="900" fontSize={size} fill={fill}>{str}</text>;
 return <AbsoluteFill style={{background:'#000'}}><svg ref={ref} viewBox="0 0 1080 1920" width="100%" height="100%" style={{fontFamily:'Inter,Arial,sans-serif'}}>
 <defs><clipPath id="gear-stage"><rect x="66" y="475" width="840" height="675"/></clipPath><linearGradient id="gear-gold" x1="0" y1="0" x2=".6" y2="1"><stop stopColor="#F3D3A3"/><stop offset=".45" stopColor="#B88743"/><stop offset="1" stopColor="#694421"/></linearGradient><linearGradient id="gear-steel" x1="0" y1="0" x2=".6" y2="1"><stop stopColor="#D8E5E7"/><stop offset=".48" stopColor="#6A8794"/><stop offset="1" stopColor="#293D49"/></linearGradient></defs>
 {txt('CORINGA',66,326,28)}{txt('EXPLICA',216,326,28,'#E9B949')}<rect x="66" y="346" width="140" height="5" fill="#E9B949"/>
 {txt('COMO AS ENGRENAGENS',66,405,48)}{txt('TRANSMITEM MOVIMENTO?',66,457,48)}
 <g clipPath={cinematic?"url(#gear-stage)":undefined}><g transform={svgCamera(active)}><g id="e395-gear-art">
 <path d="M222 918 H789" stroke="#66737C" strokeWidth="16" strokeLinecap="round"/><path d={`M${d[0]} ${d[1]} V918 M${e[0]} ${e[1]} V918`} stroke="#384753" strokeWidth="34"/>
 <g data-rigid="true"><Gear x={d[0]} y={d[1]} r={g.driverRadius} teeth={g.driverTeeth} angle={s.rotation} fill="url(#gear-gold)" highlight="#F0C77D" opacity={1} cinematic={cinematic}/></g>
 <g data-rigid="true"><Gear x={e[0]} y={e[1]} r={g.drivenRadius} teeth={g.drivenTeeth} angle={s.outputRotation} fill="url(#gear-steel)" highlight="#A4CAD3" opacity={1} cinematic={cinematic}/></g>
 </g>
 {cinematic&&t>=1.15&&t<3.5&&<g><circle cx={d[0]+g.driverRadius} cy={d[1]} r="23" fill="none" stroke="#E9B949" strokeWidth="3" strokeDasharray="6 4"/><circle cx={d[0]+g.driverRadius} cy={d[1]} r="5" fill="#E9B949"/></g>}
 </g></g>
 {detail&&<g><rect x="675" y="490" width="229" height="200" rx="8" fill="#101010" stroke="#776746" strokeWidth="2"/><g transform="translate(630 351) scale(.32)"><use href="#e395-gear-art"/><rect x={detail.roi.left} y={detail.roi.top} width={detail.roi.right-detail.roi.left} height={detail.roi.bottom-detail.roi.top} fill="none" stroke="#E9B949" strokeWidth="6"/></g>{txt('VISTA GERAL',694,672,23,'#E9B949')}{txt('DETALHE · DENTES',66,510,26,'#E9B949')}</g>}
 {cinematic&&t>=3.5&&t<6.25&&<g>
 <path d="M110 1050 H382" stroke="#E9B949" strokeWidth="6" strokeLinecap="round"/><path d="M368 1036 L388 1050 368 1064" fill="none" stroke="#E9B949" strokeWidth="6"/>
 <path d="M862 1050 H588" stroke="#A4CAD3" strokeWidth="6" strokeLinecap="round"/><path d="M602 1036 L582 1050 602 1064" fill="none" stroke="#A4CAD3" strokeWidth="6"/>
 </g>}
 {cinematic&&t>=6.25&&<g>{txt('VELOCIDADE RELATIVA',66,970,30)}<rect x="66" y="992" width="540" height="27" rx="4" fill="#E9B949"/><rect x="66" y="1043" width={540*g.driverTeeth/g.drivenTeeth} height="27" rx="4" fill="#A4CAD3"/>{txt('100%',624,1018,30,'#E9B949')}{txt('60%',408,1069,30,'#A4CAD3')}</g>}
 {txt('12 DENTES',66,1220,39,'#E9B949')}{txt('20 DENTES',540,1220,39,'#A4CAD3')}
 {txt(cinematic?(t<1.15?'DENTES CONECTADOS':t<3.5?'CONTATO ENTRE DENTES':t<6.25?'SENTIDOS OPOSTOS':'MENOR VELOCIDADE'):s.rotation>0?'SENTIDOS OPOSTOS':'DENTES CONECTADOS',66,1310,48)}
 {txt('MODELO IDEALIZADO · TESTE SEM NARRAÇÃO',66,1370,24,'#BABABA')}
 </svg></AbsoluteFill>;
};
