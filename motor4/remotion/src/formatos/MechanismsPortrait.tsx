/** Reflow vertical nativo para cenários de mecanismos reutilizáveis.
 * Recebe PROGRESSO FÍSICO dos renderers existentes; não reimplementa
 * cronologia editorial nem cria fatos. Caixa SVG corresponde à janela
 * protegida 620x682, sem crop da arte 1080x1920 do modo legado.
 * Painel e labels estão no mesmo palco; fundo de atmosfera pertence
 * ao compositor e pode ser full-bleed fora da região essencial.
 */
import React from 'react';
import {AbsoluteFill} from 'remotion';

const GOLD='#FFD21F', OFF='#F5F2EB', MUTED='#ACC6D4', AQUA='#69E0EC';
const clamp=(n:number)=>Math.min(1,Math.max(0,n));
type OpticalPortraitProps={t:number;source:number;mask:number;mirrors:number;resist:number};
type LockPortraitProps={t:number;fill:number;open:number;isFlow:boolean;state:string};

const Base:React.FC<{children:React.ReactNode;name:string}>=({children,name})=>
  <AbsoluteFill style={{background:'transparent',fontFamily:'Inter,Arial,sans-serif'}}>
    <svg width="100%" height="100%" viewBox="0 0 620 682"
      preserveAspectRatio="xMidYMid meet" role="img" aria-label={name}>
      <defs>
        <pattern id="portrait-grid" width="52" height="52" patternUnits="userSpaceOnUse">
          <path d="M52 0H0V52" stroke="#608FA8" strokeWidth="1" opacity=".12" fill="none"/>
        </pattern>
        <linearGradient id="portrait-water" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="#78EDF1"/>
          <stop offset=".24" stopColor="#39ABCC"/>
          <stop offset="1" stopColor="#155171"/>
        </linearGradient>
        <linearGradient id="portrait-steel" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="#FFFFFF"/>
          <stop offset=".65" stopColor="#A9C9D4"/>
          <stop offset="1" stopColor="#577F95"/>
        </linearGradient>
        <linearGradient id="portrait-mirror" x1="0" x2="1" y1="0" y2="1">
          <stop stopColor="#DEFBFF"/><stop offset=".52" stopColor="#80C8DC"/>
          <stop offset="1" stopColor="#35627A"/>
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="620" height="682" fill="url(#portrait-grid)"/>
      {children}
    </svg>
  </AbsoluteFill>;

export const Beam:React.FC<{d:string;progress:number;color?:string}>=({d,progress,color=AQUA})=>
  <g opacity={clamp(progress)}>
    <path d={d} stroke={color} strokeWidth="20" opacity=".18"
      fill="none" strokeLinecap="round" pathLength={1}
      strokeDasharray="1" strokeDashoffset={1-clamp(progress)}/>
    <path d={d} stroke={color} strokeWidth="6"
      fill="none" strokeLinecap="round" pathLength={1}
      strokeDasharray="1" strokeDashoffset={1-clamp(progress)}/>
    <path d={d} stroke={OFF} strokeWidth="1.5" opacity=".66"
      fill="none" strokeLinecap="round" pathLength={1}
      strokeDasharray="1" strokeDashoffset={1-clamp(progress)}/>
  </g>;


/** Direção responsiva por CAPACIDADE: em vez de miniaturizar quatro
 * objetos simultâneos, cada fase destaca fisicamente o objeto ativo.
 * A relação causal permanece visível no trilho da sequência.
 * Nenhum tema/episódio entra na geometria.
 */
type Phase='source'|'reticle'|'projection'|'wafer';
const Steps:React.FC<{active:number}>=({active})=><g>
  <path d="M112 622 H509" fill="none" stroke="#52778B" strokeWidth="4"/>
  {['LUZ','MÁSCARA','ESPELHOS','WAFER'].map((s,i)=>{
    const x=112+i*132;
    return <g key={s}>
      <circle cx={x} cy="622" r={i===active?16:11}
        fill={i<=active?GOLD:'#284A5F'} stroke="#C2E0E8" strokeWidth={i===active?3:1.5}/>
      <text x={x} y="659" fill={i===active?OFF:MUTED} fontSize="17"
        textAnchor="middle" fontWeight={i===active?900:650}>{s}</text>
    </g>;
  })}
