/** Eclusa causal: domínio hidráulico isolado, cronologia fornecida pelo storyboard.
 * Nunca representa registro real; desenha a relação água -> nível -> navio -> equalização.
 * O enquadramento e as etapas não dependem de segundos fixos do episódio.
 */
import React from 'react';
import {AbsoluteFill,Img,staticFile} from 'remotion';

export type EventoEclusa = {
  at: number;
  action?: 'closed' | 'water_enter' | 'rise' | 'equalize' | 'release';
  label: string;
};
type Props = { t: number; events: EventoEclusa[]; referenceAsset?: string; visualMode?: 'legacy'|'editorial' };
const GOLD='#FFD21F';
const ease=(v:number)=>{const x=Math.max(0,Math.min(1,v));return x*x*(3-2*x);};


/** Camada visual editorial. Usa as mesmas variáveis hidráulicas calculadas pelo
 * LockCausal, sem refazer lógica nem interferir nas versões publicadas/legadas.
 */
const EditorialCutaway:React.FC<{
  t:number;fill:number;open:number;isFlow:boolean;active?:EventoEclusa
}>=({t,fill,open,isFlow,active})=>{
  const waterY=1256-282*fill;
  const wave=Math.sin(t*4)*2.5;
  const level=waterY+wave;
  const step=active?.action||'closed';
  const actions=['closed','water_enter','rise','equalize','release'];
  const index=Math.max(0,actions.indexOf(step));
  const hullY=level-106;
  const GOLD='#FFD21F',WHITE='#F5F2EB',CYAN='#6DE1E9',MUTED='#AAC0CE';
  return <AbsoluteFill style={{
    background:'radial-gradient(ellipse at 54% 46%,#1C394C,#081725 61%,#05111D 100%)',
    fontFamily:'Inter,Arial,sans-serif',overflow:'hidden'}}>
    <svg width="100%" height="100%" viewBox="0 0 1080 1920"
      role="img" aria-label="Corte ilustrativo de eclusa: a água entra por conduto, eleva o nível e o navio, até igualar o nível externo">
      <defs>
        <pattern id="lock-edit-grid" width="70" height="70" patternUnits="userSpaceOnUse">
          <path d="M70 0H0V70" fill="none" stroke="#6694A9" strokeOpacity=".12" strokeWidth="1.2"/>
        </pattern>
        <linearGradient id="lock-edit-water" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="#82E4EF"/><stop offset=".19" stopColor="#48B7D2"/>
          <stop offset=".6" stopColor="#227291"/><stop offset="1" stopColor="#0D3F5E"/>
        </linearGradient>
        <linearGradient id="lock-edit-metal" x1="0" y1="0" x2="1" y2="0">
          <stop stopColor="#284255"/><stop offset=".32" stopColor="#A3C7CF"/>
          <stop offset=".66" stopColor="#5C7F8F"/><stop offset="1" stopColor="#20394B"/>
        </linearGradient>
        <linearGradient id="lock-edit-hull" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="#FFFFFF"/><stop offset=".46" stopColor="#CBD9DB"/>
          <stop offset="1" stopColor="#668795"/>
        </linearGradient>
        <clipPath id="lock-edit-chamber"><rect x="141" y="686" width="635" height="714"/></clipPath>
      </defs>
      <rect width="1080" height="1920" fill="url(#lock-edit-grid)"/>
      <circle cx="517" cy="1070" r="420" fill="#215F77" opacity=".09"/>
      <text x="71" y="427" fill={MUTED} fontSize="29" fontWeight="850" letterSpacing="3">ENGENHARIA EXPLICADA</text>
      <text x="71" y="506" fill={WHITE} fontSize="60" fontWeight="900">COMO A ÁGUA LEVANTA</text>
      <text x="71" y="567" fill={WHITE} fontSize="60" fontWeight="900">UM NAVIO INTEIRO?</text>
      <path d="M68 597 H1014" stroke="#48697C" strokeWidth="2" opacity=".7"/>
      <text x="112" y="705" fill={MUTED} fontSize="26" fontWeight="800" letterSpacing="2">CÂMARA DA ECLUSA</text>
      <text x="815" y="841" fill={CYAN} fontSize="26" fontWeight="850">NÍVEL ALTO</text>

      {/* Profundidade do concreto e nível do reservatório externo. */}
      <path d="M72 752 H141 V1404 H775 V933 H1018 V1432 H72Z"
        fill="#162B3C" stroke="#567486" strokeWidth="3"/>
      <rect x="145" y="752" width="628" height="645" fill="#061B2D"/>
      <rect x="801" y="966" width="214" height="431" fill="url(#lock-edit-water)" opacity=".85"/>
      <path d="M801 966 H1015" stroke="#B4FCFC" strokeWidth="7"/>
      <g clipPath="url(#lock-edit-chamber)">
        <rect x="141" y={level} width="635" height={1400-level} fill="url(#lock-edit-water)"/>
        <path d={'M141 '+level+' H777'} stroke="#D3FBF8" strokeWidth="7"/>
        {Array.from({length:10},(_,i)=><g key={i}>
          <path d={'M'+(155+i*68)+' '+(level+23+Math.sin(t*5+i)*3)+' h38'}
            stroke="#A4FFFF" strokeWidth="4" opacity=".27"/>
          <path d={'M'+(165+i*61)+' '+(level+74+i%3*31)+' h19'}
            stroke="#D8FCFA" strokeWidth="2" opacity=".10"/>
        </g>)}
      </g>
      {/* Conexão hidráulica real pelo fundo, NÃO entrada pelo portão. */}
      <path d="M978 1362 H750 V1326 H643" stroke="#203B4D" strokeWidth="41" fill="none"/>
      <path d="M978 1362 H750 V1326 H643" stroke="#547F91" strokeWidth="27" fill="none"/>
      <path d="M978 1362 H750 V1326 H643" stroke={isFlow?CYAN:'#60798A'}
        strokeWidth="13" fill="none" strokeDasharray="17 27"
        strokeDashoffset={-t*85} opacity={isFlow?.96:.33}/>
      <path d="M651 1326 l32 -18 v36 Z" fill={isFlow?GOLD:'#60798A'}/>
      <path d="M78 1397 H1017" stroke="#728B9A" strokeWidth="21"/>
      <rect x="110" y="739" width="34" height="680" fill="url(#lock-edit-metal)"/>
      <rect x="774" y="740" width="35" height="679" fill="url(#lock-edit-metal)"
        opacity={1-open*.79}/>
      <path d="M791 951 V1398" stroke={open>0.15?GOLD:'#738E9F'} strokeWidth="5"
        strokeDasharray="13 12" opacity={.35+.65*open}/>
      <text x="832" y="1462" fill={isFlow?GOLD:MUTED} fontWeight="800" fontSize="27">DUTO INFERIOR</text>

      {/* Casco com volume e detalhes: acompanha a superfície em todo instante. */}
      <g transform={'translate(0,'+(hullY-1025)+')'}>
        <path d="M225 1015 L699 1015 658 1105 278 1105Z"
          fill="#071723" opacity=".30" transform="translate(0 14)"/>
        <path d="M215 1000 H714 L667 1092 H275Z"
          fill="url(#lock-edit-hull)" stroke="#F9FCFD" strokeWidth="6"/>
        <path d="M257 1072 H665" stroke="#6D929F" strokeWidth="8"/>
        <path d="M343 948 H602 V1001 H343Z" fill="#F4F8F6" stroke="#90B2BB" strokeWidth="4"/>
        <rect x="380" y="910" width="181" height="35" rx="4" fill="#E9F2F0"/>
        <rect x="463" y="869" width="13" height="42" fill="#B7D5D8"/>
        {Array.from({length:5},(_,i)=><rect key={i} x={361+i*46} y="966" width="31" height="19"
          rx="3" fill="#2A5873"/>)}
        <path d="M235 1020 H700" stroke={WHITE} strokeWidth="2" opacity=".6"/>
      </g>

      {/* Régua de referência e seta diretamente ligada ao deslocamento. */}
      <path d="M182 1256 V974" stroke={GOLD} strokeWidth="6"
        strokeDasharray="13 12" opacity={fill>.01?1:.16}/>
      <path d={'M182 '+(level+12)+' l-18 30 h36Z'} fill={GOLD} opacity={fill>.01?1:.18}/>
      <path d="M190 1256 H241 M190 974 H241" stroke="#BAD7E2" strokeWidth="4" opacity=".55"/>
      <text x="223" y="1300" fill={MUTED} fontSize="24">NÍVEL INICIAL</text>
      <path d="M801 968 H1005" stroke="#B5FFFA" strokeWidth="3"/>
      <path d="M76 1501 H1007" stroke="#4B6D7C" strokeWidth="2"/>

      <text x="70" y="1573" fill={GOLD} fontSize="33" fontWeight="900">
        {String(index+1).padStart(2,'0')+'  /  '+(active?.label||'CÂMARA FECHADA').replace(/^[0-9]+\s*·\s*/,'')}
      </text>
      <g transform="translate(74 1607)">
        {actions.map((a,i)=><rect key={a} x={i*193} width="176" height="7"
          fill={index>=i?GOLD:'#335668'} opacity={index>=i?1:.6}/>)}
      </g>
    </svg>
  </AbsoluteFill>;
};

