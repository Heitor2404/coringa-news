/** PROVA PRIVADA A — uma família física, dois assuntos a partir de dados.
 * Piston, rod and crank all computed by SliderCrankRig, not independently
 * keyframed. Illustration is original and explanatory, not an animation
 * copied from the web. Not a production renderer.
 */
import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import specs from './slider-crank-proofs.json';
import {angleAt,rigState,type RigGeometry,type RigState} from './SliderCrankRig';
import {semanticCamera2D,ease} from './MechanismCamera2D';

type Focus='piston'|'rod'|'crank'|'intake'|'outlet';
type Driver='pressure'|'shaft';
type Step={at:number;label:string;detail:string;focus:Focus};
type Model={
 id:string;title:[string,string];subtitle:string;section:string;
 driver:Driver;ports:boolean;accent:string;geometry:RigGeometry;
 steps:Step[];footer:string;
};
type Props={kind:'motor'|'compressor';duracao?:number;private_review_only?:boolean};

const C={
 ink:'#031F36',navy:'#061B32',water:'#167AA2',white:'#F8FEFF',
 teal:'#50E8E4',yellow:'#FFD21F',cream:'#E6FCFC',steel:'#9FCED8',
 orange:'#FFAC4F',bronze:'#BB7137'
};
const smooth=(v:number)=>{const x=Math.max(0,Math.min(1,v));return x*x*(3-2*x);};
const focusAnchor=(focus:Focus,s:RigState,g:RigGeometry):{x:number;y:number}=>{
  if(focus==='piston')return {x:g.centerX,y:s.pistonPin.y-44};
  if(focus==='rod')return {
    x:(s.pistonPin.x+s.crankPin.x)/2,
    y:(s.pistonPin.y+s.crankPin.y)/2
  };
  if(focus==='crank')return {x:g.centerX,y:g.centerY};
  if(focus==='intake')return {x:406,y:580};
  return {x:590,y:580};
};
const colors=(mode:Driver)=>mode==='pressure'?
 {main:'#FFBC5C',glow:'#FFE18F',cold:'#78F4F5'}:
 {main:'#60E9D9',glow:'#B3FEED',cold:'#60E9D9'};

const SVGText:React.FC<{
 x:number;y:number;children:React.ReactNode;size?:number;
 color?:string;weight?:number;anchor?:'start'|'middle'|'end';
 spacing?:number;
}>=({x,y,children,size=27,color=C.white,weight=850,anchor='start',spacing=0})=>
  <text x={x} y={y} fill={color} fontSize={size} textAnchor={anchor}
    letterSpacing={spacing} fontFamily="Montserrat,Arial,sans-serif"
    fontWeight={weight}>{children}</text>;

const Defs:React.FC<{accent:string}>=({accent})=><defs>
  <linearGradient id="sc-bg" x1=".1" y1="0" x2=".9" y2="1">
    <stop stopColor="#06152D"/><stop offset=".44" stopColor="#0B436E"/>
    <stop offset=".78" stopColor="#145C82"/><stop offset="1" stopColor="#082440"/>
  </linearGradient>
  <radialGradient id="sc-stage" cx=".5" cy=".4" r=".7">
    <stop stopColor="#419EC2" stopOpacity=".8"/>
    <stop offset=".62" stopColor="#187A9C" stopOpacity=".52"/>
    <stop offset="1" stopColor="#071F3D" stopOpacity="0"/>
  </radialGradient>
  <linearGradient id="sc-frame" x1="0" y1="0" x2="1" y2=".8">
    <stop stopColor="#0B3A5D"/><stop offset=".34" stopColor="#4B839A"/>
    <stop offset=".56" stopColor="#174663"/><stop offset="1" stopColor="#092C50"/>
  </linearGradient>
  <linearGradient id="sc-steel" x1="0" x2="1" y1="0" y2="1">
    <stop stopColor="#EEFFFB"/><stop offset=".23" stopColor="#ADD9E2"/>
    <stop offset=".55" stopColor="#679AA9"/><stop offset="1" stopColor="#244E6D"/>
  </linearGradient>
  <linearGradient id="sc-piston" x1="0" x2="1" y1="0" y2=".4">
    <stop stopColor="#D9FFED"/><stop offset=".24" stopColor="#A4EFE7"/>
    <stop offset=".67" stopColor="#55A7C3"/><stop offset="1" stopColor="#296783"/>
  </linearGradient>
  <linearGradient id="sc-rod" x1="0" x2="1" y1="0" y2=".3">
    <stop stopColor="#FFF7BD"/><stop offset=".2" stopColor="#F6C46E"/>
    <stop offset=".63" stopColor="#DB923D"/><stop offset="1" stopColor="#8A4725"/>
  </linearGradient>
  <linearGradient id="sc-wheel" x1="0" x2="1" y1="0" y2="1">
    <stop stopColor="#62E7DF"/><stop offset=".45" stopColor="#2397B2"/>
    <stop offset="1" stopColor="#0A446A"/>
  </linearGradient>
  <linearGradient id="sc-gas" x1="0" x2=".7" y1="0" y2="1">
    <stop stopColor={accent} stopOpacity=".62"/>
    <stop offset=".6" stopColor={accent} stopOpacity=".28"/>
    <stop offset="1" stopColor={accent} stopOpacity=".03"/>
  </linearGradient>
  <filter id="sc-shadow" x="-25%" y="-25%" width="150%" height="160%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="12"/>
    <feOffset dx="0" dy="15" result="sh"/>
    <feComponentTransfer><feFuncA type="linear" slope=".32"/></feComponentTransfer>
    <feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <clipPath id="sc-chamber"><rect x="397" y="602" width="203" height="343" rx="6"/></clipPath>
