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

const Beam:React.FC<{d:string;progress:number;color?:string}>=({d,progress,color=AQUA})=>
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

export const OpticalPortrait:React.FC<OpticalPortraitProps>=({t,source,mask,mirrors,resist})=>
  <Base name="Mecanismo vertical nativo: fonte EUV, máscara refletora, espelhos e wafer em sequência causal">
    {/* A composição nativa não depende de recortar títulos de um SVG maior. */}
    <circle cx="120" cy="125" r="92" fill={GOLD} opacity=".045"/>
    <circle cx="112" cy="126" r={44+source*5} fill="#12374D" stroke="#84BED0" strokeWidth="3"/>
    {Array.from({length:12},(_,i)=>{
      const a=i*Math.PI/6+t*.85;
      return <path key={i}
        d={'M'+(112+Math.cos(a)*34)+' '+(126+Math.sin(a)*34)+' L'+
          (112+Math.cos(a)*(43+source*7))+' '+(126+Math.sin(a)*(43+source*7))}
        stroke={GOLD} strokeWidth="4" opacity={.45+.5*source}/>;
    })}
    <circle cx="112" cy="126" r={9+source*3} fill={GOLD}/>
    <text x="112" y="200" fill={OFF} textAnchor="middle" fontSize="24" fontWeight="850">LUZ EUV</text>
    <text x="112" y="229" fill={MUTED} textAnchor="middle" fontSize="18">FONTE</text>
    <Beam d="M166 126 H320" color={GOLD} progress={source}/>

    {/* Máscara grande e legível, com padrões que a luz transporta. */}
    <path d="M322 73 H559 L568 91 H332Z" fill="#668EA5" opacity=".7"/>
    <rect x="328" y="89" width="230" height="150" rx="10" fill="#102C40"
      stroke={mask>.05?GOLD:'#5B8298'} strokeWidth="5"/>
    <rect x="344" y="104" width="199" height="120" rx="4" fill="#061924" stroke="#61899D" strokeWidth="2"/>
    {Array.from({length:7},(_,i)=><rect key={i} x={355+i*26} y="118"
      width={i%3===1?13:17} height="90" rx="2"
      fill={i%3===1?'#3E7587':GOLD} opacity={.22+.78*mask}/>)}
    <text x="443" y="272" textAnchor="middle" fontWeight="850" fontSize="25" fill={OFF}>MÁSCARA</text>
    <text x="443" y="299" textAnchor="middle" fontSize="18" fill={MUTED}>REFLEXIVA</text>
    <Beam d="M450 241 L490 365" progress={mask}/>

    {/* Feixe segue caminho demonstrativo; não reivindica escala óptica real. */}
    <ellipse cx="489" cy="388" rx="99" ry="24" transform="rotate(-25 489 388)"
      fill="url(#portrait-mirror)" stroke="#C1F6F5" strokeWidth="4"/>
    <ellipse cx="489" cy="388" rx="69" ry="10" transform="rotate(-25 489 388)"
      fill="#7CD5DF" opacity={.2+.4*mirrors}/>
    <text x="489" y="463" textAnchor="middle" fontWeight="850" fontSize="24" fill={OFF}>ESPELHOS</text>
    <text x="489" y="490" textAnchor="middle" fontSize="18" fill={MUTED}>ÓPTICOS</text>
    <Beam d="M454 414 L293 542" progress={mirrors}/>

    {/* Wafer ocupa a largura principal; a exposição realmente muda o padrão. */}
    <ellipse cx="281" cy="567" rx="202" ry="66" fill="#06131D" opacity=".68"/>
    <path d="M80 564 Q87 640 281 640 Q477 640 482 564 L482 588 Q460 649 281 649 Q104 649 80 588Z"
      fill="url(#portrait-steel)" stroke="#B3E4EB" strokeWidth="3"/>
    <ellipse cx="281" cy="551" rx="201" ry="56" fill="#143B52" stroke="#CCF6F7" strokeWidth="4"/>
    <ellipse cx="281" cy="551" rx="180" ry="45" fill="none" stroke="#5FAFC2" strokeWidth="2" opacity=".67"/>
    {Array.from({length:7},(_,i)=><rect key={i} x={140+i*39}
      y={540+(i%2)*6} width="23" height="24" rx="2" fill={GOLD} opacity={resist*.85}/>)}
    <text x="281" y="678" textAnchor="middle" fontWeight="850" fontSize="22" fill={OFF}>CAMADA FOTOSSENSÍVEL</text>
  </Base>;

