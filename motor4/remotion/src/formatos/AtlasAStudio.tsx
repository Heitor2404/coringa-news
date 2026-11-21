/** Direção ilustrativa A: acabamento autoral 2.5D, ambiente do fenômeno
 * e tipografia editorial grande. Shell compartilhado entre eclusa e EUV.
 * Cenas e tempo vêm de contrato; não é exportação nem publicação.
 */
import React from 'react';
import {AbsoluteFill} from 'remotion';
import cfg from './atlas-a-proof.json';
import {ABeveledPanel,ARivet} from './AtlasAArtKit';

export const COLORS={
  navy:'#062B48',deep:'#061C34',ink:'#071C2B',
  cyan:'#27C9EB',yellow:'#FFD21F',white:'#F9FBFD',
  steel:'#B8CED7',water:'#1274A8',orange:'#FF8427'
};
type Props={
 kind:'lock'|'euv';title:[string,string];section:string;
 label:string;step:number;total:number;source:string;
 children:React.ReactNode;privateReviewOnly?:boolean;t:number
};
const sunCloud=(x:number,y:number,s:number,i:number)=><g key={i}
  transform={'translate('+x+' '+y+') scale('+s+')'} opacity=".83">
  <ellipse cx="110" cy="57" rx="122" ry="28" fill="#D5F1FF"/>
  <circle cx="58" cy="45" r="41" fill="#F5FBFF"/>
  <circle cx="109" cy="24" r="55" fill="#F5FBFF"/>
  <circle cx="171" cy="51" r="38" fill="#DDF3FF"/>
</g>;

const SkyBackdrop:React.FC<{t:number}>=({t})=><g>
  <rect width="1080" height="1920" fill="url(#a-lock-sky)"/>
  <circle cx="853" cy="302" r="208" fill="#C2ECFF" opacity=".22"/>
  <path d="M0 706 Q160 619 323 705 T652 668 T1080 641 V1030 H0Z"
    fill="#5FBB86" opacity=".93"/>
  <path d="M0 745 Q183 676 316 744 T668 725 T1080 671 V1087 H0Z"
    fill="#287B69"/>
  <path d="M0 807 Q203 743 380 782 T720 760 T1080 742 V1120 H0Z"
    fill="#194F69"/>
  {sunCloud(10,520,0.7,0)}
  {sunCloud(630,515,0.52,1)}
  {/* lower continuation is environment, not critical mechanism. */}
  <rect x="0" y="1098" width="1080" height="822" fill="url(#a-lock-deepwater)"/>
  {Array.from({length:14},(_,i)=><path key={i}
    d={'M'+(-140+i*95)+' '+(1300+i%5*92)+
      ' q90 '+(-14+Math.sin(t*1.6+i)*6)+' 185 0'}
    fill="none" stroke="#73DFF0" strokeWidth={i%3===0?6:3}
    opacity=".12"/>)}
  <path d="M0 1588 Q240 1548 465 1578 T1080 1543" fill="none"
    stroke="#58D5ED" strokeWidth="16" opacity=".10"/>
  {/* near shore far below critical band */}
  <path d="M0 1795 Q190 1750 350 1810 T720 1800 T1080 1780 V1920 H0Z"
    fill="#083B59" opacity=".53"/>
</g>;