</defs>;

const Arrow:React.FC<{x:number;y:number;direction:'down'|'up'|'right';opacity:number;
 color:string;scale?:number}>=({x,y,direction,opacity,color,scale=1})=>{
 const deg=direction==='down'?90:direction==='up'?-90:0;
 return <g opacity={opacity} transform={'translate('+x+' '+y+') rotate('+deg+') scale('+scale+')'}
   stroke={color} fill="none" strokeWidth="9" strokeLinecap="round" strokeLinejoin="round">
   <path d="M-48 0 H48"/><path d="M24 -20 L48 0 L24 20"/>
 </g>;
};

const GasParticles:React.FC<{
 t:number;top:number;energy:number;accent:string;
}>=({t,top,energy,accent})=>{
 const usable=Math.max(0,top-604);
 return <g clipPath="url(#sc-chamber)" opacity={Math.max(.16,energy)}>
  {Array.from({length:15},(_,i)=>{
    const fx=411+(i%5)*40+Math.sin(t*1.7+i)*7;
    const fy=610+(Math.floor(i/5)+.35)*usable/3+Math.cos(t*1.4+i)*4;
    return <circle key={i} cx={fx} cy={fy}
      r={4+(i%4)*1.7} fill={i%3===0?C.white:accent} opacity={.6+(i%4)*.09}/>;
  })}
 </g>;
};

