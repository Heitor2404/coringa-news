import React from 'react';
import {AbsoluteFill} from 'remotion';
import {validateScene,stateAt,type SceneData} from './SceneGraphCoreE201';
export type {SceneData} from './SceneGraphCoreE201';
export const SceneGraphE201:React.FC<{data:SceneData;t:number;duration:number;headline:string;source:string}>=({data,t,duration,headline,source})=>{
  validateScene(data,duration);
  const beat=data.beats.filter(b=>b.t<=t).slice(-1)[0]||data.beats[0];
  return <AbsoluteFill style={{background:'radial-gradient(ellipse at 45% 50%,#203C50,#0B1927 65%,#07111C)',fontFamily:'Inter,Arial,sans-serif',color:'#F5F2EB'}}>
    <div style={{position:'absolute',left:160,top:310,width:600,fontWeight:850,fontSize:26}}>CORINGA <span style={{color:'#FFD21F'}}>EXPLICA</span></div>
    <div style={{position:'absolute',left:160,top:360,width:600,fontWeight:800,fontSize:43,lineHeight:1.1}}>{headline}</div>
    <svg viewBox="0 0 900 800" style={{position:'absolute',left:30,top:530,width:930,height:827,overflow:'hidden'}} aria-label="Esquema ilustrativo">
      <defs><radialGradient id="scene-glow"><stop stopColor="#74A9BF" stopOpacity=".13"/><stop offset="1" stopColor="#74A9BF" stopOpacity="0"/></radialGradient></defs>
      <ellipse cx="450" cy="400" rx="445" ry="380" fill="url(#scene-glow)"/>
      {data.actors.map(a=>{const k=stateAt(a,t);return <g key={a.id} opacity={k.opacity} transform={'translate('+k.x+' '+k.y+') rotate('+k.angle+') scale('+k.scale+')'}>{a.shapes.map((s,i)=><path key={i} d={s.d} fill={s.fill} stroke={s.stroke||'none'} strokeWidth={s.sw||0} strokeLinecap="round" strokeLinejoin="round"/>)}</g>})}
    </svg>
    <div style={{position:'absolute',left:160,top:411,width:600,fontSize:29,fontWeight:800,lineHeight:1.08}}>{beat.text}</div>
    <div style={{position:'absolute',left:160,top:485,width:600,fontSize:19,color:'#C1D0DA',lineHeight:1.15}}>ESQUEMA SEM ESCALA · FONTE: {source}</div>
  </AbsoluteFill>;
};