</g>;
export const Reticle:React.FC<{x:number;y:number;w:number;h:number;progress:number}>=({x,y,w,h,progress})=>
  <g>
    <path d={`M${x+8} ${y-14} H${x+w-14} L${x+w} ${y+6} H${x+18}Z`}
      fill="#779DB0" opacity=".72"/>
    <rect x={x} y={y} width={w} height={h} rx="11" fill="#102C40"
      stroke={progress>.02?GOLD:'#779AAE'} strokeWidth="6"/>
    <rect x={x+17} y={y+15} width={w-34} height={h-30} rx="6" fill="#051C2C"
      stroke="#5F8A9C" strokeWidth="2"/>
    {Array.from({length:7},(_,i)=><rect key={i}
      x={x+27+i*(w-65)/7} y={y+30}
      width={(w-65)/11} height={h-60} rx="2"
      fill={i%3===1?'#376C81':GOLD} opacity={.22+.78*progress}/>)}
  </g>;
export const Sun:React.FC<{x:number;y:number;r:number;t:number;p:number}>=({x,y,r,t,p})=>
  <g>
    <circle cx={x} cy={y} r={r*1.5} fill={GOLD} opacity={.05+.07*p}/>
    <circle cx={x} cy={y} r={r} fill="#0F3246"
      stroke="#8ABDD0" strokeWidth="5"/>
    {Array.from({length:12},(_,i)=>{
      const a=i*Math.PI/6+t*.9;
      const x1=x+Math.cos(a)*r*.70,y1=y+Math.sin(a)*r*.70;
      const x2=x+Math.cos(a)*r*.95,y2=y+Math.sin(a)*r*.95;
      return <path key={i} d={`M${x1} ${y1} L${x2} ${y2}`}
        stroke={GOLD} strokeWidth="6" opacity={.5+.5*p}/>;
    })}
    <circle cx={x} cy={y} r={r*.19} fill={GOLD}/>
    <circle cx={x-4} cy={y-3} r={r*.07} fill={OFF}/>
  </g>;
export const Mirror:React.FC<{x:number;y:number;rx:number;p:number}>=({x,y,rx,p})=>
  <g>
    <ellipse cx={x} cy={y} rx={rx} ry={rx*.22}
      transform={`rotate(-26 ${x} ${y})`}
      fill="url(#portrait-mirror)" stroke="#D1FFFF" strokeWidth="6"/>
    <ellipse cx={x} cy={y} rx={rx*.77} ry={rx*.077}
      transform={`rotate(-26 ${x} ${y})`}
      fill="#98EDF5" opacity={.15+.55*p}/>
  </g>;
export const Wafer:React.FC<{x:number;y:number;rx:number;p:number}>=({x,y,rx,p})=>
  <g>
    <path d={`M${x-rx} ${y} Q${x-rx+12} ${y+105} ${x} ${y+105} Q${x+rx-12} ${y+105} ${x+rx} ${y} L${x+rx} ${y+32} Q${x+rx-28} ${y+125} ${x} ${y+125} Q${x-rx+28} ${y+125} ${x-rx} ${y+32}Z`}
      fill="url(#portrait-steel)" stroke="#C0F3F7" strokeWidth="5"/>
    <ellipse cx={x} cy={y} rx={rx} ry={rx*.3} fill="#123B50"
      stroke="#C3FFFF" strokeWidth="6"/>
    <ellipse cx={x} cy={y} rx={rx*.88} ry={rx*.23}
      fill="none" stroke="#65B1C3" strokeWidth="3"/>
    {Array.from({length:7},(_,i)=><rect key={i}
      x={x-rx*.65+i*rx*.21} y={y-rx*.065+(i%2)*7}
      width={rx*.16} height={rx*.16} rx="3"
      fill={GOLD} opacity={p*.9}/>)}
  </g>;