const Cutaway:React.FC<{t:number;g:RigGeometry;mode:Driver;
 focus:Focus;ports:boolean;accent:string;duration:number}>=
 ({t,g,mode,focus,ports,accent,duration})=>{
  const theta=angleAt(t,duration-.38);
  const s=rigState(theta,g);
  const cc=colors(mode);
  const cx=g.centerX,cy=g.centerY;
  const activePiston=focus==='piston',activeRod=focus==='rod',activeCrank=focus==='crank';
  const downward=theta<Math.PI;
  const intake=ports&&downward&&t>.32;
  const exhaust=ports&&!downward&&theta>Math.PI*1.74;
  const ptop=s.pistonTop;
  const cap=Math.max(0,ptop-603);
  const gasStrength=mode==='pressure'?
    (downward? .92:.22):(!downward? .6:.27);
  const torqueOverlay=(mode==='pressure'&&downward)||mode==='shaft';
  return <g role="img" aria-label="Pistão unido por pino à biela, que se conecta ao virabrequim em rotação. Toda geometria depende do mesmo ângulo.">
    {/* Grounded, full-size machine silhouette; no isolated generic cards. */}
    <path d="M252 582 Q252 529 305 522 H704 Q751 531 753 593
             V1052 Q743 1146 643 1163 H351 Q256 1147 245 1055 Z"
      fill="#04243E" stroke="#6DD6DE" strokeWidth="16" opacity=".75"/>
    <path d="M266 590 Q263 540 311 537 H690 Q737 538 739 594
             V1050 Q731 1132 635 1150 H350 Q273 1135 266 1049 Z"
      fill="url(#sc-frame)" stroke="#063450" strokeWidth="8"/>
    {/* Mechanical housing with real structural ribs and castings. */}
    {[0,1,2,3].map(i=><g key={i}>
      <rect x={271+i*5} y={676+i*118} width="72" height="23"
        rx="9" fill="#082F51" opacity=".66"/>
      <rect x={666} y={686+i*108} width="66" height="24"
        rx="9" fill="#082E4E" opacity=".62"/>
    </g>)}
    <rect x="301" y="857" width="397" height="281" rx="94"
      fill="#042B4C" stroke="#A4EEF0" strokeOpacity=".39"
      strokeWidth="12"/>
    {/* Flywheel: its spokes and eccentric crank pin rotate as a single body. */}
    <circle cx={cx+9} cy={cy+19} r="147"
      fill="#031B33" opacity=".52"/>
    <g transform={'rotate('+(theta*180/Math.PI)+' '+cx+' '+cy+')'}>
      <circle cx={cx} cy={cy} r="140" fill="#073755"
        stroke="#6FE2DF" strokeWidth="15"/>
      <circle cx={cx} cy={cy} r="117" fill="url(#sc-wheel)"
        stroke="#0B4966" strokeWidth="9"/>
      <circle cx={cx} cy={cy} r="94" fill="#063754"
        stroke="#8EF4E1" strokeWidth="4"/>
      {Array.from({length:8},(_,i)=>{
        const a=i*Math.PI/4;
        const start=47,end=102;
        return <line key={i}
          x1={cx+Math.sin(a)*start} y1={cy+Math.cos(a)*start}
          x2={cx+Math.sin(a)*end} y2={cy+Math.cos(a)*end}
          stroke="#B0FFF2" strokeWidth="13" strokeLinecap="round"
          opacity=".67"/>;
      })}
      <path d={'M '+cx+' '+cy+' L '+(cx+g.radius*Math.sin(theta))+' '+
        (cy-g.radius*Math.cos(theta))}
        stroke="#082D4E" strokeWidth="50" strokeLinecap="round"/>
    </g>
    <circle cx={cx} cy={cy} r="34" fill="#093352"
      stroke="#E8FFF3" strokeWidth="8"/>
    <circle cx={cx} cy={cy} r="12" fill="#1DA1B7"/>
    {/* Cylinder glass cutaway is central, large enough for short-form phone. */}
    <rect x="354" y="549" width="288" height="404" rx="27"
      fill="#06314B" stroke="#072840" strokeWidth="14"/>
    <rect x="370" y="567" width="256" height="379" rx="13"
      fill="#BDEFFA" opacity=".77"/>
    <rect x="397" y="600" width="203" height="345" rx="3"
      fill="#DBFEFC" opacity=".75"/>
    <g clipPath="url(#sc-chamber)">
      <rect x="397" y="602" width="203" height={cap}
        fill="url(#sc-gas)" opacity={gasStrength}/>
      <GasParticles t={t} top={ptop} energy={gasStrength}
        accent={accent}/>
      {mode==='pressure'&&downward&&<g opacity={.65+.15*Math.sin(t*3)}>
        <path d={'M 465 625 l-20 37 h28 l-15 31 50-54 h-30 l18-31Z'}
          fill="#FFCA65" stroke="#FF8A35" strokeWidth="3"/>
      </g>}
    </g>
    <rect x="358" y="560" width="27" height="376"
      fill="url(#sc-steel)" stroke="#265C78" strokeWidth="6"/>
    <rect x="613" y="560" width="27" height="376"
      fill="url(#sc-steel)" stroke="#265C78" strokeWidth="6"/>
    {Array.from({length:5},(_,i)=><g key={i}>
      <rect x="358" y={642+i*64} width="12" height="21"
        rx="3" fill="#C6FFFF" opacity=".78"/>
      <rect x="628" y={642+i*64} width="12" height="21"
        rx="3" fill="#6AAEBF" opacity=".72"/>
    </g>)}
    {/* Operating head: common mounting plus optional declarative ports. */}
    <rect x="337" y="520" width="321" height="75" rx="21"
      fill="#103C59" stroke="#A9E5E5" strokeWidth="9"/>
    <rect x="351" y="524" width="296" height="33" rx="12"
      fill="url(#sc-steel)"/>
    <rect x="377" y="556" width="246" height="31" rx="8"
      fill="#21617D"/>
    {[366,628].map((x,i)=><g key={i}>
      <circle cx={x} cy="541" r="10" fill="#0C4460"
        stroke="#D7FCF2" strokeWidth="4"/>
    </g>)}
    {ports&&<g>
      <path d="M397 551 H239 V515 H174" stroke="#052B45"
        strokeWidth="40" strokeLinejoin="round" fill="none"/>
      <path d="M397 551 H239 V515 H174" stroke="#69CEDE"
        strokeWidth="20" strokeLinejoin="round" fill="none"/>
      <path d="M600 551 H758 V511 H832" stroke="#04293F"
        strokeWidth="40" strokeLinejoin="round" fill="none"/>
      <path d="M600 551 H758 V511 H832" stroke="#F3C36D"
        strokeWidth="20" strokeLinejoin="round" fill="none"/>
      <g transform={'rotate('+(intake?-21:0)+' 411 590)'}>
        <rect x="395" y="585" width="36" height="12" rx="4"
          fill={intake?C.teal:'#123B54'} stroke="#DDFCF7" strokeWidth="4"/>
      </g>
      <g transform={'rotate('+(exhaust?24:0)+' 585 590)'}>
        <rect x="568" y="585" width="35" height="12" rx="4"
          fill={exhaust?C.yellow:'#123B54'} stroke="#DDFCF7" strokeWidth="4"/>
      </g>
      <Arrow x={275} y={516} direction="right" opacity={intake?1:.16}
        color="#8FFFF2" scale={.7}/>
      <Arrow x={756} y={510} direction="right" opacity={exhaust?1:.16}
        color="#FFD57D" scale={.7}/>
      <SVGText x={179} y={573} size={24} weight={950} color={intake?'#B1FFF0':'#D1E6E6'}>
        ENTRADA
      </SVGText>
      <SVGText x={716} y={573} size={24} weight={950} color={exhaust?'#FFE49E':'#D1E6E6'}>
        SAÍDA
      </SVGText>
    </g>}
    {/* All three bodies are linked by a common geometry and shared crank angle. */}
    <line x1={s.pistonPin.x+6} y1={s.pistonPin.y+7}
      x2={s.crankPin.x+6} y2={s.crankPin.y+7}
      stroke="#02233D" strokeWidth="49" strokeLinecap="round"/>
    <line x1={s.pistonPin.x} y1={s.pistonPin.y}
      x2={s.crankPin.x} y2={s.crankPin.y}
      stroke="url(#sc-rod)" strokeWidth={activeRod?39:35}
      strokeLinecap="round"/>
    <line x1={s.pistonPin.x-3} y1={s.pistonPin.y-10}
      x2={s.crankPin.x-3} y2={s.crankPin.y-10}
      stroke="#FFEAAB" strokeWidth="6" opacity=".82"/>
    {/* Solid piston with rings and joint drawn over the rod. */}
    <rect x={cx-g.pistonWidth/2+7} y={ptop+8}
      width={g.pistonWidth} height={g.pistonHeight}
      rx="18" fill="#04253D" opacity=".62"/>
    <rect x={cx-g.pistonWidth/2} y={ptop}
      width={g.pistonWidth} height={g.pistonHeight}
      rx="18" fill="url(#sc-piston)"
      stroke={activePiston?C.yellow:'#0E4962'}
      strokeWidth={activePiston?10:8}/>
    <rect x={cx-g.pistonWidth/2+13} y={ptop+9}
      width={g.pistonWidth-26} height="17" rx="6" fill="#E6FFF7" opacity=".88"/>
    {[39,57].map((gap,i)=><line key={i}
      x1={cx-g.pistonWidth/2+11} x2={cx+g.pistonWidth/2-11}
      y1={ptop+gap} y2={ptop+gap}
      stroke="#145771" strokeWidth="8" strokeLinecap="round"/> )}
    <circle cx={cx} cy={s.pistonPin.y} r="25" fill="#103B5C"
      stroke="#DEFBEC" strokeWidth="6"/>
    <circle cx={cx} cy={s.pistonPin.y} r="9" fill="#6EDBE0"/>
    {/* Rear crank arm / eccentric pin remains joined, never floats. */}
    <line x1={cx} y1={cy}
      x2={s.crankPin.x} y2={s.crankPin.y}
      stroke="#08314E" strokeWidth="34" strokeLinecap="round"
      opacity={.77}/>
    <circle cx={s.crankPin.x} cy={s.crankPin.y} r="26"
      fill="#0A3554" stroke={activeRod?C.yellow:'#FCDA8C'} strokeWidth="8"/>
    <circle cx={s.crankPin.x} cy={s.crankPin.y} r="9" fill="#FDF1BC"/>
    {/* Change-of-meaning arrows follow the current physical phase. */}
    {mode==='pressure'&&downward&&
      <g opacity={torqueOverlay?smooth((t+.03)/.45):.2}>
        <path d="M310 652 V827" fill="none"
          stroke={cc.main} strokeWidth="12" strokeLinecap="round"/>
        <path d="M285 794 L310 829 L335 794" fill="none"
          stroke={cc.main} strokeWidth="12" strokeLinecap="round"/>
      </g>}
    {mode==='shaft'&&<g opacity={focus==='crank'?1:.33}>
      <path d="M375 1115 A155 155 0 0 0 620 1130" fill="none"
        stroke={cc.cold} strokeWidth="13" strokeLinecap="round"
        strokeDasharray="21 15" strokeDashoffset={-t*55}/>
      <path d="M598 1093 L627 1132 L591 1154" fill="none"
        stroke={cc.cold} strokeWidth="12" strokeLinecap="round"/>
    </g>}
    {mode==='pressure'&&focus==='crank'&&<g>
      <path d="M373 1149 A160 160 0 0 0 618 1131" fill="none"
        stroke="#FFD66C" strokeWidth="12" strokeLinecap="round"
        strokeDasharray="23 17" strokeDashoffset={-t*57}/>
      <path d="M593 1094 L628 1130 L594 1157" fill="none"
        stroke="#FFD66C" strokeWidth="12" strokeLinecap="round"/>
    </g>}
    {/* Semantic attention is tied to the ACTOR, not a floating glow card. */}
    <g fill="none" stroke={accent} strokeLinecap="round"
      opacity={.42+.13*Math.sin(t*5)}>
      {activePiston&&<rect x={cx-g.pistonWidth/2-12}
        y={ptop-11} width={g.pistonWidth+24}
        height={g.pistonHeight+22} rx="26" strokeWidth="10"/>}
      {activeRod&&<line x1={s.pistonPin.x} y1={s.pistonPin.y}
        x2={s.crankPin.x} y2={s.crankPin.y} strokeWidth="59"
        opacity=".4"/>}
      {activeCrank&&<circle cx={cx} cy={cy} r="153"
        strokeWidth="9" strokeDasharray="30 23"
        strokeDashoffset={-t*92}/>}
      {focus==='intake'&&<circle cx="411" cy="589" r="31"
        strokeWidth="10"/>}
      {focus==='outlet'&&<circle cx="585" cy="589" r="31"
        strokeWidth="10"/>}
    </g>
    {/* Labels are anchored to components; large readable phone typography. */}
    <g opacity={.96}>
      <path d={'M 620 '+(ptop+49)+' H648'} stroke="#E1FFEF"
        strokeWidth="4" fill="none"/>
      <circle cx="619" cy={ptop+49} r="7" fill={activePiston?C.yellow:C.teal}/>
      <SVGText x={654} y={ptop+57} size={26} weight={950}
        color={activePiston?C.yellow:C.white}>PISTÃO</SVGText>
      <path d={'M 416 '+(s.pistonPin.y+145)+' L304 '+(s.pistonPin.y+160)}
        stroke="#D8F9F6" strokeWidth="4" fill="none" opacity=".81"/>
      <SVGText x={185} y={s.pistonPin.y+168} size={25} weight={950}
        color={activeRod?C.yellow:C.white}>BIELA</SVGText>
      <path d="M622 1060 H697" stroke="#D8FFF3" strokeWidth="4"/>
      <SVGText x={702} y={1068} size={23} weight={950} color={activeCrank?C.yellow:C.white}>
        EIXO
      </SVGText>
    </g>
    {/* Permanent foundation and material details, not functional objects. */}
    <path d="M355 1151 H645" stroke="#04263B" strokeWidth="43"
      strokeLinecap="round"/>
    <path d="M372 1151 H629" stroke="#90DDE3" strokeWidth="13"
      strokeLinecap="round"/>
    {Array.from({length:7},(_,i)=><circle key={i}
      cx={296+i*69} cy="1151" r="8" fill="#B7EDE9"
      stroke="#0C4660" strokeWidth="4"/>)}
  </g>;
};

