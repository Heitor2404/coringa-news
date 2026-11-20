/** Litografia EUV: linguagem editorial de PROCESSO, não card de conteúdo.
 * A fonte ilumina a máscara reflexiva; os espelhos direcionam o padrão
 * e a exposição aparece no resist do wafer. Geometria NÃO em escala.
 * Tempos dependem de eventos aprovados pelo storyboard, nunca do tema.
 */
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {OpticalPortrait} from './MechanismsPortrait';

export type OpticalAction='source'|'reticle'|'projection'|'wafer';
export type OpticalCue={at:number;action?:OpticalAction|string;label:string};
type Props={t:number;events:OpticalCue[];portrait?:boolean};

const GOLD='#FFD21F',WHITE='#F5F2EB',MUTED='#AAC0CE',CYAN='#74DBEE';
const clamp=(x:number)=>Math.max(0,Math.min(1,x));
const ease=(x:number)=>{const v=clamp(x);return v*v*(3-2*v);};
const Beam:React.FC<{d:string;p:number;color?:string;glow?:boolean}>=({d,p,color=CYAN,glow=true})=>
  <g opacity={Math.max(0,p)}>
    {glow&&<path d={d} stroke={color} strokeWidth="32" opacity=".15" fill="none" strokeLinecap="round"
      pathLength={1} strokeDasharray="1" strokeDashoffset={1-p}/>}
    <path d={d} stroke={color} strokeWidth="9" fill="none" strokeLinecap="round"
      pathLength={1} strokeDasharray="1" strokeDashoffset={1-p}/>
    <path d={d} stroke={WHITE} strokeWidth="2.5" opacity=".72" fill="none"
      pathLength={1} strokeDasharray="1" strokeDashoffset={1-p}/>
  </g>;

