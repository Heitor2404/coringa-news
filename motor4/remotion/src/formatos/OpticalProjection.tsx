/** Mecanismo óptico didático: EUV -> máscara REFLEXIVA -> espelhos -> resist.
 * Geometria ilustrativa, NÃO é a trajetória ou a máquina ASML em escala.
 * O storyboard define tempos/ações; não geramos medições nem filmagem falsa.
 */
import React from 'react';
import {AbsoluteFill} from 'remotion';

export type OpticalAction='source'|'reticle'|'projection'|'wafer';
export type OpticalCue={at:number;action?:OpticalAction|string;label:string};
type Props={t:number;events:OpticalCue[]};

const GOLD='#FFD21F',WHITE='#F5F2EB',MUTED='#B3CAD5',CYAN='#77D5E7';
const clamp=(x:number)=>Math.max(0,Math.min(1,x));
const smooth=(x:number)=>{const v=clamp(x);return v*v*(3-2*v);};

const DrawBeam:React.FC<{d:string;progress:number;encoded?:boolean}>=({d,progress,encoded})=>
  <g opacity={Math.max(.05,progress)}>
    <path d={d} fill="none" stroke={encoded?CYAN:GOLD} strokeWidth={26}
      strokeLinecap="round" opacity={.10*progress}/>
    <path d={d} fill="none" stroke={encoded?CYAN:GOLD} strokeWidth={encoded?7:11}
      strokeLinecap="round" pathLength={1} strokeDasharray="1"
      strokeDashoffset={1-progress}/>
  </g>;

export const OpticalProjection:React.FC<Props>=({t,events})=>{
  const at=(name:OpticalAction,fallback:number)=>
    events.find(x=>x.action===name)?.at ?? fallback;
  const source=smooth((t-at('source',0))/.68);
  const mask=smooth((t-at('reticle',1.05))/.80);
  const mirrors=smooth((t-at('projection',2.5))/.90);
  const resist=smooth((t-at('wafer',4.6))/.80);
  const event=events.filter(x=>x.at<=t).slice(-1)[0] || events[0];
  const patterns=[0,1,2,3,4];

  return <AbsoluteFill style={{background:'radial-gradient(ellipse at 50% 46%,#162D3F 0%,#091523 78%)',fontFamily:'Inter,Arial,sans-serif'}}>
    <svg width="100%" height="100%" viewBox="0 0 1080 1920"
      aria-label="Esquema ilustrativo: a luz ultravioleta extrema é refletida em uma máscara, guiada por espelhos e expõe o resist do wafer">
      <defs>
        <pattern id="opticalGrid" width="66" height="66" patternUnits="userSpaceOnUse">
          <path d="M66 0H0V66" stroke="#7291A1" strokeOpacity=".12" strokeWidth="1"/>
        </pattern>
        <linearGradient id="waferBody" x1="0" x2="0" y1="0" y2="1">
          <stop stopColor="#B6CDD5"/><stop offset="1" stopColor="#34556C"/>
        </linearGradient>
      </defs>
      <rect width="1080" height="1920" fill="url(#opticalGrid)"/>
      <text x="75" y="430" fill={MUTED} fontSize="26" letterSpacing="2.1" fontWeight="800">PROCESSO FÍSICO · DESENHO SIMPLIFICADO</text>
      <text x="74" y="500" fill={WHITE} fontSize="54" fontWeight="900">COMO O PADRÃO CHEGA AO CHIP?</text>
      <text x="75" y="554" fill="#91B0C1" fontSize="27">Litografia EUV · exposição de uma camada</text>

      {/* Fonte física (luz EUV) -> máscara refletora. */}
      <rect x="92" y="648" width="258" height="185" rx="20" fill="#0D2537" stroke="#426479" strokeWidth="3"/>
      <circle cx="220" cy="735" r={35+source*13} fill={GOLD} opacity={.12+.20*source}/>
      <circle cx="220" cy="735" r={23+source*5} fill={GOLD} opacity={.35+.60*source}/>
      <circle cx="220" cy="735" r="13" fill={WHITE}/>
      <text x="220" y="876" textAnchor="middle" fill={WHITE} fontSize="29" fontWeight="800">LUZ EUV</text>
      <DrawBeam d="M270 735 L550 745" progress={source}/>

      {/* EUV usa máscara reflexiva, nunca o ícone de uma máscara transmissiva. */}
      <rect x="550" y="664" width="298" height="157" rx="16" fill="#122B3F" stroke={mask>.08?GOLD:'#547184'} strokeWidth="4"/>
      {patterns.map((x)=><g key={x}>
        <rect x={579+x*49} y="698" width="26" height="79" rx="3"
          fill={x%2? '#294A5C':GOLD} opacity={.20+.75*mask}/>
      </g>)}
      <text x="698" y="874" textAnchor="middle" fill={WHITE} fontSize="27" fontWeight="800">MÁSCARA REFLEXIVA</text>

      {/* Desvio representativo da luz já modulada; espelhos EUV, não lentes. */}
      <DrawBeam d="M712 821 L806 983" progress={mask} encoded/>
      <ellipse cx="821" cy="1004" rx="118" ry="24" transform="rotate(-24 821 1004)"
        fill="#4F7888" stroke={CYAN} strokeWidth="5"/>
      <path d="M740 1015 Q820 953 901 971" fill="none"
        stroke={CYAN} strokeWidth="3" opacity={.38+.62*mirrors}/>
      <text x="821" y="1102" textAnchor="middle" fill={WHITE} fontSize="29" fontWeight="800">ESPELHOS</text>
      <text x="821" y="1134" textAnchor="middle" fill={MUTED} fontSize="24">DE PROJEÇÃO</text>
      <DrawBeam d="M797 1035 L590 1223" progress={mirrors} encoded/>

      {/* A exposição modifica o resist; NÃO cria instantaneamente um circuito pronto. */}
      <ellipse cx="514" cy="1300" rx="258" ry="77" fill="url(#waferBody)" stroke="#9CB8C8" strokeWidth="5"/>
      <ellipse cx="514" cy="1288" rx="245" ry="63" fill="#18364C" stroke={CYAN} strokeWidth="3"/>
      {patterns.map((x)=><g key={x} opacity={resist}>
        <rect x={354+x*59} y={1269+(x%2)*7} width="38" height="28"
          rx="3" fill={GOLD} opacity={x%2?.50:1}/>
      </g>)}
      <path d="M325 1325 Q512 1388 707 1325" fill="none" stroke="#D5EAEC" strokeWidth="5" opacity=".42"/>
      <text x="515" y="1433" textAnchor="middle" fill={WHITE} fontSize="31" fontWeight="900">RESIST NO WAFER</text>
      <text x="515" y="1474" textAnchor="middle" fill={MUTED} fontSize="27">
        {resist>.15?'PADRÃO EXPOSTO NA CAMADA FOTOSSENSÍVEL':'SUPERFÍCIE FOTOSSENSÍVEL'}
      </text>
      <text x="76" y="1566" fill={GOLD} fontSize="30" fontWeight="900">
        {event?.label || 'ESQUEMA EXPLICATIVO'}
      </text>
      <text x="76" y="1603" fill={MUTED} fontSize="23">Etapas representadas, não equipamentos em escala</text>
    </svg>
  </AbsoluteFill>;
};
