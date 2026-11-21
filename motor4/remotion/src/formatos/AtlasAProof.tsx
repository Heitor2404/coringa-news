/** Prova A: DOIS mecanismos independentes, mesmo acabamento editorial.
 * SVG 2.5D original com partes físicas ligadas a um único estado temporal.
 * Não copiar pixels de concept art. NÃO É renderer público/produção.
 */
import React from 'react';
import {useCurrentFrame,useVideoConfig} from 'remotion';
import cfg from './atlas-a-proof.json';
import {AtlasAStudio,COLORS} from './AtlasAStudio';
import {smooth,clamp01,eventAt,eventTime,type MechanismEvent} from './Mechanism2DCore';
import {ABeveledPanel,AJoint,ARivet} from './AtlasAArtKit';

export type AtlasAMechanism='lock'|'euv';
type Event=MechanismEvent<string>;
export type AtlasAProps={
  kind:AtlasAMechanism;
  duracao?:number;
  private_review_only?:boolean;
};
const actionTime=(events:readonly Event[],action:string):number=>
  eventTime(events,action)??Number.POSITIVE_INFINITY;
const propsFor=(kind:AtlasAMechanism)=>{
  const v=cfg.subjects[kind];
  const events=v.events.map(e=>({...e})) as Event[];
  return {title:v.title as [string,string],
    section:v.category,source:v.source,events};
};
const progress=(t:number,start:number,duration:number)=>
  smooth((t-start)/duration);
const Txt:React.FC<{
 x:number;y:number;text:string;size?:number;
 color?:string;anchor?:'middle'|'end'|'start'
}>=({x,y,text,size=27,color='#FFFFFF',anchor='middle'})=>
 <text x={x} y={y} fill={color} fontSize={size}
   textAnchor={anchor} fontFamily="Inter,Arial,sans-serif"
   fontWeight="900" paintOrder="stroke"
   stroke="rgba(4,20,42,.55)" strokeWidth="4">{text}</text>;

const Clouds:React.FC<{t:number}>=({t})=><g opacity=".7">
  {Array.from({length:3},(_,i)=><path key={i}
    d={'M'+(20+i*350+t*4)+' '+(575+i%2*85)+
      ' q42 -30 80 0 q61 -44 124 5 q41 -15 72 15 q-65 19 -138 11 q-100 12 -138 -31Z'}
    fill="#EAF9FF" opacity=".55"/>)}
</g>;
const HillTrees:React.FC=()=> <g>
  {[0,1,2,3,4,5,6].map(i=><g key={i}>
    <rect x={45+i*159} y={774+(i%3)*19} width="9"
      height="74" rx="4" fill="#1A7759"/>
    <circle cx={50+i*159} cy={769+(i%3)*19} r={25+(i%3)*9}
      fill={i%2?'#3FBE7D':'#1E9E74'}/>
    <circle cx={40+i*159} cy={754+(i%3)*19} r="15"
      fill="#8AE396" opacity=".55"/>
  </g>)}
</g>;

export const lockState=(t:number,events:readonly Event[])=>{
  const hook=actionTime(events,'hook');
  const release=actionTime(events,'release');
  // Consequência começa no gancho; mesmo estado alimenta água e casco.
  const fill=clamp01((t-hook)/4.9);
  const waterY=959-141*fill;
  const boatShift=waterY-959;
  const open=progress(t,release,.68);
  const flow=t>=hook&&t<release;
  return {fill,waterY,boatShift,open,flow,
    gateShift:open*57,boatTravel:open*20};
};