export const OpticalProjection:React.FC<Props>=({t,events,portrait=false})=>{
  const at=(key:OpticalAction,fallback:number)=>events.find(x=>x.action===key)?.at??fallback;
  const source=ease((t-at('source',0))/.65);
  const mask=ease((t-at('reticle',1.05))/.8);
  const mirrors=ease((t-at('projection',2.5))/.9);
  const resist=ease((t-at('wafer',4.6))/.9);
  const current=Math.max(0,events.filter(e=>e.at<=t).length-1);
  const active=events[current]?.label||'EXPOSIÇÃO EUV';
  const pattern=[0,1,2,3,4,5,6];
  if(portrait) return <OpticalPortrait t={t} source={source} mask={mask} mirrors={mirrors} resist={resist}/>;
  return <AbsoluteFill style={{
    background:'radial-gradient(ellipse at 54% 47%,#172F42 0%,#081723 59%,#05111D 100%)',
    fontFamily:'Inter,Arial,sans-serif',overflow:'hidden'}}>
    <svg viewBox="0 0 1080 1920" width="100%" height="100%"
      role="img" aria-label="Ilustração: luz EUV chega à máscara reflexiva, é projetada por espelhos e altera o resist do wafer; esquema sem escala">
      <defs>
        <pattern id="opt-grid" width="70" height="70" patternUnits="userSpaceOnUse">
          <path d="M70 0H0V70" stroke="#6390A9" strokeOpacity=".13" strokeWidth="1.2" fill="none"/>
        </pattern>
        <radialGradient id="opt-glow"><stop stopColor={GOLD} stopOpacity=".48"/>
          <stop offset=".40" stopColor={GOLD} stopOpacity=".14"/>
          <stop offset="1" stopColor={GOLD} stopOpacity="0"/></radialGradient>
        <linearGradient id="opt-mirror" x1="0" y1="0" x2="1" y2="1">
          <stop stopColor="#CBF2F5"/><stop offset=".34" stopColor="#80B8CD"/>
          <stop offset="1" stopColor="#234A63"/>
        </linearGradient>
        <linearGradient id="opt-wafer" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="#B7DDE8"/><stop offset=".42" stopColor="#618D9D"/>
          <stop offset="1" stopColor="#213D54"/>
        </linearGradient>
        <linearGradient id="opt-reticle" x1="0" y1="0" x2="1" y2="1">
          <stop stopColor="#577D91"/><stop offset=".37" stopColor="#1D4154"/>
          <stop offset="1" stopColor="#0C2536"/>
        </linearGradient>
        <clipPath id="opt-wafer-clip"><ellipse cx="521" cy="1306" rx="306" ry="85"/></clipPath>
      </defs>
      <rect width="1080" height="1920" fill="url(#opt-grid)"/>
      <circle cx="529" cy="1040" r="490" fill="#25566F" opacity=".065"/>
      <path d="M66 597 H1015" stroke="#48697C" strokeWidth="2" opacity=".7"/>

      <text x="70" y="427" fill={MUTED} fontWeight="850" letterSpacing="3" fontSize="29">ENGENHARIA EXPLICADA</text>
      <text x="70" y="506" fill={WHITE} fontSize="60" fontWeight="900">COMO A LUZ DESENHA</text>
      <text x="70" y="567" fill={WHITE} fontSize="60" fontWeight="900">O PADRÃO NO CHIP?</text>

      {/* Fonte: energia luminosa, sem bloco de texto em volta. */}
      <circle cx="185" cy="808" r={137+source*20} fill="url(#opt-glow)" opacity={source}/>
      <circle cx="185" cy="808" r="72" fill="#0E2C3D" stroke="#6591A5" strokeWidth="4"/>
      {Array.from({length:12},(_,i)=>{
        const a=i*Math.PI/6+t*1.7, r1=52,r2=67+source*8;
        return <path key={i} d={'M'+(185+Math.cos(a)*r1)+' '+(808+Math.sin(a)*r1)+' L'+
          (185+Math.cos(a)*r2)+' '+(808+Math.sin(a)*r2)}
          stroke={GOLD} strokeWidth="4" opacity={source*.78}/>;
      })}
      <circle cx="185" cy="808" r={17+source*8} fill={GOLD}/>
      <circle cx="185" cy="808" r="9" fill={WHITE}/>
      <text x="185" y="949" textAnchor="middle" fill={WHITE} fontWeight="850" fontSize="31">LUZ EUV</text>
      <text x="185" y="989" textAnchor="middle" fill={MUTED} fontSize="25">FONTE</text>

      {/* A máscara EUV REFLETE a luz. Feixes são explicativos, não traçado real. */}
      <Beam d="M270 808 L539 805" p={source} color={GOLD}/>
      <g transform="translate(532 682)">
        <path d="M0 17 L320 17 340 50 25 50Z" fill="#6E9AAA" opacity=".7"/>
        <rect x="22" y="48" width="312" height="214" rx="17" fill="url(#opt-reticle)"
          stroke={mask>.02?GOLD:'#4D7689'} strokeWidth="5"/>
        <rect x="42" y="67" width="275" height="174" rx="9" fill="#0C1E2D" stroke="#6B8999" strokeWidth="2"/>
        {pattern.map((i)=><g key={i}>
          <rect x={53+i*37} y="87" width={i%3===1?21:23} height="127" rx="3"
            fill={i%3===1?'#36677E':GOLD} opacity={.19+.78*mask}/>
          {i%3!==1&&<rect x={56+i*37} y="105" width="6" height="92" fill={WHITE} opacity={mask*.3}/>}
        </g>)}
        <path d="M22 243 H332" stroke={CYAN} strokeWidth="4" opacity={.1+.6*mask}/>
      </g>
      <text x="713" y="1001" fill={WHITE} textAnchor="middle" fontSize="32" fontWeight="850">MÁSCARA</text>
      <text x="713" y="1040" fill={MUTED} textAnchor="middle" fontSize="25">REFLEXIVA</text>
      <Beam d="M766 925 L827 1071" p={mask} color={CYAN}/>

      {/* Uma superfície óptica estilizada; o equipamento real tem vários espelhos. */}
      <ellipse cx="824" cy="1105" rx="147" ry="33" transform="rotate(-27 824 1105)"
        fill="url(#opt-mirror)" stroke="#B4F5F6" strokeWidth="6"/>
      <ellipse cx="824" cy="1105" rx="112" ry="12" transform="rotate(-27 824 1105)"
        fill="#87D7E3" opacity={.20+.45*mirrors}/>
      <text x="1010" textAnchor="end" y="1158" fill={WHITE} fontSize="31" fontWeight="850">ESPELHOS</text>
      <text x="1010" textAnchor="end" y="1195" fill={MUTED} fontSize="24">ÓPTICOS</text>
      <Beam d="M785 1137 L559 1266" p={mirrors} color={CYAN}/>

      {/* Wafer suficientemente grande para mostrar a alteração do resist. */}
      <ellipse cx="521" cy="1330" rx="317" ry="99" fill="#03121D" opacity=".65"/>
      <path d="M204 1322 Q207 1447 521 1447 Q835 1447 838 1322 L838 1351 Q813 1464 521 1464 Q228 1464 204 1351Z"
        fill="url(#opt-wafer)" stroke="#A3D3DF" strokeWidth="4"/>
      <ellipse cx="521" cy="1306" rx="306" ry="85" fill="#113449" stroke="#B6E9EB" strokeWidth="6"/>
      <ellipse cx="521" cy="1306" rx="285" ry="73" fill="none" stroke="#5CA2BA" strokeWidth="2" opacity=".8"/>
      <g clipPath="url(#opt-wafer-clip)">
        {Array.from({length:10},(_,i)=><path key={'w'+i} d={'M'+(251+i*60)+' 1208 V1411'}
          stroke="#63A6BA" strokeWidth="2" opacity=".24"/>)}
        {Array.from({length:4},(_,i)=><path key={'h'+i} d={'M208 '+(1264+i*27)+' H835'}
          stroke="#63A6BA" strokeWidth="2" opacity=".24"/>)}
        {pattern.map((i)=><g key={i} opacity={resist}>
          <rect x={323+i*58} y={1281+(i%2)*7} width="38" height="42" rx="3"
            fill={GOLD} opacity={.45+.45*resist}/>
          <rect x={331+i*58} y={1287+(i%2)*7} width="7" height="30" fill={WHITE} opacity=".24"/>
        </g>)}
        <rect x={201+660*resist} y="1210" width="26" height="1920" fill={CYAN} opacity={resist>0&&resist<1?.22:0}/>
      </g>
      <text x="521" y="1531" fill={WHITE} textAnchor="middle" fontSize="35" fontWeight="900">CAMADA FOTOSSENSÍVEL</text>
      <text x="521" y="1574" fill={resist>.05?GOLD:MUTED} textAnchor="middle" fontSize="29" fontWeight="700">
        {resist>.05?'PADRÃO SENDO EXPOSTO NO WAFER':'WAFER ANTES DA EXPOSIÇÃO'}
      </text>

      {/* Uma etapa editorial discreta, não novo card imenso. */}
      <text x="74" y="1644" fill={GOLD} fontSize="32" fontWeight="900">
        {String(current+1).padStart(2,'0')+'  /  '+active.replace(/^[0-9]+\s*·\s*/,'')}
      </text>
    </svg>
  </AbsoluteFill>;
};
