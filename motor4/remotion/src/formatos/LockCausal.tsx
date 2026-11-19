/** Eclusa causal: domínio hidráulico isolado, cronologia fornecida pelo storyboard.
 * Nunca representa registro real; desenha a relação água -> nível -> navio -> equalização.
 * O enquadramento e as etapas não dependem de segundos fixos do episódio.
 */
import React from 'react';
import {AbsoluteFill} from 'remotion';

export type EventoEclusa = {
  at: number;
  action?: 'closed' | 'water_enter' | 'rise' | 'equalize' | 'release';
  label: string;
};
type Props = { t: number; events: EventoEclusa[] };
const GOLD='#FFD21F';
const ease=(v:number)=>{const x=Math.max(0,Math.min(1,v));return x*x*(3-2*x);};

export const LockCausal: React.FC<Props> = ({t,events}) => {
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
  return <AbsoluteFill style={{background:'radial-gradient(ellipse at 50% 47%,#1A3344 0%,#091625 69%,#050B15 100%)'}}>
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
  </AbsoluteFill>;
};
