/** FILME EDITORIAL — compositor visual-first independente do ATLAS de cartões.
 * Stage 0: documentação real preenchendo a tela; câmera e revelações de cada assunto.
 * Não há palco-mapa persistente, slots pequenos, nem fluxo de cards como ação.
 * Todos os títulos vêm do roteiro; o compositor não inventa fatos.
 */
import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

export type Cue = {at: number; label: string; kind?: 'callout' | 'fact'; x?: number; y?: number};
export type FilmShot = {
  id: string;
  start: number;
  end: number;
  type: 'photo' | 'video' | 'comparison';
  asset: string; // caminho relativo a motor4/remotion/public, verificado pelo preflight Python
  assetB?: string;
  compareLabels?: [string, string]; // story-specific, never hard-code Taiwan into engine
  source: string;
  sourceB?: string;
  evidence: 'literal' | 'representative';
  subject: string;
  // O crop é uma escolha de DIREÇÃO: coordenadas normalizadas do objeto central.
  focus?: [number, number];
  focusB?: [number, number];
  lead: string;
  headline: string;
  highlight?: string;
  cues?: Cue[];
};
export type FilmProps = {
  duracao: number;
  shots: FilmShot[];
  label?: string;
  // Em prévia privada não há voz; o runtime pode acrescentar camada de narração
  // e legenda separadamente depois do plano aprovado.
  preview?: boolean;
};

const W = 1080, H = 1920;
const OFF_WHITE = '#F5F2EB', GOLD = '#FFD21F';
const clamp = (n: number, a=0, b=1) => Math.max(a, Math.min(b, n));
const ease = (v: number) => 1 - Math.pow(1 - clamp(v), 3);

