/** Identidade editorial compartilhada dos TESTES 2D autorais.
 * Não há fundos holográficos, cards de mecanismo ou cópias de frames
 * de terceiros. Papel claro, contorno legível e ação como protagonista.
 */
import React from 'react';
import {AbsoluteFill} from 'remotion';
export type PaperLayoutProps={
  title:[string,string];section:string;index:number;total:number;
  caption:string;children:React.ReactNode;privateReviewOnly?:boolean;
};
export const PAPER={
  bg:'#EFE9DF',bottom:'#E5DDD1',ink:'#192D36',muted:'#617179',
  subtle:'#B8ADA0',gold:'#BD8529',teal:'#3E8790',deep:'#244F5F',
  white:'#F9F7F0',brown:'#B9804B'
};
export const PaperLayout:React.FC<PaperLayoutProps>=({
  title,section,index,total,caption,children,privateReviewOnly=true
})=><AbsoluteFill style={{
  background:PAPER.bg,fontFamily:'Inter,Arial,sans-serif',
  color:PAPER.ink,overflow:'hidden'
}}>
  <svg width="100%" height="100%" viewBox="0 0 1080 1920"
    preserveAspectRatio="xMidYMid meet">
    <defs>
      <linearGradient id="paper-gradient" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0" stopColor="#F6F2E9"/>
        <stop offset="1" stopColor={PAPER.bottom}/>
      </linearGradient>
      <linearGradient id="paper-gold-metal" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0" stopColor="#F3D3A3"/>
        <stop offset=".55" stopColor="#D19B59"/>
        <stop offset="1" stopColor="#97612F"/>
      </linearGradient>
      <linearGradient id="paper-teal-metal" x1="0" x2="1" y1="0" y2="1">
        <stop offset="0" stopColor="#92C7CA"/>
        <stop offset=".53" stopColor="#548F98"/>
        <stop offset="1" stopColor="#2B6470"/>
      </linearGradient>
      <linearGradient id="paper-steel" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0" stopColor="#6F8A96"/>
        <stop offset="1" stopColor="#283D4A"/>
      </linearGradient>
    </defs>
    <rect width="1080" height="1920" fill="url(#paper-gradient)"/>
    {children}
  </svg>
  <div style={{position:'absolute',top:305,left:156,width:600,
    display:'flex',alignItems:'center',gap:8,fontSize:26,
    fontWeight:900,letterSpacing:.4}}>
    CORINGA <span style={{color:PAPER.gold}}>EXPLICA</span>
  </div>
  <div style={{position:'absolute',top:354,left:157,width:600,
    fontSize:22,fontWeight:790,letterSpacing:1.3,color:PAPER.muted}}>
    {section}
  </div>
  <div style={{position:'absolute',top:395,left:155,width:690,
    fontSize:48,lineHeight:1.04,letterSpacing:-1.35,fontWeight:900}}>
    {title[0]}
    <div>{title[1]}</div>
  </div>
  <div style={{position:'absolute',top:1093,left:155,width:607,
    borderTop:'2px solid #B8ADA0',paddingTop:13}}>
    <div style={{fontSize:20,fontWeight:850,color:PAPER.gold,
      letterSpacing:1.2,marginBottom:8}}>
      {String(index).padStart(2,'0')} / {String(total).padStart(2,'0')}
    </div>
    <div style={{fontSize:caption.length>40?29:35,fontWeight:900,
      lineHeight:1.09,letterSpacing:-.45,maxWidth:600}}>
      {caption}
    </div>
  </div>
  <div style={{position:'absolute',top:1220,left:155,width:600,
    fontSize:17.5,fontWeight:670,color:PAPER.muted}}>
    ESQUEMA VETORIAL AUTORAL · MODELO IDEALIZADO
  </div>
  {privateReviewOnly&&<div style={{position:'absolute',left:0,right:0,
    bottom:56,textAlign:'center',fontWeight:770,letterSpacing:1.4,
    fontSize:19,color:PAPER.muted}}>
    PRÉVIA PRIVADA · NÃO PUBLICAR
  </div>}
</AbsoluteFill>;