export const OpticalPortrait:React.FC<OpticalPortraitProps & {phase?:string}>=
({t,source,mask,mirrors,resist,phase='source'})=>{
  const stage:Phase = (['source','reticle','projection','wafer'].includes(phase)?phase:'source') as Phase;
  const index=(['source','reticle','projection','wafer'] as Phase[]).indexOf(stage);
  return <Base name="EUV em close por ação: fonte, máscara reflexiva, espelhos e wafer com trilho causal">
    {/* Fundo cinemático. A ação ativa é grande e aparece integralmente na SAFE. */}
    <circle cx="315" cy="298" r="265" fill="#2A6077" opacity=".13"/>
    <circle cx="315" cy="298" r="207" fill="none" stroke="#42677F" strokeWidth="2" opacity=".28"/>
    {stage==='source'&&<g>
      <Sun x={209} y={269} r={113} t={t} p={source}/>
      <Beam d="M324 269 H398" color={GOLD} progress={source}/>
      <Reticle x={405} y={174} w={175} h={190} progress={mask}/>
      <text x="209" y="456" textAnchor="middle" fontSize="31" fontWeight="900" fill={OFF}>LUZ EUV</text>
      <text x="209" y="492" textAnchor="middle" fontSize="21" fill={MUTED}>FONTE LUMINOSA</text>
      <text x="493" y="401" textAnchor="middle" fontSize="23" fontWeight="800" fill={OFF}>MÁSCARA</text>
    </g>}
    {stage==='reticle'&&<g>
      <Sun x={90} y={266} r={46} t={t} p={source}/>
      <Beam d="M143 266 H186" color={GOLD} progress={source}/>
      <Reticle x={191} y={124} w={377} h={316} progress={mask}/>
      <text x="383" y="489" textAnchor="middle" fontSize="31" fontWeight="900" fill={OFF}>MÁSCARA REFLEXIVA</text>
      <text x="383" y="530" textAnchor="middle" fontSize="22" fill={MUTED}>O PADRÃO É REFLETIDO</text>
    </g>}
    {stage==='projection'&&<g>
      <Reticle x={43} y={82} w={252} h={153} progress={mask}/>
      <Beam d="M281 198 L351 315" progress={mask}/>
      <Mirror x={391} y={326} rx={174} p={mirrors}/>
      <Beam d="M339 364 L266 465" progress={mirrors}/>
      <ellipse cx="246" cy="510" rx="179" ry="48" fill="#0C2637" stroke="#9ADCE5" strokeWidth="5"/>
      <text x="395" y="449" fontSize="31" textAnchor="middle" fontWeight="900" fill={OFF}>ESPELHOS</text>
      <text x="395" y="485" fontSize="21" textAnchor="middle" fill={MUTED}>PROJETAM A LUZ</text>
    </g>}
    {stage==='wafer'&&<g>
      <Mirror x={470} y={157} rx={105} p={mirrors}/>
      <Beam d="M442 205 L349 281" progress={mirrors}/>
      <Wafer x={301} y={334} rx={253} p={resist}/>
      <text x="306" y="528" fontSize="29" fontWeight="900"
        textAnchor="middle" fill={OFF}>CAMADA FOTOSSENSÍVEL</text>
      <text x="306" y="563" fontSize="21" textAnchor="middle"
        fill={resist>.1?GOLD:MUTED}>
        {resist>.1?'PADRÃO SENDO EXPOSTO':'ANTES DA EXPOSIÇÃO'}
      </text>
    </g>}
    <Steps active={index}/>
  </Base>;
};

/** O renderer de eclusa preserva a geometria causal INTEGRAL em cada estado:
 * lado alto, conduto inferior, portão e casco que flutua. A atenção muda
 * pela cor/movimento sem cortar nenhum desses atores.
 */