const IndustrialBackdrop:React.FC<{t:number}>=({t})=><g>
  <rect width="1080" height="1920" fill="url(#a-euv-backdrop)"/>
  {/* Cor, contraste e volume seguem a família editorial A da eclusa.
      Ambiente industrial próprio, não o antigo quadro técnico roxo. */}
  <circle cx="819" cy="368" r="247" fill="#F7CE7D" opacity=".21"/>
  <path d="M0 688 Q204 539 445 649 T1080 580 V1008 H0Z"
    fill="#0B5B88" opacity=".56"/>
  <path d="M0 1082 L184 997 H905 L1080 1082 V1920 H0Z"
    fill="#153B64"/>
  <path d="M0 1198 L190 1155 H890 L1080 1198 V1920 H0Z"
    fill="#0B3458"/>
  {[-40,960].map((x,i)=><g key={i}>
    <ABeveledPanel x={x} y={528} width={158} height={1190}
      tone="cobalt" rx={22}/>
    {Array.from({length:7},(_,j)=><ARivet key={j}
      x={x+77} y={670+j*142} r={9}/>)}
  </g>)}
  {/* Máquina física e etapa do wafer no mesmo plano de profundidade. */}
  <ABeveledPanel x={112} y={1241} width={858} height={488}
    tone="steel" rx={29}/>
  <ABeveledPanel x={188} y={1335} width={709} height={280}
    tone="cobalt" rx={25}/>
  <path d="M225 1432 H853" stroke="#85EDDD" strokeWidth="10"
    opacity=".78"/>
  <path d="M225 1534 H853" stroke="#F1BD72" strokeWidth="9"
    opacity=".74"/>
  {Array.from({length:6},(_,i)=><g key={i}>
    <ARivet x={257+i*111} y={1388} r={14}/>
    <path d={`M${257+i*111} 1475 v37`}
      stroke="#8CE5E6" strokeWidth="10" opacity=".35"/>
  </g>)}
  <ABeveledPanel x={147} y={1727} width={778} height={64}
    tone="sand" rx={9}/>
  <path d="M110 1814 Q550 1763 967 1814" stroke="#3EA9C0"
    strokeWidth="17" fill="none" opacity=".37"/>
  <path d="M160 1170 H921" stroke="#FED68B" strokeWidth="8"
    opacity=".4"/>
</g>;