const photograph = (asset: string, p: number, focus: [number,number], travel: number, side: 'full'|'left'|'right'='full') => {
  const zoom = 1.04 + ease(p)*0.13;
  // subject full-bleed, zoom subtly; the image NEVER becomes a 500px photo card.
  const cx = (focus[0] - 0.5) * 32 * ease(p);
  const cy = (focus[1] - 0.5) * 16 * ease(p);
  return <Img src={staticFile(asset)} style={{
    position:'absolute', left:0, top:0, width:'100%', height:'100%',
    objectFit:'cover', objectPosition:`${focus[0]*100}% ${focus[1]*100}%`,
    transform:`translate3d(${-cx}%,${-cy}%,0) scale(${zoom + travel}, ${zoom+travel})`,
    transformOrigin:`${focus[0]*100}% ${focus[1]*100}%`,
    filter:'brightness(.84) saturate(1.02) contrast(1.06)',
  }}/>;
};
const Body: React.FC<{shot: FilmShot;p:number}> = ({shot,p}) => {
  if(shot.type === 'video') {
    return <AbsoluteFill><OffthreadVideo src={staticFile(shot.asset)} muted
      startFrom={Math.max(0, Math.round((shot as any).source_in_seconds * 30) || 0)}
      style={{width:'100%',height:'100%',objectFit:'cover',
        objectPosition:`${(shot.focus||[.5,.5])[0]*100}% ${(shot.focus||[.5,.5])[1]*100}%`,
        filter:'brightness(.90) saturate(1.02)'}}/></AbsoluteFill>;
  }
  if(shot.type === 'comparison' && shot.assetB) {
    const right = clamp((p-.13)/.44);
    return <AbsoluteFill>
      <div style={{position:'absolute',inset:0,overflow:'hidden'}}>{photograph(shot.asset,p,shot.focus||[.5,.5],.02)}</div>
      <div style={{position:'absolute',inset:0,clipPath:`inset(0 ${(1-right)*100}% 0 0)`}}>
        {photograph(shot.assetB,p,shot.focusB||[.5,.5],0)}
      </div>
      {right>.04 && <div style={{position:'absolute',left:`${right*100}%`,top:0,bottom:0,width:4,background:GOLD,boxShadow:`0 0 22px ${GOLD}`}}/>}
      <div style={{position:'absolute',top:470,left:42,background:'rgba(5,14,24,.85)',padding:'9px 18px',fontWeight:900,fontSize:31,letterSpacing:1.2,color:OFF_WHITE}}>{shot.compareLabels?.[0] || 'ANTES'}</div>
      {right>.6 && <div style={{position:'absolute',top:470,right:42,background:'rgba(5,14,24,.85)',padding:'9px 18px',fontWeight:900,fontSize:31,letterSpacing:1.2,color:GOLD}}>{shot.compareLabels?.[1] || 'DEPOIS'}</div>}
    </AbsoluteFill>;
  }
  return <AbsoluteFill>{photograph(shot.asset,p,shot.focus||[.5,.5],.01)}</AbsoluteFill>;
};
const Caption: React.FC<{text:string; highlighted?:string}> = ({text,highlighted}) => {
  const parts = highlighted ? text.split(highlighted) : [text];
  return <div style={{fontFamily:'Inter, Arial, sans-serif',fontSize:63,lineHeight:1.09,fontWeight:900,textTransform:'uppercase',letterSpacing:-1.5,whiteSpace:'pre-line'}}>
    {parts.map((part,i)=><React.Fragment key={i}>{part}{highlighted && i<parts.length-1 && <span style={{color:GOLD}}>{highlighted}</span>}</React.Fragment>)}
  </div>;
};
const FilmShotView: React.FC<{shot:FilmShot;total:number;index:number}> = ({shot,total,index}) => {
  const frame=useCurrentFrame(),fps=useVideoConfig().fps;
  const now=frame/fps;
  const duration=Math.max(.01, shot.end-shot.start);
  const p=clamp((now-shot.start)/duration);
  const fadeIn=clamp((now-shot.start)/.16),fadeOut=clamp((shot.end-now)/.14);
  const cue=shot.cues?.filter(c=>now >= shot.start+c.at).slice(-1)[0];
  const cueAge=cue?now-shot.start-cue.at:0;
  return <AbsoluteFill style={{opacity:Math.min(fadeIn,fadeOut),background:'#08101A',overflow:'hidden'}}>
    <Body shot={shot} p={p}/>
    {/* strong editorial gradient is NOT a black rectangle over the subject */}
    <AbsoluteFill style={{pointerEvents:'none',background:'linear-gradient(180deg,rgba(3,8,16,.55) 0%,rgba(3,8,16,.08) 21%,rgba(3,8,16,.03) 48%,rgba(3,8,16,.58) 72%,#050A12 100%)'}}/>
    <div style={{position:'absolute',top:248,left:62,right:62,display:'flex',justifyContent:'space-between',alignItems:'center',color:OFF_WHITE,fontFamily:'Inter,Arial',fontSize:28,fontWeight:800,letterSpacing:2.1}}>
      <span>CORINGA <span style={{color:GOLD}}>EXPLICA</span></span>
      <span style={{fontSize:24,fontWeight:600,color:'#C2CCD5'}}>{shot.lead.toUpperCase()}</span>
    </div>
    <div style={{position:'absolute',top:302,left:62,width:140,height:5,background:GOLD,transform:`scaleX(${ease(p)})`,transformOrigin:'left'}}/>
    {cue && <div style={{
      position:'absolute',top:380+((cue.y||.38)-.38)*700,left:64+((cue.x||.5)-.5)*150,maxWidth:W-128,
      transform:`translateY(${(1-ease(cueAge/.25))*22}px)`,
      opacity:ease(cueAge/.25),fontFamily:'Inter,Arial',fontWeight:900,fontSize:37,
      padding:'13px 17px',borderLeft:`6px solid ${GOLD}`,
      background:'rgba(6,12,22,.78)',color:OFF_WHITE,letterSpacing:.5,
    }}>{cue.label}</div>}
    <div style={{position:'absolute',left:60,right:60,top:1275,
      opacity:ease((now-shot.start-.12)/.32),transform:`translateY(${(1-ease((now-shot.start-.12)/.32))*36}px)`,
      color:OFF_WHITE,textShadow:'0 3px 18px rgba(0,0,0,.65)'}}>
      <Caption text={shot.headline} highlighted={shot.highlight}/>
    </div>
    <div style={{position:'absolute',bottom:288,left:64,right:64,fontFamily:'Inter,Arial',fontSize:26,color:'#CFD6E0',fontWeight:600}}>
      {shot.evidence==='representative'?'IMAGEM ILUSTRATIVA · ':''}{shot.subject}
    </div>
    <div style={{position:'absolute',bottom:240,left:64,right:64,fontFamily:'Inter,Arial',fontSize:21,color:'#ACBBC7',letterSpacing:.6}}>
      FONTE: {shot.source}
    </div>
    <div style={{position:'absolute',bottom:198,left:64,right:64,height:3,background:'rgba(255,255,255,.25)'}}>
      <div style={{width:`${100*p}%`,height:'100%',background:GOLD}}/>
    </div>
  </AbsoluteFill>;
};
export const FilmeEditorial: React.FC<FilmProps> = ({shots,duracao,preview=true}) => {
  const frame=useCurrentFrame(),fps=useVideoConfig().fps,t=frame/fps;
  const shot=shots.findIndex(s=>t>=s.start&&t<s.end);
  return <AbsoluteFill style={{background:'#050A12'}}>
    {shot>=0&&<FilmShotView shot={shots[shot]} total={duracao} index={shot}/>}
    {preview&&<div style={{position:'absolute',bottom:40,left:0,right:0,textAlign:'center',
      fontFamily:'Inter,Arial',color:'#CFD6E0',opacity:.7,fontSize:20,letterSpacing:1.1}}>
      AMOSTRA VISUAL — SEM NARRAÇÃO · NÃO PUBLICADO
    </div>}
  </AbsoluteFill>;
};