export const LockPortrait:React.FC<LockPortraitProps>=({t,fill,open,isFlow,state})=>{
  const waterY=492-237*clamp(fill);
  const hullY=waterY-11;
  const gate=clamp(open);
  const beam=isFlow?GOLD:'#6FA6BA';
  return <Base name="Eclusa vertical: reservatório alto alimenta por gravidade a câmara; navio flutua com o nível e portão abre na equalização">
    <circle cx="280" cy="330" r="286" fill="#205B70" opacity=".16"/>
    <path d="M20 92 H600" stroke="#476D80" strokeWidth="3" opacity=".8"/>
    <text x="39" y="72" fontSize="22" fontWeight="900" fill={OFF}>CÂMARA</text>
    <text x="462" y="72" fontSize="22" fontWeight="900" fill={GOLD}>LADO ALTO</text>
    <rect x="30" y="176" width="414" height="397" rx="2" fill="#061A29" stroke="#7199A9" strokeWidth="4"/>
    <rect x="471" y="230" width="122" height="343" fill="#132F40" stroke="#769AAA" strokeWidth="4"/>
    <rect x="479" y="254" width="106" height="319" fill="url(#portrait-water)" opacity=".9"/>
    <path d="M479 254 H585" stroke="#E0FFFF" strokeWidth="6"/>
    <rect x="34" y={waterY} width="406" height={573-waterY}
      fill="url(#portrait-water)" opacity=".93"/>
    <path d={`M33 ${waterY} H442`} stroke="#D7FFFF" strokeWidth="7"/>
    {Array.from({length:7},(_,i)=><path key={i} d={`M${48+i*55} ${waterY+18+Math.sin(t*4+i)*2} h35`}
      stroke="#C9FAFF" opacity=".48" strokeWidth="3"/>)}
    {/* Navio sobe APENAS em resposta ao nível da água. */}
    <g transform={`translate(${gate*48} ${hullY-455})`}>
      <path d="M69 407 H391 L357 466 H105Z"
        fill="url(#portrait-steel)" stroke="#F2FFFF" strokeWidth="5"/>
      <path d="M105 452 H358" stroke="#60889A" strokeWidth="7"/>
      <rect x="134" y="364" width="200" height="41" rx="3"
        fill="#E8F4F5" stroke="#9DC4D0" strokeWidth="2"/>
      <rect x="161" y="328" width="145" height="34" rx="2" fill="#ECF7F8"/>
      <rect x="220" y="294" width="11" height="33" fill="#BFE5ED"/>
      {Array.from({length:6},(_,i)=><rect key={i} x={144+i*30}
        y="377" width="22" height="17" fill="#1C4B61"/>)}
    </g>
    <rect x="24" y="174" width="18" height="401" fill="#A9C4CD"/>
    <g opacity={1-gate*.93} transform={`translate(${gate*37} 0)`}>
      <rect x="443" y="176" width="19" height="396" fill="#9EBAC5" stroke="#DAF4F7" strokeWidth="2"/>
    </g>
    {gate>.02&&<path d="M462 315 H489" stroke={GOLD} strokeWidth="7" strokeDasharray="12 9" opacity={gate}/>}
    {/* Duto sai do nível alto e termina no fundo da câmara, controlado por válvula. */}
    <path d="M535 365 V608 H332 V570" fill="none"
      stroke="#152D40" strokeWidth="45" strokeLinejoin="round" strokeLinecap="round"/>
    <path d="M535 365 V608 H332 V570" fill="none"
      stroke="#7899A9" strokeWidth="30" strokeLinejoin="round" strokeLinecap="round"/>
    <path d="M535 365 V608 H332 V570" fill="none"
      stroke={beam} strokeWidth="14" strokeDasharray="22 24"
      strokeDashoffset={-t*86} opacity={isFlow?1:.22}/>
    <circle cx="535" cy="458" r={state==='water_enter'?43:32}
      fill="#0A2939" stroke={isFlow?GOLD:'#B7D4DC'} strokeWidth="6"/>
    <path d="M516 438 L554 476 M516 476 L554 438"
      fill="none" stroke={isFlow?GOLD:'#D7E7ED'} strokeWidth="7" strokeLinecap="round"/>
    {state==='rise'&&<g opacity={.55+.3*Math.sin(t*5)}>
      <path d={`M80 ${waterY+10} V${waterY-122}`} stroke={GOLD} strokeWidth="9" strokeDasharray="13 10"/>
      <path d={`M61 ${waterY-97} L80 ${waterY-132} L99 ${waterY-97}Z`} fill={GOLD}/>
    </g>}
    {state==='equalize'&&<path d="M43 254 H589" stroke={GOLD}
      strokeWidth="5" strokeDasharray="12 13" opacity=".62"/>}
    <text x="531" y="664" textAnchor="middle" fontSize="22" fontWeight="850"
      fill={isFlow?GOLD:OFF}>VÁLVULA</text>
    <text x="260" y="662" textAnchor="middle" fontSize="20"
      fill={MUTED}>CONDUTO INFERIOR</text>
  </Base>;
};