export const AtlasAStudio:React.FC<Props>=({
  kind,title,section,label,step,total,source,t,children,
  privateReviewOnly=true
})=>{
  const euv=kind==='euv';
  const GOLD=COLORS.yellow;
  return <AbsoluteFill style={{fontFamily:'Inter,Arial,sans-serif',
    overflow:'hidden',background:euv?'#0B436F':'#12679A'}}>
    <svg viewBox="0 0 1080 1920" width="100%" height="100%"
      role="img" aria-label={'Prévia editorial ilustrada do mecanismo: '+kind}>
      <defs>
        <linearGradient id="a-lock-sky" x1="0" x2=".1" y1="0" y2="1">
          <stop stopColor="#115FBC"/>
          <stop offset=".47" stopColor="#16A8F0"/>
          <stop offset=".82" stopColor="#8CD9FB"/>
          <stop offset="1" stopColor="#C4F3FF"/>
        </linearGradient>
        <linearGradient id="a-lock-deepwater" x1="0" x2=".4" y1="0" y2="1">
          <stop stopColor="#178CBB"/><stop offset=".4" stopColor="#065477"/>
          <stop offset="1" stopColor="#032B46"/>
        </linearGradient>
        <linearGradient id="a-lock-water" x1="0" x2="0" y1="0" y2="1">
          <stop stopColor="#8AF7F5"/><stop offset=".10" stopColor="#24BCE9"/>
          <stop offset=".68" stopColor="#1079B3"/>
          <stop offset="1" stopColor="#084C83"/>
        </linearGradient>
        <linearGradient id="a-concrete" x1="0" x2="1" y1="0" y2="0">
          <stop stopColor="#5C7585"/><stop offset=".3" stopColor="#D3C9B5"/>
          <stop offset=".7" stopColor="#8CA6AD"/><stop offset="1" stopColor="#37566B"/>
        </linearGradient>
        <linearGradient id="a-ship" x1="0" x2="1" y1="0" y2="1">
          <stop stopColor="#15466B"/><stop offset=".60" stopColor="#062F53"/>
          <stop offset="1" stopColor="#051B35"/>
        </linearGradient>
        <linearGradient id="a-euv-backdrop" x1="0" x2=".4" y1="0" y2="1">
          <stop stopColor="#10658E"/><stop offset=".48" stopColor="#227EAF"/>
          <stop offset=".8" stopColor="#17436B"/>
          <stop offset="1" stopColor="#082947"/>
        </linearGradient>
        <linearGradient id="a-euv-floor" x1="0" x2=".4" y1="0" y2="1">
          <stop stopColor="#3A286E"/><stop offset="1" stopColor="#100D32"/>
        </linearGradient>
        <linearGradient id="a-euv-steel" x1="0" x2="1" y1="0" y2="1">
          <stop stopColor="#E5F7E7"/><stop offset=".25" stopColor="#80B3CE"/>
          <stop offset=".55" stopColor="#2D749B"/><stop offset="1" stopColor="#173C70"/>
        </linearGradient>
        <linearGradient id="a-euv-wafer" x1="0" x2="1" y1="0" y2="1">
          <stop stopColor="#5A40D8"/><stop offset=".46" stopColor="#252976"/>
          <stop offset="1" stopColor="#13143F"/>
        </linearGradient>
        <radialGradient id="a-euv-glow">
          <stop stopColor="#B96FFF" stopOpacity=".54"/>
          <stop offset=".35" stopColor="#885CFF" stopOpacity=".26"/>
          <stop offset="1" stopColor="#885CFF" stopOpacity="0"/>
        </radialGradient>
      </defs>
      {euv?<IndustrialBackdrop t={t}/>:<SkyBackdrop t={t}/>}
      {children}
    </svg>

    {/* Branding e textos essenciais sempre entre y300 e y1240.
        O ambiente, mesmo na faixa UI inferior, continua FULL-BLEED. */}
    <div style={{position:'absolute',top:295,left:145,
      display:'inline-flex',alignItems:'center',gap:9,
      fontSize:23,fontWeight:950,letterSpacing:.25,
      background:'rgba(4,22,45,.88)',borderRadius:8,
      padding:'7px 12px',color:'#fff'}}>
      CORINGA <span style={{background:GOLD,color:COLORS.ink,
        padding:'3px 7px',borderRadius:4}}>EXPLICA</span>
    </div>
    <div style={{position:'absolute',top:353,left:151,width:610,
      fontSize:20,fontWeight:850,letterSpacing:1.7,
      color:euv?'#E2D8FF':'#FFFFFF',
      textShadow:'0 2px 7px rgba(0,12,28,.72)'}}>
      {section}
    </div>
    <div style={{position:'absolute',top:386,left:145,width:770,
      fontSize:53,lineHeight:1.01,letterSpacing:-1.5,
      fontWeight:950,color:'#fff',textShadow:'0 3px 12px rgba(0,18,40,.96)'}}>
      <div>{title[0]}</div><div>{title[1]}</div>
    </div>
    {/* Um cue compacto entre título e máquina: não tapa o fenômeno. */}
    <div style={{position:'absolute',top:cfg.visual_layout.cue[1],
      left:cfg.visual_layout.cue[0],width:cfg.visual_layout.cue[2],
      minHeight:cfg.visual_layout.cue[3],
      display:'flex',alignItems:'center',gap:12,
      borderRadius:9,padding:'5px 12px',
      background:euv?'rgba(6,42,70,.93)':'rgba(2,44,73,.88)',
      borderLeft:'7px solid '+GOLD,
      boxShadow:'0 4px 12px rgba(4,20,35,.24)'}}>
      <span style={{fontSize:16,fontWeight:900,color:GOLD,
        whiteSpace:'nowrap'}}>{String(step).padStart(2,'0')}</span>
      <span style={{fontSize:label.length>34?23:26,
        lineHeight:1.07,fontWeight:950,color:'#FFFFFF'}}>
        {label}
      </span>
    </div>
    <div style={{position:'absolute',top:1210,left:148,width:600,
      fontSize:17.5,fontWeight:700,
      textShadow:'0 2px 7px rgba(0,9,22,.75)',
      color:'#FFFFFF'}}>
      {source}
    </div>
    {privateReviewOnly&&<div style={{position:'absolute',bottom:49,left:0,
      right:0,textAlign:'center',fontSize:19,fontWeight:800,
      letterSpacing:1.35,color:'rgba(255,255,255,.75)',
      textShadow:'0 2px 5px rgba(0,4,20,.85)'}}>
      PRÉVIA PRIVADA · NÃO PUBLICAR
    </div>}
  </AbsoluteFill>;
};