const LockActors:React.FC<{t:number;events:Event[]}>=({t,events})=>{
  const s=lockState(t,events);
  const amber=COLORS.yellow;
  return <g aria-label="Câmara da eclusa e reservatório ligados por conduto inferior; água sobe e navio flutua com a superfície">
    <defs>
      <clipPath id="a-chamber"><rect x="264" y="668" width="636" height="470"/></clipPath>
      <clipPath id="a-reservoir"><rect x="75" y="723" width="169" height="413"/></clipPath>
    </defs>
    <Clouds t={t}/><HillTrees/>
    {/* Estratigrafia exposta. Não é decoração: permite enxergar a galeria
        hidráulica passando SOB a câmara em 9:16. Sem rótulos essenciais
        na faixa inferior ocupável pelas redes. */}
    <path d="M0 1207 Q220 1181 467 1212 T1080 1200 V1920 H0Z"
      fill="#746F60" stroke="#D1B99B" strokeWidth="12"/>
    <path d="M0 1332 Q195 1287 414 1328 T1080 1310 V1438
      Q760 1473 493 1436 T0 1457Z" fill="#9A826E" opacity=".87"/>
    <path d="M0 1509 Q255 1470 533 1524 T1080 1487 V1623
      Q807 1660 567 1631 T0 1660Z" fill="#54635F" opacity=".9"/>
    <path d="M0 1710 Q321 1690 539 1730 T1080 1695 V1920 H0Z"
      fill="#294F55" opacity=".93"/>
    {Array.from({length:13},(_,i)=>{
      const x=(i*179)%1120,y=1310+(i%4)*155;
      return <g key={i} opacity=".24">
        <path d={'M'+x+' '+y+' l45 12 -20 25 -32 -6Z'}
          fill={i%2?'#D9C6A3':'#213F4B'}/>
        <path d={'M'+(x+60)+' '+(y+23)+' l29 -10 15 21'}
          fill="none" stroke="#E7CDB2" strokeWidth="5"/>
      </g>;
    })}
    {/* Terreno e estrutura: concretos com perspectiva simples 2.5D,
        nunca uma imagem estática ocupando todo o quadro. */}
    <path d="M0 809 Q165 749 262 810 L264 1150 H0Z"
      fill="#7E9870"/>
    <path d="M932 811 Q1004 774 1080 794 V1291 H930Z"
      fill="#7D976D"/>
    <path d="M0 1115 H1080 V1267 H0Z" fill="#596D65" opacity=".55"/>
    <path d="M72 709 V1141 H249 V674" fill="#60717D"
      stroke="#E2D1B6" strokeWidth="13" strokeLinejoin="round"/>
    <path d="M267 661 H913 V1140 H257V661Z"
      fill="#0B314C" stroke="#D0BC9E" strokeWidth="19"/>
    <rect x="280" y="675" width="616" height="450" fill="#0A3962"/>
    <rect x="272" y="670" width="622" height="452" fill="#073A60"
      opacity=".36"/>
    {/* Reservatório elevado à esquerda. A origem da água fica visível. */}
    <g clipPath="url(#a-reservoir)">
      <rect x="77" y="802" width="163" height="332"
        fill="url(#a-lock-water)"/>
      {Array.from({length:5},(_,i)=><path key={i}
        d={'M75 '+(815+i*51)+' H245'} stroke="#99F9F7"
        strokeWidth="4" opacity=".28"/>)}
    </g>
    <path d="M73 802 H244" stroke="#E6FCFF" strokeWidth="7"/>
    <Txt x={158} y={760} size={23} text="NÍVEL ALTO"/>
    <path d="M245 690 V1150" stroke="#DBBF96" strokeWidth="24"/>
    <path d="M267 685 V1139" stroke="#264C65" strokeWidth="9"/>

    {/* Água da câmara: único waterY usado pela superfície e pelo navio. */}
    <g clipPath="url(#a-chamber)">
      <rect x="271" y={s.waterY} width="625" height={1146-s.waterY}
        fill="url(#a-lock-water)"/>
      <path d={'M272 '+s.waterY+' H901'} stroke="#E4FFFF"
        strokeWidth="8"/>
      {Array.from({length:9},(_,i)=><path key={i}
        d={'M'+(279+i*76)+' '+(s.waterY+24+Math.sin(t*5+i)*4)+' h48'}
        fill="none" stroke="#E2FFFF" strokeWidth="4" opacity=".4"/>)}
      {Array.from({length:5},(_,i)=><path key={i}
        d={'M'+(297+i*113)+' '+(s.waterY+66+i%2*38)+' h31'}
        stroke="#B1F7F8" strokeWidth="3" opacity=".25"/>)}
    </g>
    {/* Gated bottom channel is drawn as ONE connected pipe. The origin
        is in the raised reservoir, destination under the chamber water. */}
    <path d="M166 878 V1440 H355 V993"
      fill="none" stroke="#3B4B59" strokeWidth="53"
      strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M166 878 V1440 H355 V993"
      fill="none" stroke="#80AAB7" strokeWidth="34"
      strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M166 878 V1440 H355 V993"
      fill="none" stroke={s.flow?'#28EBFF':'#376F94'}
      strokeWidth="18" strokeDasharray="22 28"
      strokeDashoffset={-t*106} strokeLinecap="round"
      strokeLinejoin="round" opacity={s.flow?1:.35}/>
    <AJoint x={166} y={944} r={44} active={s.flow}/>
    <circle cx="166" cy="944" r="36" fill="#124366"
      stroke={s.flow?amber:'#C7DEDE'} strokeWidth="8"/>
    <path d="M145 923 L188 965 M188 923 L145 965" stroke="#E8F7F8"
      strokeWidth="8" strokeLinecap="round" opacity={s.flow?.35:1}/>
    {s.flow&&<g>
      <path d="M160 982 l-16 -18 h32Z" fill={amber}/>
      <path d="M256 997 l22 14 -22 14Z" fill={amber}/>
    </g>}
    {/* Sidewalls stay visible and physically separate the two levels. */}
    <path d="M908 666 V1146" stroke="#456479" strokeWidth="45"/>
    <path d="M899 666 V1146" stroke="url(#a-concrete)" strokeWidth="27"/>
    <path d="M251 661 V1141" stroke="#253C50" strokeWidth="13"/>
    <g transform={'translate('+s.gateShift+' 0)'} opacity={1-s.open*.75}>
      <path d="M903 716 V1118" stroke="#17354C" strokeWidth="29"/>
      <path d="M911 716 V1118" stroke="#B0C4C9" strokeWidth="14"/>
    </g>
    {/* Ship bow remains IN ONE CHAMBER. Hull follows water by buoyancy,
        not by an independent keyframe translation. */}
    <g transform={'translate('+(-40+s.boatTravel)+' '+s.boatShift+') translate(560 959) scale(1.28 1.05) translate(-560 -959)'}>
      <ellipse cx="565" cy="977" rx="218" ry="27" fill="#031B34" opacity=".37"/>
      {/* stacks: three layers of actual colorful shipping containers */}
      {Array.from({length:3},(_,row)=>
        Array.from({length:5-row},(_,col)=>{
          const x=394+col*58+row*30,y=755-row*53;
          const colors=['#FF8F23','#0BA0C5','#EA542F','#197D9F','#F3B829'];
          return <g key={row+'-'+col}>
            <rect x={x} y={y} width="56" height="50" rx="2"
              fill={colors[(col+row*2)%colors.length]}
              stroke="#D3E2E4" strokeWidth="2.2"/>
            {Array.from({length:4},(_,i)=><path key={i}
              d={'M'+(x+9+i*12)+' '+(y+4)+' v42'}
              stroke="#143F56" strokeWidth="2.5" opacity=".32"/>)}
          </g>;
        })
      )}
      <path d="M344 805 H791 L755 949 Q565 1010 379 949 Z"
        fill="url(#a-ship)" stroke="#BFE9F1" strokeWidth="6"/>
      <path d="M351 820 H787 L751 903 H389Z" fill="#145F8E" opacity=".35"/>
      <path d="M387 925 Q560 967 748 925" fill="none"
        stroke="#39A5CA" strokeWidth="8" opacity=".65"/>
      <path d="M374 809 H762" stroke="#E2F7FA" strokeWidth="6"/>
      {/* Bridge and crew house */}
      <rect x="565" y="706" width="131" height="48" rx="4"
        fill="#F4FAF5" stroke="#9FD4DD" strokeWidth="4"/>
      <rect x="588" y="672" width="83" height="33" rx="3"
        fill="#E8F7F5"/>
      <rect x="623" y="646" width="11" height="26"
        fill="#EAF7F2"/>
      <path d="M634 640 V650" stroke="#FFF9E5" strokeWidth="4"/>
      {[0,1,2,3].map(i=><rect key={i} x={579+i*27} y="722"
        width="19" height="17" fill="#0B5B87" rx="2"/>)}
      <path d="M367 907 Q558 964 772 907" stroke="#D4ECF2"
        strokeWidth="5" fill="none" opacity=".58"/>
    </g>
    {/* Cause-effect highlight, never a giant floating card. */}
    {s.fill>.04&&<g opacity={Math.min(1,s.fill*4)}>
      <path d={'M328 '+(s.waterY+15)+' V'+(s.waterY-95)}
        stroke={amber} strokeWidth="8" strokeDasharray="16 12"/>
      <path d={'M308 '+(s.waterY-74)+' L328 '+(s.waterY-110)+' L348 '+(s.waterY-74)+'Z'}
        fill={amber}/>
    </g>}
    {s.open>.2&&<g opacity={s.open}>
      <path d="M845 874 H897" stroke={amber}
        strokeWidth="8" strokeDasharray="12 10"/>
      <path d="M888 856 L909 874 L888 892Z" fill={amber}/>
    </g>}
    {/* Technical side highlighting stays tied to the hydraulic circuit. */}
    <ABeveledPanel x={80} y={1143} width={925} height={34}
      tone="sand" rx={5}/>
    <ARivet x={132} y={1160} r={8}/>
    <ARivet x={956} y={1160} r={8}/>
    <path d="M90 1282 Q245 1231 393 1286 T702 1271 T1090 1260"
      stroke="#91F5F6" strokeWidth="4" opacity=".14" fill="none"/>
  </g>;
};

