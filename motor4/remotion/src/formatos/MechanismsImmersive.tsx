/** Palco imersivo por FAIXAS, não por tema. A área superior (840x345) é
 * segura ANTES da coluna de ícones; a área inferior 620x247 cai na
 * interseção conservadora com os ícones. Ambas derivam do contrato de
 * plataformas e são inspecionadas por fase. A lógica física é recebida
 * das mesmas timelines de EUV / eclusa, nunca recriada aqui.
 */
import React from 'react';
import {AbsoluteFill} from 'remotion';
import safety from './safe-zones-vertical.json';
import {Sun,Reticle,Mirror,Wafer,Beam} from './MechanismsPortrait';

const GOLD='#FFD21F', WHITE='#F5F2EB', MUTED='#9BB8C8', AQUA='#74DCE9';
const S=safety.mechanism_layout;
const rstyle=(r:readonly number[]):React.CSSProperties=>({
  position:'absolute',left:r[0],top:r[1],width:r[2]-r[0],height:r[3]-r[1]
});
const clamp=(x:number)=>Math.max(0,Math.min(1,x));

type Phase='source'|'reticle'|'projection'|'wafer';
const names:Phase[]=['source','reticle','projection','wafer'];

const Stage:React.FC<{kind:string;children:React.ReactNode;support:React.ReactNode}>=
({kind,children,support})=>
  <AbsoluteFill style={{background:'transparent',fontFamily:'Inter,Arial,sans-serif'}}>
    <div data-safe-role="wide_mechanism_hero"
      style={{...rstyle(S.wide_hero),overflow:'hidden'}}>
      <svg viewBox="0 0 840 345" width="100%" height="100%"
        preserveAspectRatio="xMidYMid meet" role="img" aria-label={kind}>
        <defs>
          <linearGradient id="wide-water" x1="0" y1="0" x2="0" y2="1">
            <stop stopColor="#8FF7F4"/>
            <stop offset=".3" stopColor="#4ABAD5"/>
            <stop offset="1" stopColor="#165171"/>
          </linearGradient>
          <linearGradient id="wide-metal" x1="0" y1="0" x2="0" y2="1">
            <stop stopColor="#FFFFFF"/><stop offset=".6" stopColor="#BAD6E0"/>
            <stop offset="1" stopColor="#557F91"/>
          </linearGradient>
        </defs>
        <rect width="840" height="345" fill="#081D2D" opacity=".33"/>
        <circle cx="420" cy="177" r="300" fill="#24556C" opacity=".16"/>
        {children}
      </svg>
    </div>
    <div data-safe-role="wide_mechanism_support"
      style={{...rstyle(S.wide_support),overflow:'hidden'}}>
      <svg viewBox="0 0 620 247" width="100%" height="100%"
        preserveAspectRatio="xMidYMid meet" role="img" aria-label="Visão causal complementar dentro da área protegida">
        <path d="M18 16 H602" stroke="#456D80" strokeWidth="2"/>
        {support}
      </svg>
    </div>
  </AbsoluteFill>;

export const OpticalImmersive:React.FC<{
  t:number;source:number;mask:number;mirrors:number;resist:number;phase?:string
}>=({t,source,mask,mirrors,resist,phase='source'})=>{
  const step=(names.includes(phase as Phase)?phase:'source') as Phase;
  const active=names.indexOf(step);
  return <Stage kind="Litografia EUV: close amplo causal dentro da faixa sem controles laterais"
    support={<g>
      <path d="M80 76 H540" fill="none" stroke="#5C8B9E" strokeWidth="4"/>
      {names.map((n,i)=>{
        const x=80+i*153;
        return <g key={n}>
          <circle cx={x} cy="76" r={active===i?19:13}
            fill={i<=active?GOLD:'#304E64'} stroke="#C8E6EF" strokeWidth="2"/>
          <text x={x} y="123" fontSize="20" textAnchor="middle"
            fontWeight={active===i?900:700} fill={active===i?WHITE:MUTED}>
            {['FONTE','MÁSCARA','ESPELHOS','WAFER'][i]}
          </text>
          <path d={`M${x-48} 148 h96`} stroke={active===i?GOLD:'#355970'}
            strokeWidth={active===i?5:2}/>
        </g>;
      })}
      <text x="310" y="202" fontSize="22" textAnchor="middle"
        fill={MUTED} fontWeight="650">LUZ → PADRÃO → PROJEÇÃO → RESIST</text>
    </g>}>
    {step==='source'&&<g>
      <Sun x={190} y={174} r={127} t={t} p={source}/>
      <Beam d="M322 174 H409" color={GOLD} progress={source}/>
      <Reticle x={416} y={65} w={382} h={239} progress={mask}/>
    </g>}
    {step==='reticle'&&<g>
      <Sun x={122} y={177} r={72} t={t} p={source}/>
      <Beam d="M200 177 H254" color={GOLD} progress={source}/>
      <Reticle x={263} y={33} w={523} h={278} progress={mask}/>
    </g>}
    {step==='projection'&&<g>
      <Reticle x={42} y={70} w={272} h={182} progress={mask}/>
      <Beam d="M301 214 L422 183" progress={mask}/>
      <Mirror x={595} y={175} rx={193} p={mirrors}/>
      <Beam d="M563 227 L437 304" progress={mirrors}/>
    </g>}
    {step==='wafer'&&<g>
      <Mirror x={173} y={86} rx={120} p={mirrors}/>
      <Beam d="M265 119 L494 188" progress={mirrors}/>
      <Wafer x={577} y={209} rx={231} p={resist}/>
    </g>}
  </Stage>;
};

