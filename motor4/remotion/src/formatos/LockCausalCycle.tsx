/** Uma eclusa como SEQUÊNCIA CAUSAL, não um efeito isolado.
 * Demonstração simplificada de um ciclo de subida, em corte longitudinal.
 * Entrada/fecho/valvulas/gravidade/subida/equalização/abertura/saída.
 * O motor NÃO finge que é registro filmado nem que cada portão
 * move-se verticalmente: abertura é indicada na vista lateral.
 *
 * Os tempos vêm das ações do storyboard, nunca de segundos do tema.
 */
import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';

export type LockCycleAction =
  'enter' | 'seal' | 'valves' | 'rise' | 'equalize' | 'open' | 'exit';
export type LockCycleCue = {
  at: number;
  action?: LockCycleAction | string;
  label: string;
};
type Props = {t: number; events: LockCycleCue[]; referenceAsset?: string; duration?:number};

const YLOW=1110, YHIGH=817, YFLOOR=1335;
const INLET_X=288, OUTLET_X=748;
const GOLD='#FFD21F', WHITE='#F6F4EC', CYAN='#75DDEB';
const clamp=(x:number)=>Math.max(0,Math.min(1,x));
const ease=(x:number)=>{const y=clamp(x);return y*y*(3-2*y);};

export const LockCausalCycle: React.FC<Props> = ({t,events,referenceAsset,duration}) => {
  const find=(action:LockCycleAction,fallback:number) =>
    events.find(e=>e.action===action)?.at ?? fallback;
  const timeline = {
    enter:find('enter',0), seal:find('seal',2.6), valves:find('valves',4.6),
    rise:find('rise',6.1), equalize:find('equalize',12.2),
    open:find('open',14), exit:find('exit',15.6),
  };
  const entry=ease((t-timeline.enter-.15)/Math.max(.5,timeline.seal-timeline.enter-.5));
  const seal=ease((t-timeline.seal)/1.1);
  const flowOn=ease((t-timeline.valves)/.65)*(1-ease((t-timeline.equalize)/.65));
  const raise=ease((t-timeline.rise)/Math.max(1,timeline.equalize-timeline.rise-.1));
  const gateOpen=ease((t-timeline.open)/1.1);
  const travel=ease((t-timeline.exit)/Math.max(.8,(duration ?? 17.35)-timeline.exit));
  const shipX=180+309*entry+442*travel;
  const waterY=YLOW-(YLOW-YHIGH)*raise;
  const isFilling=flowOn>.01;
  const current=events.filter(e=>e.at<=t).slice(-1)[0] || events[0];
  const step=Math.max(0,events.indexOf(current));
  const flowDash=-t*72;
  const blend=referenceAsset?ease(t/.8):1;

  return <AbsoluteFill style={{background:'#091524'}}>
    {/* Ponte honesta: 1 último quadro do mesmo master em vez de uma tomada falsa. */}
    {referenceAsset && t<.8 && <Img src={staticFile(referenceAsset)}
      style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover',
        objectPosition:'50% 48%',transform:'scale(1.1)',
        transformOrigin:'50% 30%',filter:'brightness(.98) saturate(1.04)'}}/>}
    {referenceAsset && t<.8 && <AbsoluteFill style={{opacity:1-blend,
      background:'linear-gradient(180deg,rgba(3,8,16,.55) 0%,rgba(3,8,16,.08) 21%,rgba(3,8,16,.03) 48%,rgba(3,8,16,.58) 72%,#050A12 100%)'}}/>}
    <AbsoluteFill style={{opacity:blend,
      background:'radial-gradient(ellipse at 50% 45%,#1B3649 0%,#091625 76%,#050D17 100%)'}}>
      <svg viewBox="0 0 1080 1920" width="100%" height="100%"
        style={{fontFamily:'Inter,Arial,sans-serif'}}
        role="img" aria-label="Ilustração longitudinal simplificada de eclusa: entrada, fechamento, fluxo por gravidade, elevação, equalização, abertura do portão superior e saída">
        <defs>
          <linearGradient id="cycleWater" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#83E6E8"/>
            <stop offset=".18" stopColor="#329DB5"/>
            <stop offset="1" stopColor="#0D4A70"/>
          </linearGradient>
          <linearGradient id="cycleWall" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#4C6775"/>
            <stop offset=".52" stopColor="#A8B8BC"/>
            <stop offset="1" stopColor="#385667"/>
          </linearGradient>
          <linearGradient id="cycleHull" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#F2F4F0"/>
            <stop offset=".42" stopColor="#C5D0D5"/>
            <stop offset="1" stopColor="#647D8B"/>
          </linearGradient>
          <pattern id="cycleGrid" width="60" height="60" patternUnits="userSpaceOnUse">
            <path d="M60 0H0V60" fill="none" stroke="#82A6B7" strokeOpacity=".12" strokeWidth="1.3"/>
          </pattern>
          <pattern id="cycleConcrete" width="35" height="32" patternUnits="userSpaceOnUse">
            <path d="M0 30 L35 30 M34 0 L34 32" fill="none" stroke="#273B46" strokeOpacity=".35" strokeWidth="1.6"/>
          </pattern>
          <clipPath id="cycleChamberClip"><rect x={INLET_X+14} y="720" width={OUTLET_X-INLET_X-28} height={YFLOOR-720}/></clipPath>
          <clipPath id="cycleMapClip"><rect x="61" y="715" width="957" height="785"/></clipPath>
        </defs>
        <rect width="1080" height="1920" fill="url(#cycleGrid)"/>

        {/* Tipografia é secundária: a câmara ocupa o centro da tela. */}
        <text x="75" y="448" fill="#9CC0CC" fontSize="26" fontWeight="800" letterSpacing="2.8">PRINCÍPIO FÍSICO · VISTA LATERAL SIMPLIFICADA</text>
        <text x="74" y="511" fill={WHITE} fontSize="55" fontWeight="900">COMO UM NAVIO SOBE?</text>
        <path d="M77 538 H1003" stroke="#54798B" strokeWidth="2"/>
        <text x="98" y="662" fill="#ADC0CC" fontSize="25" fontWeight="800">CANAL INFERIOR</text>
        <text x="375" y="662" fill="#F3F5F4" fontSize="25" fontWeight="800">CÂMARA</text>
        <text x="808" y="662" fill={CYAN} fontSize="25" fontWeight="800">NÍVEL ALTO</text>

        {/* Seção longitudinal completa: duas cotas diferentes e câmara entre portões. */}
        <g clipPath="url(#cycleMapClip)">
          <path d="M60 750 H287 V1335 H748 V720 H1018 V1372 H60Z" fill="#253D4C"/>
          <path d="M60 738 H287 V1353 H748 V704 H1018" fill="none" stroke="#6E8B97" strokeWidth="12"/>
          <rect x="74" y={YLOW} width={INLET_X-74} height={YFLOOR-YLOW} fill="url(#cycleWater)" opacity=".9"/>
          <rect x={OUTLET_X} y={YHIGH} width={1004-OUTLET_X} height={YFLOOR-YHIGH} fill="url(#cycleWater)" opacity=".94"/>
          <rect x={INLET_X+9} y="708" width={OUTLET_X-INLET_X-18} height={YFLOOR-708} fill="#061625"/>
          <g clipPath="url(#cycleChamberClip)">
            <rect x={INLET_X+10} y={waterY} width={OUTLET_X-INLET_X-20} height={YFLOOR-waterY} fill="url(#cycleWater)" opacity=".96"/>
            <path d={'M'+(INLET_X+10)+' '+waterY+' H'+(OUTLET_X-10)} stroke="#D2FFFF" strokeWidth="5"/>
            {Array.from({length:5},(_,i)=><path key={i}
              d={'M'+(INLET_X+23+i*88)+' '+(waterY+21+Math.sin(t*5+i)*3)+' h49'}
              stroke="#C1F6F5" strokeWidth="3" opacity=".52"/>)}
            {isFilling && Array.from({length:5},(_,i)=><g key={i}
              transform={'translate('+(346+i*76)+','+(1308-(t-timeline.rise)*((18+i*5)%32))+')'}
              opacity={.25+.45*flowOn}>
              <circle cx="0" cy="0" r={6+i%3*2} fill="#B8FFF4"/>
            </g>)}
          </g>

          {/* A imagem física correta: a água alta de jusante não atravessa os portões.
              A vazão entra por condutos internos quando as válvulas abrem. */}
          <path d="M947 1030 V1390 H352 V1313" stroke="#607F8F" strokeWidth="40"
            fill="none" strokeLinecap="square"/>
          <path d="M947 1030 V1390 H352 V1313" stroke="#061928" strokeWidth="23"
            fill="none" strokeLinecap="square"/>
          {isFilling && <path d="M947 1030 V1390 H352 V1313" stroke="#FFD21F" strokeWidth="9"
            strokeDasharray="18 27" strokeDashoffset={flowDash} opacity={.42+.42*flowOn}
            fill="none"/>}
          <path d="M349 1329 V1290 M505 1390 V1305 M646 1390 V1305" stroke="#6FD7E8"
            strokeWidth="12" opacity={.5+.45*flowOn}/>
          <path d="M815 1390 l28 -27 v54Z" fill={isFilling?GOLD:'#6E8393'}/>
          <circle cx="807" cy="1390" r="18" fill="#102839" stroke={isFilling?GOLD:'#A2B5BC'} strokeWidth="5"/>
          <path d={'M795 '+(1390+(isFilling?0:-11))+' l24 '+(isFilling?0:22)}
            stroke={isFilling?GOLD:'#D4DEE1'} strokeWidth="5" opacity=".9"/>
          <text x="678" y="1452" fill={isFilling?GOLD:'#A6BDC7'} fontSize="28" fontWeight="800">ÁGUA POR GRAVIDADE</text>
          {/* Fundo/contorno da câmara com paredes e portões independentes. */}
          <rect x="268" y="727" width="22" height="619" fill="url(#cycleWall)"/>
          <rect x="749" y="704" width="22" height="650" fill="url(#cycleWall)"/>
          <rect x="280" y="1340" width="480" height="24" fill="url(#cycleWall)"/>
          <rect x="280" y="1340" width="480" height="24" fill="url(#cycleConcrete)" opacity=".55"/>

          {/* Portões miter ilustrados na lateral como barreira opaca/tracejada:
              a abertura real se dá em planta, não como elevador vertical. */}
          <rect x="291" y="786" width="16" height="547" fill="#DDE1DE" opacity={seal*.93+(1-seal)*.08}/>
          <path d="M299 790 V1331" stroke={seal?'#BBD8DF':'#A3C3CF'}
            strokeWidth="4" strokeDasharray={seal?'0':'12 13'} opacity=".7"/>
          <rect x="736" y="780" width="18" height="550" fill="#DDE1DE" opacity={1-.92*gateOpen}/>
          <path d="M745 786 V1328" stroke={gateOpen>0.6?GOLD:'#A8CBD2'}
            strokeWidth="4" strokeDasharray={gateOpen>0.6?'16 10':'0'} opacity=".7"/>

          {/* O navio flutua continuamente: subida Y tem MESMA curva da água. */}
          <g transform={'translate('+(shipX-480)+','+(waterY-YLOW)+')'}>
            <g filter="drop-shadow(0px 8px 6px rgba(3,9,15,.5))">
              <path d="M353 1035 H608 L573 1130 H395Z" fill="url(#cycleHull)" stroke="#EDF5F5" strokeWidth="4"/>
              <path d="M377 1100 H584" stroke="#356C84" strokeWidth="8"/>
              <path d="M389 1023 H568" stroke="#90AFBC" strokeWidth="5"/>
              <rect x="404" y="980" width="131" height="52" fill="#F1F3EE" stroke="#728E9F" strokeWidth="3"/>
              <rect x="428" y="951" width="89" height="27" fill="#D5E4E7" stroke="#7F9AA7" strokeWidth="2"/>
              <path d="M481 918 V950" stroke="#C6E1E6" strokeWidth="10"/>
              {Array.from({length:5},(_,i)=><rect key={i} x={419+i*22} y="999" width="14" height="13"
                rx="2" fill="#235574"/>)}
              {Array.from({length:6},(_,i)=><rect key={i} x={399+i*27} y="1046" width="16" height="9"
                rx="2" fill="#456E83"/>)}
            </g>
          </g>

          {/* Guia de cotejo: o mesmo nível que move a água move o casco. */}
          {raise>.03 && raise<.98 && <g>
            <path d={'M589 '+YLOW+' V'+waterY} stroke={GOLD} strokeWidth="5"
              strokeDasharray="11 12" opacity=".72"/>
            <path d={'M576 '+(waterY+15)+' l13 -22 13 22Z'} fill={GOLD}/>
            <text x="572" y="1239" fontSize="25" fill={GOLD} fontWeight="800">SOBE</text>
          </g>}
        </g>

        <path d={'M89 '+YLOW+' H268'} stroke="#C3F2F5" strokeWidth="4" strokeDasharray="10 8" opacity=".75"/>
        <path d={'M770 '+YHIGH+' H997'} stroke="#C3F2F5" strokeWidth="4" strokeDasharray="10 8" opacity=".85"/>

        {/* Status: ações da animação, não cartões decorativos gigantes. */}
        <path d="M75 1536 H1005" stroke="#557384" strokeWidth="2"/>
        <text x="79" y="1514" fill="#AAC2CD" fontSize="27" letterSpacing="2.3" fontWeight="800">
          {'ETAPA '+String(step+1).padStart(2,'0')+' / '+String(events.length).padStart(2,'0')}
        </text>
        <text x="78" y="1604" fill={WHITE} fontSize="43" fontWeight="900">
          {current?.label || 'ENTRADA NA CÂMARA'}
        </text>
        {events.map((e,i)=><rect key={e.action || i} x={78+i*133} y="1636" height="8" width="117"
          fill={i<=step?GOLD:'#344F62'}/>)}
        <text x="78" y="1718" fill="#96B4C0" fontSize="23">
          ILUSTRAÇÃO DO PRINCÍPIO · DISTÂNCIAS FORA DE ESCALA
        </text>
        <text x="78" y="1770" fill="#8CA8B8" fontSize="21">
          FONTES: AUTORIDADE DO CANAL DO PANAMÁ · ESQUEMA PRÓPRIO
        </text>
      </svg>
    </AbsoluteFill>
  </AbsoluteFill>;
};