const Photon:React.FC<{d:string;p:number;col?:string}>=({
 d,p,col='#EF81FF'
})=>{
 const q=Math.max(0,Math.min(1,p));
 return <g opacity={q}>
   <path d={d} fill="none" stroke={col} strokeWidth="31"
     strokeLinecap="round" opacity=".16"
     pathLength={1} strokeDasharray="1" strokeDashoffset={1-q}/>
   <path d={d} fill="none" stroke={col} strokeWidth="11"
     strokeLinecap="round" pathLength={1} strokeDasharray="1"
     strokeDashoffset={1-q}/>
   <path d={d} fill="none" stroke="#FFFFFF" strokeWidth="2.5"
     opacity=".83" strokeLinecap="round" pathLength={1}
     strokeDasharray="1" strokeDashoffset={1-q}/>
 </g>;
};
export const euvState=(t:number,events:readonly Event[])=>{
 const a=(name:string)=>actionTime(events,name);
 const source=progress(t,a('hook'),1.0);
 const reflection=progress(t,a('reticle'),.75);
 const mirrors=progress(t,a('mirrors'),.85);
 const resist=progress(t,a('wafer'),.90);
 return {source,reflection,mirrors,resist};
};
const EuvActors:React.FC<{t:number;events:Event[]}>=({t,events})=>{
 const s=euvState(t,events);
 const gold=COLORS.yellow,purple='#CE7EFF';
 return <g aria-label="Esquema ilustrativo EUV: a máscara REFLETE a luz; espelhos projetam o padrão sobre a resina do wafer">
   <defs>
    <clipPath id="a-euv-wafer-clip"><ellipse cx="510" cy="989" rx="278" ry="70"/></clipPath>
   </defs>
   {/* Housing and column are physical equipment parts, not abstract
       grids or presentation cards. Shapes retain consistent locations. */}
   <path d="M160 578 H904 V1118 H178 Q147 1088 160 578Z"
     fill="#104B77" stroke="#80D8E7" strokeWidth="17"/>
   <path d="M164 587 H899 V1096 H164Z"
     fill="#1C527F" opacity=".55"/>
   <path d="M201 612 V1084 M858 612 V1084" stroke="#D6B46C"
     strokeWidth="17" opacity=".8"/>
   <path d="M198 624 H868" stroke="#BCEFF2" strokeWidth="7" opacity=".60"/>
   <ABeveledPanel x={182} y={1088} width={710} height={28}
     tone="steel" rx={5}/>
   <ARivet x={208} y={1101} r={7}/>
   <ARivet x={862} y={1101} r={7}/>
   <circle cx="213" cy="737" r={106+Math.sin(t*2)*5}
     fill="url(#a-euv-glow)" opacity={s.source}/>
   <AJoint x={212} y={740} r={69} active={s.source>.15} accent="#FFCC60"/>
   <circle cx="212" cy="740" r="57" fill="#D47B56"
     stroke="#FFE8A5" strokeWidth="8"/>
   {Array.from({length:12},(_,i)=>{
     const a=i*Math.PI/6+t*.55;
     return <path key={i} d={'M'+(212+Math.cos(a)*38)+' '+(740+Math.sin(a)*38)+
       ' L'+(212+Math.cos(a)*51)+' '+(740+Math.sin(a)*51)}
       stroke={gold} strokeWidth="5" opacity={.2+.8*s.source}/>;
   })}
   <circle cx="212" cy="740" r="19" fill={gold} opacity={.45+.55*s.source}/>
   <circle cx="212" cy="740" r="8" fill="#FFFCE0"/>
   {/* Illuminate from source to reflective patterned reticle. */}
   <Photon d="M270 725 L535 635" p={s.source} col="#FFF1B8"/>
   {/* Reticle slants to visually deflect the incident ray. Light reflects
       at x513 y664, not through the mask into the optics. */}
   <g>
     <path d="M395 597 L681 674 L668 735 L382 658Z"
       fill="url(#a-euv-steel)" stroke="#C4DDF2" strokeWidth="7"
       strokeLinejoin="round"/>
     <path d="M393 612 L674 684 L666 710 L388 636Z"
       fill="#222150" stroke="#D49FFF" strokeWidth="4"/>
     {Array.from({length:8},(_,i)=><path key={i}
       d={'M'+(403+i*32)+' '+(616+i*8)+' l-6 29'}
       stroke={i%3===0?'#F9C35C':'#E4BAFF'} strokeWidth="13"
       opacity={.25+.65*s.reflection}/>)}
     <path d="M393 600 L683 675" stroke="#FDEAB3" strokeWidth="5"
       opacity={.25+.75*s.reflection}/>
     {/* A função da máscara é explicada pelo cue; um segundo letreiro aqui
         encobriria a superfície refletiva após a compactação editorial. */}
   </g>
   {/* All rays share the SAME paths over all beats. Only disclosure changes. */}
   <circle cx="535" cy="635" r="10" fill="#FFDF6D" opacity={s.reflection}/>
   <Photon d="M535 635 L758 787" p={s.reflection} col="#E2F8FF"/>
   <AJoint x={759} y={792} r={37} active={s.mirrors>.1}/>
   <ellipse cx="759" cy="792" rx="102" ry="23"
     transform="rotate(-25 759 792)" fill="url(#a-euv-steel)"
     stroke="#D6F3FF" strokeWidth="6"/>
   <ellipse cx="759" cy="792" rx="79" ry="8"
     transform="rotate(-25 759 792)" fill="#80DBFF" opacity={.2+.46*s.mirrors}/>
   <Photon d="M745 819 L587 877" p={s.mirrors} col="#8FCAFF"/>
   <AJoint x={580} y={879} r={33} active={s.mirrors>.1}/>
   <ellipse cx="580" cy="879" rx="94" ry="20"
     transform="rotate(26 580 879)" fill="url(#a-euv-steel)"
     stroke="#A5E7F6" strokeWidth="6"/>
   <ellipse cx="580" cy="879" rx="72" ry="7"
     transform="rotate(26 580 879)" fill="#9BCDF8"
     opacity={.16+.4*s.mirrors}/>
   <Photon d="M561 896 L524 951" p={s.mirrors} col="#D787FF"/>
   {/* Mesa mecânica contínua: conectada ao estágio, não disco flutuante. */}
   <path d="M390 1035 L405 1312 H638 L654 1035" fill="#15466C"
     stroke="#86D7E9" strokeWidth="22" strokeLinejoin="round"/>
   <ABeveledPanel x={426} y={1091} width={164} height={239}
     tone="cobalt" rx={12}/>
   <ARivet x={455} y={1264}/><ARivet x={562} y={1264}/>
   {/* Wafer and exposing photoresist, not a complete finished chip. */}
   <ellipse cx="509" cy="1039" rx="296" ry="67"
     fill="#0A0F3A" opacity=".6"/>
   <path d="M231 987 Q242 1114 510 1114 Q778 1114 789 987
     L789 1011 Q768 1135 510 1135 Q252 1135 231 1011Z"
     fill="url(#a-euv-steel)" stroke="#9BCDF7" strokeWidth="7"/>
   <ellipse cx="510" cy="989" rx="278" ry="70"
     fill="url(#a-euv-wafer)" stroke="#C2DCFC" strokeWidth="7"/>
   <ellipse cx="510" cy="989" rx="265" ry="61"
     fill="none" stroke="#6EADFF" strokeWidth="3" opacity=".8"/>
   <g clipPath="url(#a-euv-wafer-clip)">
     {Array.from({length:8},(_,i)=><path key={'vert'+i}
       d={'M'+(270+i*66)+' 910 V1071'} stroke="#7C8DCE"
       strokeWidth="2" opacity=".42"/>)}
     {Array.from({length:5},(_,i)=><path key={'horiz'+i}
       d={'M215 '+(953+i*24)+' H792'} stroke="#7C8DCE"
       strokeWidth="2" opacity=".42"/>)}
     {Array.from({length:7},(_,i)=><g key={i} opacity={s.resist}>
       <rect x={314+i*60} y={976+(i%2)*11} width="40" height="33"
         fill={gold} rx="3" opacity=".4"/>
       <rect x={327+i*60} y={983+(i%2)*11} width="13" height="20"
         fill="#FFA9FF" rx="2"/>
     </g>)}
     <rect x={221+s.resist*590} y="908" width="31" height="170"
       fill="#DEABFF" opacity={s.resist>0&&s.resist<1?.38:0}/>
   </g>
   {s.resist>.1&&<ellipse cx="508" cy="963" rx="244" ry="41"
     fill="#B679FF" opacity={s.resist*.07}/>}
   {/* Deliberately spare labels: editorial cue explains each action. */}
   <Txt x={206} y={840} size={24} text="FONTE EUV" color="#FFFFFF"/>
   <Txt x={510} y={1180} size={25} text="WAFER · RESINA FOTOSSENSÍVEL"
     color="#F9EEFF"/>
  </g>;
};

/** Same typography, rhythm contract and visual margins for both families.
 * Implementations are separate PHYSICAL capabilities, not per-episode edits.
 */
export const AtlasAProof:React.FC<AtlasAProps>=({
  kind,duracao,private_review_only=true
})=>{
 const frame=useCurrentFrame(),fps=useVideoConfig().fps;
 const t=frame/fps;
 const x=propsFor(kind);
 const fallback=x.events[0];
 const active=eventAt(t,x.events,fallback);
 const idx=Math.max(0,x.events.findIndex(e=>e.action===active.action));
 return <AtlasAStudio kind={kind} t={t} title={x.title}
    section={x.section} source={x.source} label={active.label}
    step={idx+1} total={x.events.length}
    privateReviewOnly={private_review_only}>
    {kind==='lock'
      ?<LockActors t={t} events={x.events}/>
      :<EuvActors t={t} events={x.events}/>}
  </AtlasAStudio>;
};
