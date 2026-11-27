import React from 'react';
import {AbsoluteFill,Img,staticFile} from 'remotion';
import {panelGeometry,validateSourceStage,type SourceStage} from './SourceStageCoreE389';
export const SourceStageView:React.FC<{stage:SourceStage;asset:string;dimensions:number[];elapsed:number;duration:number;probe?:boolean}>=({stage:s,asset,dimensions,elapsed,duration,probe})=>{
 validateSourceStage(s,duration,asset,dimensions);
 const g=panelGeometry(s.panel,dimensions);
 const h=s.highlights.filter(x=>elapsed>=x.at).at(-1);
 const alpha=h?Math.min(1,Math.max(0,(elapsed-h.at)/.22)):0;
 const host=React.useRef<HTMLDivElement>(null);
 React.useLayoutEffect(()=>{
  if(!probe||!host.current)return;
  const rows=Array.from(host.current.querySelectorAll<HTMLElement>('[data-stage-text]')).map(e=>({text:e.textContent,fit:e.scrollWidth<=e.clientWidth+1&&e.scrollHeight<=e.clientHeight+1}));
  console.log('E389_STAGE '+JSON.stringify({stage:s.stage,group:s.group,panel:s.panel,geometry:g,active:h?.label||null,alpha,rows,fit:rows.every(x=>x.fit)}));
 },[probe,s,elapsed]);
 const text=(value:string,left:number,top:number,width:number,height:number,fontSize:number,color:string,weight:number)=><div data-stage-text style={{position:'absolute',left,top,width,height,fontSize,color,fontWeight:weight,lineHeight:1.1,overflow:'hidden'}}>{value}</div>;
 return <AbsoluteFill style={{background:'#000',fontFamily:'Inter,Arial,sans-serif'}}>
  <div ref={host} style={{position:'absolute',inset:0}}>
   <div style={{position:'absolute',left:66,top:300,fontSize:28,fontWeight:800,color:'#F5F5F5',letterSpacing:2.1}}>CORINGA <span style={{color:'#E9B949'}}>EXPLICA</span></div>
   <div style={{position:'absolute',left:66,top:346,width:140,height:5,background:'#E9B949'}}/>
   {text(s.title,66,403,839,54,39,'#F5F5F5',900)}
   {text('ESQUEMA '+(s.stage+1)+'/'+s.count+' · SEM ESCALA',66,453,839,34,25,'#E9B949',800)}
   <div style={{position:'absolute',left:g.x,top:g.y,width:g.width,height:g.height,overflow:'hidden'}}>
    <Img src={staticFile(asset)} style={{position:'absolute',left:g.offsetX,top:g.offsetY,width:g.sourceWidth,height:g.sourceHeight}}/>
    {h&&<svg width="100%" height="100%" viewBox="0 0 1000 1000" preserveAspectRatio="none" style={{position:'absolute',inset:0,opacity:alpha}}>
      <rect x={h.box[0]*1000} y={h.box[1]*1000} width={(h.box[2]-h.box[0])*1000} height={(h.box[3]-h.box[1])*1000} fill="none" stroke="#171717" strokeWidth="10"/>
      <rect x={h.box[0]*1000} y={h.box[1]*1000} width={(h.box[2]-h.box[0])*1000} height={(h.box[3]-h.box[1])*1000} fill="none" stroke="#F9CB42" strokeWidth="5" strokeDasharray="24 12"/>
    </svg>}
   </div>
   {h&&<div style={{opacity:alpha}}>{text(h.label,66,1095,839,48,37,'#E9B949',800)}</div>}
   {text(s.credit,66,1147,839,28,22,'#D0D0D0',600)}
  </div>
 </AbsoluteFill>;
};
