import React from 'react';
import {AbsoluteFill} from 'remotion';
import {validateScene,stateAt,type SceneData,validateSceneV2,stateAtV2,cameraAt,worldToScreen,BOX_V2,CAPTION_V2,type SceneDataV2} from './SceneGraphCoreE201';
export type {SceneData,SceneDataV2} from './SceneGraphCoreE201';
const GOLD='#FFD21F',INK='#F5F2EB';
const SceneGraphV2:React.FC<{data:SceneDataV2;t:number;duration:number;headline:string;source:string}>=({data,t,duration,headline,source})=>{
  validateSceneV2(data,duration);
  const cam=cameraAt(data.camera,t);
  const cap=data.captions.find(c=>t>=c.start&&t<c.end);
  const nat=data.nature==='esquema_com_dado_real'?'ESQUEMA ILUSTRATIVO + CONTORNO REAL':'ESQUEMA ILUSTRATIVO SEM ESCALA';
  // rótulos em espaço de TELA (tamanho constante), com prioridade: essencial em foco > essencial > efeito > partícula;
  // rótulo que colide com outro já colocado é omitido nesse quadro (sem texto sobre texto)
  type Lb={id:string;x:number;y:number;w:number;text:string;op:number;kind:string;pri:number};
  const cand:Lb[]=[];
  const drawn=data.actors.map(a=>{
    const k=stateAtV2(a,t);if(k.opacity<=0.003)return null;
    const [vx,vy,vw,vh]=a.view,m=Math.max(vw,vh),f=a.size/m;
    const [sx,sy]=worldToScreen(cam,k.x,k.y);const z=cam.zoom*k.scale;
    const rad=k.angle*Math.PI/180;
    const rw=vw*f*k.sx*z/2,rh=vh*f*k.sy*z/2;
    const hh=Math.abs(Math.sin(rad))*rw+Math.abs(Math.cos(rad))*rh;
    const ww=Math.abs(Math.cos(rad))*rw+Math.abs(Math.sin(rad))*rh;
    const flt=Math.abs(k.sat-1)>0.01?`url(#sat-${a.id})`:undefined;
    const janela=!a.label_t||(t>=a.label_t[0]&&t<=a.label_t[1]);
    if(a.label&&a.layer!=='contexto'&&k.opacity>0.5&&janela){
      const w=Math.min(620,a.label.length*15.5+34);
      cand.push({id:a.id,x:Math.min(870-w/2,Math.max(150+w/2,sx)),y:sy+hh+12+48<=1240?sy+hh+12:Math.max(BOX_V2[1],sy-hh-52),w,text:a.label,op:Math.min(1,(k.opacity-0.5)/0.35),kind:a.layer,
        pri:(a.layer==='essencial'?(k.opacity>0.9?3:2):a.layer==='efeito'?1:0)});
    }
    const essencial=a.layer==='essencial';
    return <g key={a.id}>
      {/* sombra de contato (profundidade 2.5D), só para atores essenciais */}
      {essencial&&<ellipse cx={sx} cy={sy+hh*0.96} rx={ww*0.78} ry={Math.max(5,hh*0.09)} fill="#000" opacity={0.32*k.opacity}/>}
      <g opacity={k.opacity} transform={`translate(${sx} ${sy}) rotate(${k.angle}) scale(${z*k.sx*f} ${z*k.sy*f}) translate(${-(vx+vw/2)} ${-(vy+vh/2)})`} filter={flt??(essencial?'url(#e202-pop)':undefined)}>
      {/* saturação < 1 = DESBOTAR: tira a cor e clareia (pálido), em vez de escurecer para cinza */}
      {flt&&<defs><filter id={`sat-${a.id}`}><feColorMatrix type="saturate" values={String(Math.min(1.5,k.sat))}/>
        {k.sat<1&&<feComponentTransfer>{(['R','G','B'] as const).map(c=>{const w=0.55*(1-k.sat);const F=c==='R'?'feFuncR':c==='G'?'feFuncG':'feFuncB';return React.createElement(F,{key:c,type:'linear',slope:1-w,intercept:w});})}</feComponentTransfer>}</filter></defs>}
      {a.shapes.map((s,i)=><path key={i} d={s.d} fill={s.fill} stroke={s.stroke||'none'} strokeWidth={(s.sw||0)} vectorEffect={a.layer==='contexto'?'non-scaling-stroke':undefined} strokeLinecap="round" strokeLinejoin="round"
        {...(a.tracado?{pathLength:1,strokeDasharray:`${k.draw} 1`}:{})}/>)}
      {a.tint_color&&k.tint>0.003&&<g opacity={k.tint}>{a.shapes.filter(s=>s.fill!=='none').map((s,i)=><path key={'t'+i} d={s.d} fill={a.tint_color}/>)}</g>}
    </g></g>;
  });
  const placed:Lb[]=[];
  for(const c of cand.sort((p,q)=>q.pri-p.pri)){
    const box=(l:Lb)=>[l.x-l.w/2-6,l.y-4,l.x+l.w/2+6,l.y+48];
    const b=box(c);
    if(b[3]>1240||b[1]<BOX_V2[1]-20)continue; // label lane: never place essential text in lower UI
    if(placed.some(p=>{const o=box(p);return !(b[2]<o[0]||b[0]>o[2]||b[3]<o[1]||b[1]>o[3]);}))continue;
    placed.push(c);
  }
  const labels=placed.map(l=><div key={'l'+l.id} style={{position:'absolute',left:l.x-l.w/2,top:l.y,width:l.w,textAlign:'center',opacity:l.op}}>
    <span style={{display:'inline-block',padding:'5px 14px',borderRadius:22,background:l.kind==='particula'||l.kind==='efeito'?'rgba(255,210,31,.94)':'rgba(8,18,30,.84)',color:l.kind==='particula'||l.kind==='efeito'?'#0B1927':INK,border:l.kind==='particula'||l.kind==='efeito'?'none':'2px solid rgba(255,210,31,.75)',fontSize:28,fontWeight:800,whiteSpace:'nowrap'}}>{l.text}</span></div>);
  return <AbsoluteFill style={{background:'radial-gradient(ellipse at 50% 38%,#1F3B52 0%,#0C1A2A 58%,#060D17 100%)',fontFamily:'Inter,Arial,sans-serif',color:INK,overflow:'hidden'}}>
    {/* ambiente de tela cheia, não essencial: grade sutil que acompanha a câmera (paralaxe 0,35) */}
    <svg width={1080} height={1920} style={{position:'absolute',inset:0,opacity:.18}}>
      <defs><pattern id="e202-grid" width={90} height={90} patternUnits="userSpaceOnUse" patternTransform={`translate(${-cam.x*.35} ${-cam.y*.35})`}>
        <circle cx={45} cy={45} r={2.2} fill="#8FB3CC"/></pattern></defs>
      <rect width={1080} height={1920} fill="url(#e202-grid)"/>
    </svg>
    <svg width={1080} height={1920} style={{position:'absolute',inset:0}} aria-label="Esquema ilustrativo">
      {/* bordas suaves acima do título e abaixo da legenda: o mundo pode exceder a área segura sem cortes duros */}
      <defs><linearGradient id="e202-fade" x1="0" y1="0" x2="0" y2="1920" gradientUnits="userSpaceOnUse">
        <stop offset={480/1920} stopColor="#fff" stopOpacity="0"/><stop offset={510/1920} stopColor="#fff" stopOpacity="1"/>
        <stop offset={1450/1920} stopColor="#fff" stopOpacity="1"/><stop offset={1500/1920} stopColor="#fff" stopOpacity="0"/></linearGradient>
        <mask id="e202-mask" maskUnits="userSpaceOnUse" x="0" y="0" width="1080" height="1920"><rect width="1080" height="1920" fill="url(#e202-fade)"/></mask>
        <filter id="e202-pop" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="6" stdDeviation="7" floodColor="#000" floodOpacity=".45"/></filter>
        <radialGradient id="e202-spot" cx="50%" cy="50%" r="50%"><stop offset="0" stopColor="#FFD21F" stopOpacity=".10"/><stop offset="1" stopColor="#FFD21F" stopOpacity="0"/></radialGradient></defs>
      {/* luz de palco quente no centro da área segura (identidade dourada do canal), não essencial */}
      <ellipse cx={(BOX_V2[0]+BOX_V2[2])/2} cy={(BOX_V2[1]+BOX_V2[3])/2+40} rx={520} ry={470} fill="url(#e202-spot)"/>
      <g mask="url(#e202-mask)">{drawn}</g></svg>
    {labels}
    <div style={{position:'absolute',left:160,top:300,fontWeight:900,fontSize:25,letterSpacing:.5}}>CORINGA <span style={{color:GOLD}}>EXPLICA</span></div>
    <div style={{position:'absolute',left:160,top:330,width:610,fontWeight:850,fontSize:30,lineHeight:1.05,whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>{data.headline||headline}</div>
    <div style={{position:'absolute',left:160,top:490,width:610,fontSize:16.5,lineHeight:1.12,color:'#AFC3D2',fontWeight:650,whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>
      {nat} · FONTE: {source}</div>
    {cap&&<div style={{position:'absolute',left:CAPTION_V2[0],top:CAPTION_V2[1],width:CAPTION_V2[2]-CAPTION_V2[0],height:CAPTION_V2[3]-CAPTION_V2[1],display:'flex',alignItems:'center',justifyContent:'center',textAlign:'center'}}>
      <div style={{fontSize:48,fontWeight:900,lineHeight:1.06,textShadow:'0 3px 0 #000, 0 0 18px rgba(0,0,0,.85)'}}>
        {cap.words.map((w,i)=><span key={i} style={{color:t>=w.s&&t<Math.max(w.e,w.s+.12)?GOLD:INK}}>{w.w}{i<cap.words.length-1?' ':''}</span>)}
      </div></div>}
    {data.credits.length>0&&<div style={{position:'absolute',left:160,top:1460,width:610,fontSize:15,lineHeight:1.12,color:'#8FA6B8',fontWeight:600,background:'rgba(8,18,30,.8)'}}>{data.credits.join(' · ')}</div>}
  </AbsoluteFill>;
};
export const SceneGraphE201:React.FC<{data:SceneData|SceneDataV2;t:number;duration:number;headline:string;source:string}>=({data,t,duration,headline,source})=>{
  if((data as SceneDataV2).schema==='coringa.scene_graph.private.v2')return <SceneGraphV2 data={data as SceneDataV2} t={t} duration={duration} headline={headline} source={source}/>;
  const d1=data as SceneData;
  validateScene(d1,duration);
  const beat=d1.beats.filter(b=>b.t<=t).slice(-1)[0]||d1.beats[0];
  return <AbsoluteFill style={{background:'radial-gradient(ellipse at 45% 50%,#203C50,#0B1927 65%,#07111C)',fontFamily:'Inter,Arial,sans-serif',color:'#F5F2EB'}}>
    <div style={{position:'absolute',left:160,top:310,width:600,fontWeight:850,fontSize:26}}>CORINGA <span style={{color:'#FFD21F'}}>EXPLICA</span></div>
    <div style={{position:'absolute',left:160,top:360,width:600,fontWeight:800,fontSize:43,lineHeight:1.1}}>{headline}</div>
    <svg viewBox="0 0 900 800" style={{position:'absolute',left:30,top:530,width:930,height:827,overflow:'hidden'}} aria-label="Esquema ilustrativo">
      <defs><radialGradient id="scene-glow"><stop stopColor="#74A9BF" stopOpacity=".13"/><stop offset="1" stopColor="#74A9BF" stopOpacity="0"/></radialGradient></defs>
      <ellipse cx="450" cy="400" rx="445" ry="380" fill="url(#scene-glow)"/>
      {d1.actors.map(a=>{const k=stateAt(a,t);return <g key={a.id} opacity={k.opacity} transform={'translate('+k.x+' '+k.y+') rotate('+k.angle+') scale('+k.scale+')'}>{a.shapes.map((s,i)=><path key={i} d={s.d} fill={s.fill} stroke={s.stroke||'none'} strokeWidth={s.sw||0} strokeLinecap="round" strokeLinejoin="round"/>)}</g>})}
    </svg>
    <div style={{position:'absolute',left:160,top:411,width:600,fontSize:29,fontWeight:800,lineHeight:1.08}}>{beat.text}</div>
    <div style={{position:'absolute',left:160,top:485,width:600,fontSize:19,color:'#C1D0DA',lineHeight:1.15}}>ESQUEMA SEM ESCALA · FONTE: {source}</div>
  </AbsoluteFill>;
};