export const LockPortrait:React.FC<LockPortraitProps>=({t,fill,open,isFlow,state})=>{
  const waterY=460-210*clamp(fill);
  const boatY=waterY-13;
  const bright=isFlow?GOLD:AQUA;
  const showGate=clamp(open);
  return <Base name="Mecanismo vertical nativo de eclusa: reservatório elevado, válvula, galeria inferior, água da câmara e navio flutuante">
    <text x="24" y="45" fill={MUTED} fontSize="19" fontWeight="750">CÂMARA</text>
    <text x="435" y="45" fill={GOLD} fontSize="19" fontWeight="850">LADO ALTO</text>
    <path d="M25 58 H598" stroke="#48697B" strokeWidth="2"/>
    {/* Níveis separados, tubulação visível, portão fechado até equalizar. */}
    <rect x="30" y="154" width="357" height="375" fill="#071A28" stroke="#526F80" strokeWidth="3"/>
    <rect x="438" y="211" width="143" height="318" fill="#0D2738" stroke="#668A9C" strokeWidth="3"/>
    <rect x="447" y="249" width="124" height="280" fill="url(#portrait-water)" opacity=".87"/>
    <path d="M447 249 H571" stroke="#D8FFFF" strokeWidth="5"/>
    <g>
      <rect x="34" y={waterY} width="349" height={529-waterY} fill="url(#portrait-water)" opacity=".97"/>
      <path d={'M34 '+waterY+' H383'} stroke="#D3FFFF" strokeWidth="5"/>
      {Array.from({length:6},(_,i)=><path key={i}
        d={'M'+(47+i*54)+' '+(waterY+18+Math.sin(t*3+i)*2)+' h36'}
        stroke="#DDFBFA" opacity=".48" strokeWidth="3"/>)}
    </g>
    <path d="M30 530 H592" stroke="#8AA4B1" strokeWidth="10"/>
    {/* Navio acompanha estritamente a superfície da água. */}
    <g transform={'translate(0 '+(boatY-442)+')'}>
      <path d="M76 410 H341 L314 460 H109Z" fill="url(#portrait-steel)" stroke="#F1FCFF" strokeWidth="4"/>
      <path d="M97 450 H322" stroke="#638BA1" strokeWidth="5"/>
      <rect x="122" y="373" width="170" height="36" rx="2" fill="#DCECF0" stroke="#A0C6D2" strokeWidth="2"/>
      <rect x="147" y="340" width="115" height="31" fill="#E8F5F4"/>
      <rect x="176" y="314" width="11" height="26" fill="#B8DDE3"/>
      {Array.from({length:5},(_,i)=><rect key={i} x={130+31*i} y="386" width="24" height="15"
        fill="#26576A" stroke="#567E91" strokeWidth="1"/>)}
    </g>
    <rect x="27" y="150" width="17" height="387" fill="#94AFBB"/>
    <g opacity={1-showGate*.9} transform={'translate('+(showGate*24)+' 0)'}>
      <rect x="385" y="154" width="20" height="380" fill="#A2BBC4" stroke="#E3F3F5" strokeWidth="2"/>
    </g>
    {open>.03&&<path d="M403 295 H443" stroke={GOLD} strokeWidth="7"
      strokeDasharray="11 9" opacity={open}/>}
    {/* Água passa POR BAIXO: trajeto a partir do reservatório elevado. */}
    <path d="M525 375 V574 H289 V527" fill="none" stroke="#182F40"
      strokeWidth="38" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M525 375 V574 H289 V527" fill="none" stroke="#7C9FAF"
      strokeWidth="25" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M525 375 V574 H289 V527" fill="none" stroke={bright}
      strokeWidth="12" strokeLinecap="round" strokeLinejoin="round"
      strokeDasharray="23 23" strokeDashoffset={-t*81} opacity={isFlow?1:.28}/>
    <circle cx="525" cy="460" r="28" fill="#123044" stroke={isFlow?GOLD:'#B8D5DA'} strokeWidth="5"/>
    <path d="M510 445 L540 475 M510 475 L540 445" fill="none"
      stroke={isFlow?GOLD:'#CFDFE3'} strokeWidth="6" strokeLinecap="round"/>
    <text x="525" y="633" textAnchor="middle" fill={GOLD} fontSize="22" fontWeight="850">VÁLVULA</text>
    <text x="282" y="627" textAnchor="middle" fill={MUTED} fontSize="20">ENTRADA PELO FUNDO</text>
    <text x="24" y="672" fill={OFF} fontSize="17" fontWeight="720">
      {state==='release'?'SAÍDA APÓS EQUALIZAÇÃO':'O NAVIO SOBE COM A ÁGUA'}
    </text>
  </Base>;
};
