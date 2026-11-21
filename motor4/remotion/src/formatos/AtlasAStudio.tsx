/** Direção ilustrativa A: acabamento autoral 2.5D, ambiente do fenômeno
 * e tipografia editorial grande. Shell compartilhado entre eclusa e EUV.
 * Cenas e tempo vêm de contrato; não é exportação nem publicação.
 */
import React from 'react';
import {AbsoluteFill} from 'remotion';

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
  <path d="M0 622 H1080" stroke="#6C7BB9" strokeWidth="12" opacity=".18"/>
  <rect x="0" y="493" width="127" height="1184" fill="#27305F" opacity=".45"/>
  <rect x="953" y="493" width="127" height="1184" fill="#283260" opacity=".47"/>
  {[78,995].map((x,i)=><g key={i} opacity=".42">
    <rect x={x-24} y="580" width="32" height="975" rx="11"
      fill="#7188B5"/>
    <path d={'M'+(x-24)+' 637 h32 M'+(x-24)+' 1099 h32'}
      stroke="#A6ACCB" strokeWidth="9"/>
  </g>)}
  <circle cx="526" cy="871" r="530" fill="#8B58DC" opacity=".10"/>
  <ellipse cx="545" cy="1380" rx="470" ry="155" fill="#4A3198" opacity=".22"/>
  <rect x="0" y="1220" width="1080" height="700" fill="url(#a-euv-floor)"/>
  {Array.from({length:7},(_,i)=><g key={i} opacity=".19">
    <path d={'M'+(-180+i*200)+' 1280 L'+(-310+i*330)+' 1920'}
      fill="none" stroke="#8B83D6" strokeWidth="11"/>
    <path d={'M0 '+(1320+i*85)+' H1080'}
      stroke="#7770B9" strokeWidth="7"/>
  </g>)}
  {/* walls/cables belong to factory environment, no fake optical rays */}
  <path d="M115 550 V1130 Q120 1172 169 1170 H225"
    fill="none" stroke="#54699D" strokeWidth="24" opacity=".4"/>
  <path d="M965 555 V1110 Q949 1133 930 1148"
    fill="none" stroke="#7E6EAC" strokeWidth="17" opacity=".35"/>
</g>;

export const AtlasAStudio:React.FC<Props>=({
  kind,title,section,label,step,total,source,t,children,
  privateReviewOnly=true
})=>{
  const euv=kind==='euv';
  const GOLD=COLORS.yellow;
  return <AbsoluteFill style={{fontFamily:'Inter,Arial,sans-serif',
    overflow:'hidden',background:euv?'#110C31':'#12679A'}}>
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
          <stop stopColor="#110C37"/><stop offset=".48" stopColor="#2B1A6B"/>
          <stop offset=".8" stopColor="#10133A"/>
          <stop offset="1" stopColor="#0C1135"/>
        </linearGradient>
        <linearGradient id="a-euv-floor" x1="0" x2=".4" y1="0" y2="1">
          <stop stopColor="#3A286E"/><stop offset="1" stopColor="#100D32"/>
        </linearGradient>
        <linearGradient id="a-euv-steel" x1="0" x2="1" y1="0" y2="1">
          <stop stopColor="#B5C8EC"/><stop offset=".25" stopColor="#6679B7"/>
          <stop offset=".55" stopColor="#3E408B"/><stop offset="1" stopColor="#181C53"/>
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
    <div style={{position:'absolute',top:1090,left:146,width:604,
      borderRadius:9,padding:'11px 16px 14px',
      background:euv?'rgba(8,10,42,.90)':'rgba(2,30,53,.87)',
      boxShadow:'0 5px 21px rgba(3,15,28,.22)',
      borderLeft:'8px solid '+GOLD}}>
      <div style={{fontSize:19,letterSpacing:1.5,fontWeight:900,
        color:GOLD,marginBottom:6}}>
        {String(step).padStart(2,'0')} / {String(total).padStart(2,'0')}
      </div>
      <div style={{fontSize:label.length>40?27:32,lineHeight:1.09,
        fontWeight:950,color:'#FFFFFF'}}>
        {label}
      </div>
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