export const SliderCrankProof:React.FC<Props>=({kind,private_review_only=true})=>{
 const {fps}=useVideoConfig();
 const frame=useCurrentFrame();
 const t=frame/fps;
 const fixture:Model=(specs.models as unknown as Record<string,Model>)[kind]
   ??(specs.models.motor as unknown as Model);
 const duration=specs.duration;
 const stage=Math.max(0,fixture.steps.reduce((idx,s,i)=>t>=s.at?i:idx,0));
 const beat=fixture.steps[stage];
 const palette=colors(fixture.driver);
 const state=rigState(angleAt(t,duration-.38),fixture.geometry);
 const previousStep=fixture.steps[Math.max(0,stage-1)];
 const currentFocus=focusAnchor(beat.focus,state,fixture.geometry);
 const previousFocus=focusAnchor(previousStep.focus,state,fixture.geometry);
 const camera=semanticCamera2D({
   t,focus:currentFocus,previousFocus,changeAt:beat.at,
   machine:specs.camera.machineBounds,
   startViewport:specs.camera.introViewport,
   detailViewport:specs.camera.detailViewport,
   maxScale:specs.camera.maxScale,
   zoomStart:specs.camera.zoomStart,
   zoomSeconds:specs.camera.zoomSeconds,
 });
 const titleOpacity=1-ease((t-.58)/.52);
 const out=(Math.round(state.displacement/fixture.geometry.radius));
 return <svg width="100%" height="100%" viewBox="0 0 1080 1920"
   preserveAspectRatio="xMidYMid meet" role="img"
   aria-label="Prova animada do mecanismo pistão–biela–virabrequim, calculado pela cinemática slider-crank">
    <Defs accent={fixture.accent}/>
    <rect width="1080" height="1920" fill="url(#sc-bg)"/>
    <ellipse cx="525" cy="885" rx="590" ry="680" fill="url(#sc-stage)"/>
    <path d="M0 1490 Q215 1440 445 1512 T1080 1505 V1920 H0Z"
      fill="#063151" opacity=".67"/>
    <path d="M0 1635 Q260 1575 530 1645 T1080 1613 V1920 H0Z"
      fill="#03243F" opacity=".75"/>
    {/* Branded editorial opening, not a giant card with a number. */}
    <rect x="135" y="295" width="328" height="55" rx="10"
      fill="#031D33" stroke="#1CBFCA" strokeWidth="3"/>
    <SVGText x={153} y={332} size={28} color={C.white} weight={950}>
      CORINGA
    </SVGText>
    <rect x="301" y="307" width="150" height="34" rx="6" fill={C.yellow}/>
    <SVGText x={316} y={331} size={23} color={C.ink} weight={950}>EXPLICA</SVGText>
    <g opacity={titleOpacity}>
      <SVGText x={138} y={390} size={57} color={C.white} weight={950} spacing={-1.5}>
        {fixture.title[0]}
      </SVGText>
      <SVGText x={138} y={448} size={57} color={C.white} weight={950} spacing={-1.5}>
        {fixture.title[1]}
      </SVGText>
      <rect x="140" y="470" width="85" height="9" rx="4" fill={fixture.accent}/>
      <SVGText x={238} y={495} size={27} color="#C7EFF2" weight={740}>
        {fixture.subtitle}
      </SVGText>
    </g>
    {/* CÂMERA SEMÂNTICA COMPARTILHADA: palco se aproxima sem cortar a
        máquina e acompanha suavemente o alvo físico de cada acontecimento. */}
    <g transform={`matrix(${camera.scale} 0 0 ${camera.scale} ${camera.tx} ${camera.ty})`}>
      <Cutaway t={t} g={fixture.geometry} mode={fixture.driver}
        focus={beat.focus} ports={fixture.ports}
        accent={fixture.accent} duration={duration}/>
    </g>
    {/* Narrative caption: always about the ACTUAL causal change. */}
    <rect x="129" y="1174" width="804" height="80" rx="22"
      fill="#082A44" stroke="#2C92AF" strokeWidth="4"/>
    <rect x="149" y="1192" width="10" height="38" rx="5"
      fill={fixture.accent}/>
    <SVGText x={234} y={1208} size={33} color={C.white} weight={950}>
      {beat.label}
    </SVGText>
    <SVGText x={153} y={1238} size={23} color="#CBF3F4" weight={650}>
      {beat.detail}
    </SVGText>
    <SVGText x={174} y={1208} size={19} color={fixture.accent} weight={950}>
      {String(stage+1).padStart(2,'0')+' / 04'}
    </SVGText>
    {private_review_only&&
      <SVGText x={540} y={1847} size={23} color="#8CB2CA"
        anchor="middle" weight={810} spacing={1.7}>
        LABORATÓRIO PRIVADO · NÃO PUBLICAR
      </SVGText>}
    {/* End of data-driven physical proof. No episode-specific TSX conditions. */}
    <g opacity="0" data-displacement={out}
      data-crank-degrees={Math.round(state.theta*180/Math.PI)}>
      <text x="0" y="0">FRAME</text>
    </g>
  </svg>;
};