export const LockImmersive:React.FC<{
  t:number;fill:number;open:number;isFlow:boolean;state:string
}>=({t,fill,open,isFlow,state})=>{
  const level=299-127*clamp(fill);
  const hullShift=level-299;
  const gate=clamp(open),flow=isFlow?GOLD:AQUA;
  return <Stage kind="Corte grande de eclusa: reservatório elevado, conduto inferior, câmara, barco flutuante"
    support={<g>
      {/* O apoio amplia o componente CAUSAL e não inventa um segundo tanque. */}
      <path d="M555 27 V161 H154 V72" fill="none" stroke="#38576A"
        strokeWidth="54" strokeLinejoin="round" strokeLinecap="round"/>
      <path d="M555 27 V161 H154 V72" fill="none" stroke="#81A5B5"
        strokeWidth="32" strokeLinejoin="round" strokeLinecap="round"/>
      <path d="M555 27 V161 H154 V72" fill="none"
        stroke={flow} strokeWidth="15" strokeLinecap="round" strokeLinejoin="round"
        strokeDasharray="25 25" strokeDashoffset={-t*81}
        opacity={isFlow?1:.22}/>
      <circle cx="555" cy="90" r={state==='water_enter'?43:33}
        fill="#092535" stroke={isFlow?GOLD:'#B8D4DF'} strokeWidth="6"/>
      <path d="M535 70 L575 110 M535 110 L575 70" fill="none"
        stroke={isFlow?GOLD:WHITE} strokeWidth="7" strokeLinecap="round"/>
      <text x="140" y="226" fontWeight="820" fill={WHITE} fontSize="23"
        textAnchor="middle">ENTRA PELO FUNDO</text>
      <text x="531" y="226" fontWeight="820" fill={isFlow?GOLD:WHITE}
        fontSize="23" textAnchor="middle">VÁLVULA</text>
    </g>}>
    {/* Faixa superior larga: a relação navio/água/reservatório CABE inteira. */}
    <rect x="35" y="83" width="532" height="251" fill="#061829"
      stroke="#6D95A8" strokeWidth="4"/>
    <rect x="649" y="114" width="161" height="220" fill="#102B3E"
      stroke="#7C9BA9" strokeWidth="4"/>
    <rect x="656" y="171" width="149" height="163" fill="url(#wide-water)"/>
    <path d="M656 171 H805" stroke="#D8FFFF" strokeWidth="7"/>
    <rect x="39" y={level} width="524" height={334-level} fill="url(#wide-water)"/>
    <path d={`M38 ${level} H565`} stroke="#D6FFFF" strokeWidth="7"/>
    {Array.from({length:9},(_,i)=><path key={i}
      d={`M${55+i*54} ${level+14+Math.sin(t*4+i)*2} h34`}
      stroke="#CBF9FF" strokeWidth="3" opacity=".5"/>)}
    <g transform={`translate(${gate*44} ${hullShift})`}>
      <path d="M102 255 H505 L457 300 H148Z" fill="url(#wide-metal)"
        stroke="#F5FFFF" strokeWidth="5"/>
      <path d="M151 286 H456" stroke="#5B8498" strokeWidth="7"/>
      <rect x="176" y="216" width="238" height="37" rx="3"
        fill="#F2F8F7" stroke="#B0D2DA" strokeWidth="3"/>
      <rect x="219" y="185" width="145" height="31" fill="#E5F2F3"/>
      <rect x="285" y="155" width="12" height="30" fill="#AED4E1"/>
      {Array.from({length:6},(_,i)=><rect key={i} x={184+i*36}
        y="229" width="24" height="15" fill="#28546C"/>)}
    </g>
    <rect x="26" y="80" width="20" height="257" fill="#ABC3CA"/>
    <g opacity={1-gate*.94} transform={`translate(${gate*42} 0)`}>
      <rect x="567" y="83" width="23" height="252" fill="#94B0BD"
        stroke="#E0F8FC" strokeWidth="2"/>
    </g>
    {state==='rise'&&<g opacity={.45+.38*Math.sin(t*5)}>
      <path d={`M76 ${level+8} V${level-104}`} stroke={GOLD} strokeWidth="8" strokeDasharray="11 9"/>
      <path d={`M55 ${level-82} L76 ${level-116} L97 ${level-82}Z`} fill={GOLD}/>
    </g>}
    {state==='equalize'&&<path d="M43 171 H805" stroke={GOLD}
      strokeWidth="5" strokeDasharray="13 12" opacity=".60"/>}
    <text x="63" y="58" fontWeight="850" fontSize="24" fill={WHITE}>CÂMARA DA ECLUSA</text>
    <text x="667" y="89" fontWeight="850" fontSize="22" fill={GOLD}>NÍVEL ALTO</text>
  </Stage>;
};
