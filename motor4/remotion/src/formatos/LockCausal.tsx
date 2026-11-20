/** Eclusa causal: domínio hidráulico isolado, cronologia fornecida pelo storyboard.
 * Nunca representa registro real; desenha a relação água -> nível -> navio -> equalização.
 * O enquadramento e as etapas não dependem de segundos fixos do episódio.
 */
import React from 'react';
import {AbsoluteFill,Img,staticFile} from 'remotion';
import {LockImmersive} from './MechanismsImmersive';

export type EventoEclusa = {
  at: number;
  action?: 'closed' | 'water_enter' | 'rise' | 'equalize' | 'release';
  label: string;
};
type Props = { t: number; events: EventoEclusa[]; referenceAsset?: string; visualMode?: 'legacy'|'editorial'|'portrait' };
const GOLD='#FFD21F';
const ease=(v:number)=>{const x=Math.max(0,Math.min(1,v));return x*x*(3-2*x);};


/** Camada visual editorial. Usa as mesmas variáveis hidráulicas calculadas pelo
 * LockCausal, sem refazer lógica nem interferir nas versões publicadas/legadas.
 */
const EditorialCutaway:React.FC<{
  t:number;fill:number;open:number;isFlow:boolean;active?:EventoEclusa
}>=({t,fill,open,isFlow,active})=>{
  // Dois níveis VISÍVEIS, conectados pelo mesmo tubo. A água é o elevador;
  // nenhum motor ergue o casco. Somente a direção de enchimento é ilustrada.
  const high=939,low=1252;
  const waterY=low-(low-high)*fill;
  const wave=Math.sin(t*3.2)*1.4;
  const level=waterY+wave;
  const state=active?.action||'closed';
  const steps=['closed','water_enter','rise','equalize','release'];
  const index=Math.max(0,steps.indexOf(state));
  const showGravity=isFlow && index>=1;
  const GOLD='#FFD21F',WHITE='#F5F2EB',CYAN='#6DE1E9',MUTED='#ABC3D0';
  const hullShift=level-1064;
  const travel=ease((open-.25)/.75)*62;
  const detail=state==='closed'?'DOIS LADOS COM NÍVEIS DIFERENTES':
    state==='water_enter'?'A GRAVIDADE LEVA A ÁGUA AO FUNDO':
    state==='rise'?'O NAVIO FLUTUA E SOBE COM A ÁGUA':
    state==='equalize'?'O DESNÍVEL ENTRE OS LADOS DESAPARECE':
    'O NAVIO PODE PASSAR PARA O LADO ALTO';
  return <AbsoluteFill style={{
    background:'radial-gradient(ellipse at 49% 46%,#1B394D 0%,#0B1C2C 58%,#05101B 100%)',
    fontFamily:'Inter,Arial,sans-serif',overflow:'hidden'}}>
    <svg width="100%" height="100%" viewBox="0 0 1080 1920"
      role="img"
      aria-label="Corte ilustrativo: reservatório alto alimenta por gravidade um conduto inferior controlado por válvula; a água enche a câmara, eleva um navio flutuante e o portão só abre quando os níveis se igualam">
      <defs>
        <pattern id="lock-edit-grid" width="66" height="66" patternUnits="userSpaceOnUse">
          <path d="M66 0H0V66" fill="none" stroke="#6B98AE" strokeOpacity=".12" strokeWidth="1.2"/>
        </pattern>
        <linearGradient id="lock-edit-water" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="#9AF1EF"/><stop offset=".10" stopColor="#56CCDB"/>
          <stop offset=".58" stopColor="#21789A"/><stop offset="1" stopColor="#0A3957"/>
        </linearGradient>
        <linearGradient id="lock-edit-metal" x1="0" y1="0" x2="1" y2="0">
          <stop stopColor="#243B4B"/><stop offset=".38" stopColor="#B7D5D8"/>
          <stop offset=".77" stopColor="#6E96A7"/><stop offset="1" stopColor="#274051"/>
        </linearGradient>
        <linearGradient id="lock-edit-hull" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="#FEFFFF"/><stop offset=".52" stopColor="#C6D7DC"/>
          <stop offset="1" stopColor="#658B9C"/>
        </linearGradient>
        <clipPath id="lock-edit-chamber"><rect x="136" y="723" width="596" height="693"/></clipPath>
      </defs>
      <rect width="1080" height="1920" fill="url(#lock-edit-grid)"/>
      <circle cx="540" cy="1060" r="450" fill="#235E77" opacity=".09"/>

      <text x="68" y="431" fill={MUTED} fontSize="28" fontWeight="850" letterSpacing="3">MECANISMO · CORTE TRANSVERSAL</text>
      <text x="68" y="506" fill={WHITE} fontSize="60" fontWeight="900">DE ONDE VEM A ÁGUA</text>
      <text x="68" y="569" fill={WHITE} fontSize="60" fontWeight="900">QUE LEVANTA O NAVIO?</text>
      <path d="M66 600 H1014" stroke="#496E80" strokeWidth="2"/>

      {/* Fato físico central: água elevada à direita, câmara mais baixa à esquerda. */}
      <rect x="140" y="744" width="597" height="672" fill="#051727"/>
      <path d="M736 904 H1023 V1435 H736Z" fill="#172C3C" stroke="#607F8F" strokeWidth="3"/>
      <rect x="814" y={high} width="213" height={1416-high} fill="url(#lock-edit-water)"/>
      <path d={'M814 '+high+' H1027'} stroke="#CAFFFA" strokeWidth="7"/>
      <path d={'M141 '+low+' H732'} stroke="#9BC2D0" strokeWidth="3" strokeDasharray="16 15" opacity=".26"/>

      {/* O indicador não é uma medida em metros, apenas comparação dos níveis. */}
      <text x="833" y="842" fill={GOLD} fontSize="31" fontWeight="900">NÍVEL</text>
      <text x="833" y="882" fill={GOLD} fontSize="31" fontWeight="900">MAIS ALTO</text>
      <path d="M930 897 V925" stroke={GOLD} strokeWidth="5"/>
      <path d="M916 913 L930 933 944 913 Z" fill={GOLD}/>
      <text x="148" y="705" fill={MUTED} fontSize="27" fontWeight="850" letterSpacing="2.1">CÂMARA DA ECLUSA</text>

      {/* Água da câmara: sobe SOMENTE depois de a válvula ser acionada. */}
      <g clipPath="url(#lock-edit-chamber)">
        <rect x="137" y={level} width="596" height={1416-level} fill="url(#lock-edit-water)"/>
        <path d={'M137 '+level+' H733'} stroke="#D1FFFF" strokeWidth="7"/>
        {Array.from({length:10},(_,i)=><g key={i}>
          <path d={'M'+(150+i*60)+' '+(level+17+Math.sin(t*3+i)*3)+' h37'}
            stroke="#BEF8FA" strokeWidth="3.5" opacity=".35"/>
          <path d={'M'+(158+i*58)+' '+(level+53+i%3*25)+' h18'}
            stroke="#D8FCFA" strokeWidth="2" opacity=".12"/>
        </g>)}
      </g>

      {/* Navio acompanha imediatamente a superfície: não é içado. */}
      <g transform={'translate('+travel+' '+hullShift+')'}>
        <path d="M221 1002 H674 L636 1092 H266Z"
          fill="#112432" opacity=".35" transform="translate(0 14)"/>
        <path d="M216 1000 H680 L641 1092 H263Z"
          fill="url(#lock-edit-hull)" stroke="#F3FFFF" strokeWidth="5"/>
        <path d="M247 1073 H644" stroke="#628B9C" strokeWidth="9"/>
        <rect x="339" y="946" width="246" height="55" rx="3"
          fill="#F1F7F4" stroke="#8DABB5" strokeWidth="3"/>
        <rect x="381" y="907" width="158" height="37" rx="3" fill="#E0EAE9"/>
        <rect x="451" y="867" width="13" height="41" fill="#B3D0D5"/>
        {Array.from({length:5},(_,i)=><rect key={i} x={350+i*45} y="964"
          width="26" height="19" rx="3" fill="#235573"/>)}
      </g>
      {/* Primeiro vê-se o barco, depois o movimento vertical acompanhado. */}
      {fill>.02 && <g>
        <path d={'M191 '+(low-22)+' V'+(level+10)} stroke={GOLD} strokeWidth="7" strokeDasharray="15 12"/>
        <path d={'M173 '+(level+24)+' L191 '+(level-10)+' L209 '+(level+24)+'Z'} fill={GOLD}/>
      </g>}

      {/* Barreira sólida: os portões permanecem fechados enquanto há desnível. */}
      <rect x="101" y="741" width="38" height="695" fill="url(#lock-edit-metal)"/>
      <g transform={'translate('+(open*40)+' 0)'} opacity={1-open*.92}>
        <rect x="734" y="747" width="46" height="686" fill="url(#lock-edit-metal)"
          stroke="#C2D9DB" strokeWidth="2"/>
        <path d="M755 772 V1390" stroke="#2C4556" strokeWidth="4"/>
      </g>
      {open>.03 && <g opacity={open}>
        <path d="M757 931 H838" stroke={GOLD} strokeWidth="7" strokeDasharray="11 10"/>
        <path d="M824 914 L849 931 824 949 Z" fill={GOLD}/>
      </g>}
      <path d="M99 1426 H1032" stroke="#67889C" strokeWidth="20"/>

      {/* O tubo tem origem VISÍVEL no reservatório elevado e desemboca embaixo da câmara. */}
      <path d="M944 1130 V1364 H632 V1331 H563" stroke="#182E3D"
        fill="none" strokeWidth="55" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M944 1130 V1364 H632 V1331 H563" stroke="#618594"
        fill="none" strokeWidth="37" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M944 1130 V1364 H632 V1331 H563" stroke={showGravity?CYAN:'#68899C'}
        fill="none" strokeWidth="17" strokeLinecap="round" strokeLinejoin="round"
        strokeDasharray="26 29" strokeDashoffset={-t*117} opacity={showGravity?1:.28}/>
      {isFlow&&<g>
        <path d="M922 1303 L944 1332 L966 1303" stroke={GOLD} strokeWidth="5"
          fill="none" strokeLinecap="round"/>
        <path d="M842 1347 L813 1364 L842 1381" stroke={GOLD}
          strokeWidth="5" fill="none" strokeLinecap="round"/>
        <path d="M645 1321 L615 1338 L645 1355" stroke={GOLD}
          strokeWidth="5" fill="none" strokeLinecap="round"/>
      </g>}
      {/* Animação do comando da VÁLVULA, imediatamente perceptível. */}
      <circle cx="944" cy="1225" r="34" fill="#0B2635"
        stroke={showGravity?GOLD:'#8FB3C0'} strokeWidth="6"/>
      <path d={'M922 1203 L966 1247 M922 1247 L966 1203'} stroke={showGravity?GOLD:'#B8CFD5'}
        strokeWidth="8" strokeLinecap="round" opacity={showGravity?0.25:1}/>
      {showGravity&&<circle cx="944" cy="1225" r="46" stroke={GOLD}
        strokeWidth="3" fill="none" opacity={.35+.22*Math.sin(t*6)}/>}
      <text x="816" y="1282" fill={showGravity?GOLD:WHITE}
        fontSize="27" fontWeight="900">VÁLVULA</text>
      <text x="1010" y="1446" textAnchor="end" fill={showGravity?GOLD:MUTED}
        fontSize="24" fontWeight="850">ÁGUA POR GRAVIDADE</text>
      <path d="M71 1496 H1010" stroke="#4D7284" strokeWidth="2"/>

      {/* Texto só conclui o que já está sendo visto. */}
      <text x="72" y="1554" fill={GOLD} fontSize="31" fontWeight="900">
        {String(index+1).padStart(2,'0')+'  /  '+(active?.label||'PORTÕES FECHADOS').replace(/^[0-9]+\s*·\s*/,'')}
      </text>
      <text x="72" y="1609" fill={WHITE} fontSize="26" fontWeight="700">{detail}</text>
      <g transform="translate(75 1641)">
        {steps.map((a,i)=><rect key={a} x={i*192} width="172" height="7"
          fill={index>=i?GOLD:'#36576B'}/>)}
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
  if(visualMode==='portrait') return <LockImmersive t={t} fill={fill} open={open} isFlow={isFlow} state={state}/>;
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