export const LockCausal: React.FC<Props> = ({t,events,referenceAsset,visualMode='legacy'}) => {
  const at=(action:NonNullable<EventoEclusa['action']>,fallback:number)=>
    events.find(e=>e.action===action)?.at ?? fallback;
  const inlet=at('water_enter',1),
        equilibrium=at('equalize',3.6),release=at('release',4.7);
  const fill=ease((t-inlet)/Math.max(.5,equilibrium-inlet));
  const open=ease((t-release)/.55);
  const y=1095-254*fill;
  const pulse=.5+.5*Math.sin(Math.max(0,t-inlet)*9);
  const active=events.filter(e=>e.at<=t).slice(-1)[0];
  const state=active?.action || 'closed';
  const isFlow=t>=inlet && t<equilibrium;
  const yHull=y-53;
  const rulerY=[1095,1031,968,904,841];
  if(visualMode==='editorial') return <EditorialCutaway t={t} fill={fill} open={open} isFlow={isFlow} active={active}/>;
  return <AbsoluteFill style={{background:'#091625'}}>
    {referenceAsset && t < .85 && <Img src={staticFile(referenceAsset)}
      style={{position:'absolute',width:'100%',height:'100%',objectFit:'cover',
        objectPosition:'50% 48%',transform:'scale(1.1)',transformOrigin:'50% 30%',
        filter:'brightness(.98) saturate(1.04)'}}/>}
    {referenceAsset && t < .85 && <AbsoluteFill style={{opacity:1-ease(t/.85),pointerEvents:'none',
      background:'linear-gradient(180deg,rgba(3,8,16,.55) 0%,rgba(3,8,16,.08) 21%,rgba(3,8,16,.03) 48%,rgba(3,8,16,.58) 72%,#050A12 100%)'}}/>}
    <AbsoluteFill style={{opacity:referenceAsset ? ease(t/.85) : 1,
      background:'radial-gradient(ellipse at 50% 47%,#1A3344 0%,#091625 69%,#050B15 100%)'}}>
    <svg width="100%" height="100%" viewBox="0 0 1080 1920" role="img"
      aria-label="Corte didático: água entra pelo canal inferior, eleva o nível e o navio; após a equalização o portão pode abrir">
      <defs>
        <linearGradient id="waterNew" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="#69D9EA" offset="0%"/><stop stopColor="#247C9F" offset="48%"/>
          <stop stopColor="#134560" offset="100%"/>
        </linearGradient>
        <linearGradient id="concreteNew" x1="0" y1="0" x2="1" y2="0">
          <stop stopColor="#344D5E" offset="0%"/><stop stopColor="#A6BAC1" offset="45%"/>
          <stop stopColor="#243A49" offset="100%"/>
        </linearGradient>
        <pattern id="dotsNew" width="44" height="44" patternUnits="userSpaceOnUse">
          <path d="M44 0H0V44" stroke="#527284" strokeOpacity=".14" fill="none" strokeWidth="1.2"/>
        </pattern>
        <clipPath id="chamberNew"><rect x="142" y="748" width="667" height="510"/></clipPath>
      </defs>
      <rect width="1080" height="1920" fill="url(#dotsNew)"/>
      <text x="83" y="440" fill="#BDCAD1" fontSize="30" letterSpacing="3.2" fontWeight="700">CORTE TRANSVERSAL · ILUSTRAÇÃO</text>
      <text x="83" y="506" fill="#F5F2EB" fontSize="49" fontWeight="800">A ECLUSA POR DENTRO</text>
      <rect x="82" y="535" height="4" width="914" fill="#476477"/>

      {/* Terreno acima e abaixo da água, seção da câmara e do reservatório superior. */}
      <path d="M110 752 V1300 H1010 V752" fill="#142637" stroke="#536B7C" strokeWidth="3"/>
      <rect x="143" y="748" width="666" height="510" fill="#061422"/>
      <rect x="819" y="841" width="173" height="417" fill="url(#waterNew)" opacity=".77"/>
      <g clipPath="url(#chamberNew)">
        <rect x="142" y={y} width="667" height={1258-y} fill="url(#waterNew)" opacity=".93"/>
        {Array.from({length:7},(_,i)=><path key={i} d={'M'+(149+i*107)+' '+(y+17+Math.sin(t*7+i)*2)+' h68'}
          stroke="#B0F6F5" strokeWidth="3.4" opacity=".42"/>)}
        <path d={'M142 '+y+' H809'} stroke="#B7FBFA" strokeWidth="5" opacity=".9"/>
      </g>
      <rect x="106" y="718" width="37" height="560" fill="url(#concreteNew)"/>
      <rect x="804" y="718" width="34" height="560" fill="url(#concreteNew)"/>
      <path d="M108 1257 H1010" stroke="#7E9BAD" strokeWidth="24"/>

      {/* Galeria hidráulica — entra água pela parte inferior, não pelos portões. */}
      <path d="M970 1224 H771 V1183 H655" fill="none" stroke="#4E6D81" strokeWidth="39" strokeLinecap="square"/>
      <path d="M970 1224 H771 V1183 H655" fill="none" stroke="#61D6E8" strokeWidth="13" strokeDasharray="23 28" strokeDashoffset={-t*66}
        opacity={isFlow ? .65+.28*pulse : .23}/>
      <path d="M662 1183 l24 -15 v30 Z" fill={isFlow?GOLD:'#53758A'}/>
      <text x="668" y="1335" fill={isFlow?GOLD:'#A0B1BD'} fontSize="28" fontWeight="700">DUTO DE ENCHIMENTO</text>
      <path d="M774 1207 H964" fill="none" stroke={isFlow?GOLD:'#617D90'} strokeWidth={isFlow?4:2} strokeDasharray="11 12"/>

      {/* Portão no lado do nível superior: só fica 'liberado' após igualar a água. */}
      <rect x="802" y="756" width="18" height="458" fill="#9CAFB9" opacity={1-.83*open}/>
      <path d="M815 758 V1213" stroke={open?GOLD:'#7C929F'} strokeWidth="4" strokeDasharray={open?'13 11':'0'}/>
      <g transform={'translate(0,'+(yHull-101)+')'}>
        <path d="M249 78 H666 L624 145 H290 Z" fill="#DDE5E8" stroke="#F4F5F1" strokeWidth="5"/>
        <path d="M274 141 H638" stroke="#8A9FAE" strokeWidth="10"/>
        <rect x="373" y="22" width="191" height="53" rx="3" fill="#F4F2E9" stroke="#9BAEB6" strokeWidth="3"/>
        <rect x="410" y="-7" width="120" height="27" fill="#E8F0F0"/>
        <rect x="466" y="-48" width="12" height="42" fill="#A5CBD2"/>
        {Array.from({length:5},(_,i)=><rect key={i} x={393+32*i} y="40" width="20" height="14" fill="#254456"/>)}
      </g>
      {rulerY.map((ry,i)=><g key={i} opacity={i===0||i===4?1:.55}>
        <path d={'M154 '+ry+' h28'} stroke="#B2C8D2" strokeWidth="3"/>
      </g>)}
      <path d="M182 1095 V841" stroke="#8FA8B4" strokeWidth="3" strokeDasharray="7 12" opacity=".65"/>
      <path d="M822 841 H991" stroke="#B9F4ED" strokeWidth="5" opacity=".9"/>
      <text x="903" y="807" textAnchor="middle" fill="#CFE7EF" fontSize="25" fontWeight="700">NÍVEL ALTO</text>
      <text x="218" y="1129" fill="#A5BAC6" fontSize="23">NÍVEL INICIAL</text>
      <path d={'M207 1095 V'+y} fill="none" stroke={fill>.01?GOLD:'#6F8795'} strokeWidth="7" strokeDasharray="13 11" opacity={fill>.01?1:.22}/>
      {fill>.02 && <path d={'M188 '+(y+18)+' l19 -30 19 30Z'} fill={GOLD}/>}

      {/* Hierarquia das etapas: somente a informação pedida pela etapa aparece. */}
      <rect x="80" y="1344" width="920" height="151" fill="rgba(6,13,22,.86)" stroke="#537487" strokeWidth="2"/>
      <rect x="80" y="1344" width="8" height="151" fill={GOLD}/>
      <text x="117" y="1394" fill="#A8C3CF" fontSize="25" letterSpacing="2.6" fontWeight="700">
        {state==='closed'?'01 · ISOLAR':state==='water_enter'?'02 · ENCHER':state==='rise'?'03 · ELEVAR':state==='equalize'?'04 · IGUALAR':'05 · LIBERAR'}
      </text>
      <text x="117" y="1453" fill="#FAF7EF" fontSize="42" fontWeight="850">{active?.label || 'CÂMARA FECHADA'}</text>
      <g transform="translate(118,1534)">
        {['closed','water_enter','rise','equalize','release'].map((a,i)=><rect key={a} x={i*185} width="169" height="7"
          fill={['closed','water_enter','rise','equalize','release'].indexOf(state)>=i?GOLD:'#355063'}/>)}
      </g>
      
    </svg>
    </AbsoluteFill>
  </AbsoluteFill>;
};
