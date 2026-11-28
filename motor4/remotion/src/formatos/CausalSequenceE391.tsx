import React from 'react';
import {AbsoluteFill,Audio,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
import {causalFrame,validateCausalSequence,type CausalSequence} from './Causal2DCoreE391';
const colors={rock:'#72777D',magma:'#DF5844',void:'#14171B',boundary:'#4C5158'};
type Caption={start:number;end:number;words:{w:string;hl:boolean}[]};
export type Props={sequence:CausalSequence;duracao:number;private_review_only:boolean;audio?:string;captions:Caption[];probe?:boolean};
export const CausalSequenceView:React.FC<Props>=({sequence,duracao,private_review_only,audio,captions,probe})=>{
 if(!private_review_only)throw Error('E391-PRIVATE');
 validateCausalSequence(sequence,duracao);
 const elapsed=useCurrentFrame()/useVideoConfig().fps,f=causalFrame(sequence,elapsed);
 const host=React.useRef<HTMLDivElement>(null),cap=captions.find(g=>g.start<=elapsed&&elapsed<g.end);
 React.useLayoutEffect(()=>{
  if(!probe||!host.current)return;
  const rows=Array.from(host.current.querySelectorAll<HTMLElement>('[data-causal-text]')).map(e=>({text:e.textContent,role:e.dataset.causalText,fit:e.scrollWidth<=e.clientWidth+1&&e.scrollHeight<=e.clientHeight+1}));
  console.log('E391_CAUSAL '+JSON.stringify({...f,rows,fit:rows.every(r=>r.fit)}));
 },[probe,sequence,elapsed]);
 const label=(v:string,x:number,y:number,w:number,h:number,size:number,color:string,weight:number)=><div data-causal-text="label" style={{position:'absolute',left:x,top:y,width:w,height:h,fontSize:size,color,fontWeight:weight,lineHeight:1.1,overflow:'hidden'}}>{v}</div>;
 return <AbsoluteFill style={{background:'#000',fontFamily:'Inter,Arial,sans-serif'}}>
  {audio&&<Audio src={staticFile(audio)}/>}
  <div ref={host} style={{position:'absolute',inset:0}}>
   <div style={{position:'absolute',left:66,top:300,fontSize:28,fontWeight:800,color:'#F5F5F5',letterSpacing:2.1}}>CORINGA <span style={{color:'#E9B949'}}>EXPLICA</span></div>
   <div style={{position:'absolute',left:66,top:346,width:140,height:5,background:'#E9B949'}}/>
   {label(f.title,66,390,839,54,43,'#F5F5F5',900)}
   {label('ESQUEMA EXPLICATIVO · SEM ESCALA',66,450,839,34,25,'#E9B949',800)}
   <svg viewBox="0 0 840 550" style={{position:'absolute',left:66,top:495,width:839,height:550}} overflow="hidden">
    <defs><marker id="arrow-e391" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#E9B949"/></marker></defs>
    {f.layers.map(l=><polygon key={l.id} points={l.points.map(p=>p.join(',')).join(' ')} fill={colors[l.kind]} stroke={l.kind==='magma'?'#FF9E75':'#B7BCC1'} strokeWidth={l.kind==='void'?1.4:2.5} strokeLinejoin="round"/>)}
    {f.arrows.map((a,i)=><line key={i} x1={a.from[0]} y1={a.from[1]} x2={a.to[0]} y2={a.to[1]} stroke="#E9B949" strokeWidth="6" strokeLinecap="round" markerEnd="url(#arrow-e391)" opacity={Math.min(1,.25+f.progress)}/>)}
   </svg>
   {label(f.label,66,1060,839,48,37,'#E9B949',800)}
   {label(sequence.credit,66,1135,839,30,22,'#D0D0D0',600)}
   <div style={{position:'absolute',left:66,top:1170,width:839,display:'flex',gap:6}}>{sequence.states.map((s,i)=><div key={s.id} style={{flex:1,height:4,background:i<=f.index?'#E9B949':'#353535'}}/>)}</div>
   {cap&&<div data-causal-text="subtitle" style={{position:'absolute',left:66,top:1190,width:839,height:150,fontSize:60,fontWeight:900,lineHeight:1.08,color:'#F5F5F5',overflow:'hidden'}}>{cap.words.map((w,i)=><span key={i} style={{color:w.hl?'#E9B949':'#F5F5F5'}}>{w.w}{i<cap.words.length-1?' ':''}</span>)}</div>}
   {label('PRÉVIA PRIVADA · NÃO PUBLICAR',66,1800,839,35,22,'#8B8B8B',600)}
  </div>
 </AbsoluteFill>;
};
