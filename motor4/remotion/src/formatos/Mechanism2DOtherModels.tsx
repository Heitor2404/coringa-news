/** PROVA PRIVADA — duas famílias de mecanismos 2D com a MESMA identidade.
 * Ambas usam events + geometria, mas relações físicas diferentes.
 * Não implica gerar qualquer máquina a partir de uma frase.
 */
import React from 'react';
import {useCurrentFrame,useVideoConfig} from 'remotion';
import probes from './mechanisms2d-probes.json';
import {ASurfaceGrain} from './AtlasAArtKit';
import {PAPER,PaperLayout} from './Mechanism2DPaperStudio';
import {smooth,eventAt,eventTime,type MechanismEvent} from './Mechanism2DCore';

type PulleyAction='assembly'|'load'|'pull'|'lift'|'result';
type GearAction='assembly'|'teeth'|'drive'|'ratio'|'result';
type Mode='pulley'|'gears';
type Props={duracao?:number;kind:Mode;private_review_only?:boolean};
const font='Inter,Arial,sans-serif';
const asCues=<A extends string>(entries:readonly {at:number;action:string;label:string}[]):
 MechanismEvent<A>[]=>entries.map(e=>({at:e.at,action:e.action as A,label:e.label}));

const ArcArrow:React.FC<{cx:number;cy:number;r:number;reverse?:boolean;opacity:number;stroke:string}>=
({cx,cy,r,reverse=false,opacity,stroke})=>{
 const from=reverse?140:40,to=reverse?40:140;
 const pt=(deg:number)=>{
  const a=deg*Math.PI/180;
  return [cx+Math.cos(a)*r,cy+Math.sin(a)*r];
 };
 const [x1,y1]=pt(from),[x2,y2]=pt(to);
 const d=['M',x1,y1,'A',r,r,0,0,reverse?0:1,x2,y2].join(' ');
 const arrow=(reverse?'M '+(x2-15)+' '+(y2+5)+' L '+(x2+4)+' '+(y2-6)+' L '+(x2+13)+' '+(y2+13):
   'M '+(x2-14)+' '+(y2-9)+' L '+(x2+5)+' '+(y2+3)+' L '+(x2+13)+' '+(y2-17));
 return <g opacity={opacity} fill="none" stroke={stroke} strokeWidth="8"
   strokeLinecap="round" strokeLinejoin="round">
   <path d={d}/><path d={arrow}/>
 </g>;
};
const Text:React.FC<{x:number;y:number;size?:number;color?:string;children:React.ReactNode}>=
({x,y,size=25,color=PAPER.ink,children})=>
 <text x={x} y={y} textAnchor="middle" fontSize={size}
   fontFamily={font} fill={color} fontWeight="850">{children}</text>;

export const pulleyState=(t:number)=>{
 const v=probes.demo.pulley;
 const cues=asCues<PulleyAction>(v.cues);
 const cue=(name:PulleyAction)=>eventTime(cues,name)??100;
 const assembly=smooth((t-cue('assembly'))/.5);
 const weightVisible=smooth((t-cue('load'))/.6);
 const intent=smooth((t-cue('pull'))/.55);
 const travel=smooth((t-(cue('pull')+.4))/2.65)*v.geometry.maxTravel;
 const result=smooth((t-cue('result'))/.45);
 const current=eventAt(t,cues,cues[0]);
 const g=v.geometry;
 return {cues,current,assembly,weightVisible,intent,travel,result,
   freeEndY:g.freeEndInitialY+travel,loadTopY:g.loadTopInitialY-travel,
   wheelRotation:travel/g.radius*180/Math.PI};
};
const PulleyDrawing:React.FC<{t:number}>=({t})=>{
 const st=pulleyState(t),g=probes.demo.pulley.geometry;
 const cx=g.center[0],cy=g.center[1],r=g.radius;
 const path='M '+g.freeX+' '+st.freeEndY+' V '+cy+
   ' A '+r+' '+r+' 0 0 1 '+g.loadX+' '+cy+' V '+st.loadTopY;
 const loadY=st.loadTopY+24;
 const ropeOpacity=.35+.65*st.assembly;
 return <g role="img" aria-label="Polia fixa com roda, corda contínua e peso; a ponta desce enquanto o peso sobe">
   {/* Viga e suspensão do eixo: os apoios pertencem à máquina. */}
   <path d="M 264 519 H 761" stroke="#AFA496" strokeWidth="24" strokeLinecap="round"/>
   <path d="M 292 499 H 729" stroke="#FAF6EC" strokeWidth="7" strokeLinecap="round"/>
   <path d="M 500 529 V 574" stroke={PAPER.deep} strokeWidth="21" strokeLinecap="round"/>
   <path d="M 510 540 V 582" stroke="#99A9AE" strokeWidth="6"/>
   <g opacity={st.assembly}>
     {/* Roda que realmente gira a partir do MESMO deslocamento da corda. */}
     <circle cx={cx} cy={cy} r={r+11} fill="#B7A795" opacity=".17"/>
     <g transform={'rotate('+st.wheelRotation+' '+cx+' '+cy+')'}>
       <circle cx={cx} cy={cy} r={r} fill="url(#paper-teal-metal)"
         stroke={PAPER.deep} strokeWidth="8"/>
       <circle cx={cx} cy={cy} r={r-12} fill="none"
         stroke="#DAE9E5" strokeWidth="5" opacity=".77"/>
       {Array.from({length:6},(_,i)=>{
         const a=i*Math.PI/3;
         return <path key={i}
           d={['M',cx+Math.cos(a)*28,cy+Math.sin(a)*28,
             'L',cx+Math.cos(a)*(r-25),cy+Math.sin(a)*(r-25)].join(' ')}
           fill="none" stroke="#D9F0EA" strokeWidth="13" strokeLinecap="round"
           opacity=".75"/>;
       })}
     </g>
     <circle cx={cx} cy={cy} r="27" fill="#344D56"
       stroke="#FAF9F1" strokeWidth="5"/>
     <circle cx={cx} cy={cy} r="10" fill="#D3E9E6"/>
   </g>
   {/* Desenhar a corda como UMA peça contínua mantém a causalidade,
       não um painel com flechas independentes. */}
   <path d={path} stroke="#705A42" strokeWidth="19" opacity={ropeOpacity}
     strokeLinecap="round" fill="none"/>
   <path d={path} stroke="#E7C18D" strokeWidth="13" opacity={st.assembly}
     strokeLinecap="round" fill="none"/>
   <path d={path} stroke="#FBDEAE" strokeWidth="3" opacity={st.assembly}
     strokeLinecap="round" fill="none"/>
   <g opacity={st.assembly}>
     <circle cx={g.freeX} cy={st.freeEndY} r="18"
       fill={PAPER.gold} stroke="#F7E8CE" strokeWidth="5"/>
     <path d={['M',g.freeX-37,st.freeEndY+23,'Q',g.freeX,st.freeEndY+60,
       g.freeX+37,st.freeEndY+23].join(' ')}
       fill="none" stroke={PAPER.gold} strokeWidth="10" strokeLinecap="round"/>
   </g>
   <g opacity={st.weightVisible}>
     {/* Caixa solidária à ponta oposta da corda; seu y é derivado do
         mesmo travel e não de outra timeline visual. */}
     <path d={['M',g.loadX,st.loadTopY,'V',loadY].join(' ')}
       stroke="#617E84" strokeWidth="9" strokeLinecap="round"/>
     <path d={['M',g.loadX-26,loadY,'Q',g.loadX,loadY-24,g.loadX+26,loadY].join(' ')}
       fill="none" stroke="#617E84" strokeWidth="8"/>
     <rect x={g.loadX-g.loadWidth/2} y={loadY}
       width={g.loadWidth} height={g.loadHeight} rx="9"
       fill="url(#paper-steel)" stroke="#3B5665" strokeWidth="5"/>
     <path d={['M',g.loadX-g.loadWidth/2+14,loadY+15,
       'H',g.loadX+g.loadWidth/2-14].join(' ')}
       stroke="#C4D2D6" strokeWidth="6" opacity=".6"/>
     {Array.from({length:3},(_,i)=><path key={i}
       d={['M',g.loadX-42+i*42,loadY+32,'V',loadY+98].join(' ')}
       stroke="#B9D5DB" strokeWidth="6" opacity=".13"/>)}
     <Text x={g.loadX} y={loadY+72} size={28} color="#FAF8F0">PESO</Text>
   </g>
   {/* Setas só aparecem quando existe força/deslocamento narrado. */}
   <g opacity={st.intent}>
     <path d={['M',302,786,'V',933].join(' ')}
       stroke={PAPER.gold} strokeWidth="10" strokeLinecap="round"/>
     <path d="M 284 910 L 302 947 L 320 910" stroke={PAPER.gold}
       strokeWidth="10" strokeLinejoin="round" fill="none"/>
     <Text x={300} y={772} color={PAPER.gold}>PUXAR</Text>
   </g>
   <g opacity={Math.min(1,st.travel/40)}>
     <path d="M 744 965 V 832" stroke={PAPER.teal} strokeWidth="10"
       strokeLinecap="round"/>
     <path d="M 725 859 L 744 821 L 763 859" fill="none"
       stroke={PAPER.teal} strokeWidth="10" strokeLinejoin="round"/>
     {/* A direção vem da seta e do deslocamento físico, sem rótulo sobre o peso. */}
   </g>
   {/* A conclusão causal fica no caption seguro, não em cima da caixa. */}
 </g>;
};

const polar=(cx:number,cy:number,r:number,angle:number):[number,number]=>
 [cx+Math.cos(angle)*r,cy+Math.sin(angle)*r];
export const gearOutline=(cx:number,cy:number,r:number,n:number)=>{
 const parts:string[]=[];
 // Perfil 2D de dentes radial, relação geométrica controlada por n.
 for(let i=0;i<n;i++){
   const a=i*2*Math.PI/n-Math.PI/2;
   const corners:[number,number][]=[
     polar(cx,cy,r*.925,a-.48*Math.PI/n),
     polar(cx,cy,r*1.025,a-.30*Math.PI/n),
     polar(cx,cy,r*1.025,a+.30*Math.PI/n),
     polar(cx,cy,r*.925,a+.48*Math.PI/n),
   ];
   corners.forEach(([x,y])=>parts.push((parts.length?'L':'M')+' '+x.toFixed(2)+' '+y.toFixed(2)));
 }
 return parts.join(' ')+' Z';
};
export const gearState=(t:number)=>{
 const v=probes.demo.gears,cues=asCues<GearAction>(v.cues),g=v.geometry;
 const cue=(name:GearAction)=>eventTime(cues,name)??100;
 const assembly=smooth((t-cue('assembly'))/.6);
 const showTeeth=smooth((t-cue('teeth'))/.55);
 const rotation=smooth((t-(cue('drive')+.18))/3.25)*g.driverTurnDegrees;
 const outputRotation=-(rotation*g.driverTeeth/g.drivenTeeth);
 const showRatio=smooth((t-cue('ratio'))/.5);
 const showResult=smooth((t-cue('result'))/.45);
 return {assembly,showTeeth,rotation,outputRotation,showRatio,showResult,
   current:eventAt(t,cues,cues[0]),cues,ratio:g.drivenTeeth/g.driverTeeth};
};
export const Gear:React.FC<{
  x:number;y:number;r:number;teeth:number;angle:number;fill:string;
  highlight:string;opacity:number;spokes?:number;cinematic?:boolean;
}>=({x,y,r,teeth,angle,fill,highlight,opacity,spokes=5,cinematic=false})=><g opacity={opacity}>
  <g transform={'rotate('+angle+' '+x+' '+y+')'}>
    {cinematic&&Array.from({length:8},(_,i)=><path key={i} d={gearOutline(x,y,r,teeth)} transform={`translate(${(8-i)*1.8} ${(8-i)*2.1})`} fill="#293239" stroke={i%2?'#667782':'#3B444B'} strokeWidth="1.8"/>)}
    <path d={gearOutline(x,y,r,teeth)} fill={fill}
      stroke={highlight} strokeWidth="6" strokeLinejoin="round"/>
    {cinematic&&<ASurfaceGrain id={'gear-grain-'+teeth} d={gearOutline(x,y,r,teeth)} kind="metal" opacity={.65}/>}
    <circle cx={x} cy={y} r={r*.74} fill="none"
      stroke={highlight} strokeWidth="4" opacity=".55"/>
    <circle cx={x} cy={y} r={r*.61} fill="none"
      stroke={PAPER.white} strokeWidth="3" opacity=".5"/>
    {Array.from({length:spokes},(_,i)=>{
      const a=i*Math.PI*2/spokes;
      const [x1,y1]=polar(x,y,r*.29,a),[x2,y2]=polar(x,y,r*.55,a);
      return <path key={i} d={['M',x1,y1,'L',x2,y2].join(' ')}
        stroke={PAPER.white} strokeWidth="21" strokeLinecap="round" opacity=".64"/>;
    })}
  </g>
  <circle cx={x} cy={y} r="35" fill="#28414E"
    stroke={PAPER.white} strokeWidth="7"/>
  <circle cx={x} cy={y} r="12" fill="#D6E3DD"/>
</g>;

const GearDrawing:React.FC<{t:number}>=({t})=>{
 const st=gearState(t),g=probes.demo.gears.geometry;
 const d=g.driverCenter,e=g.drivenCenter;
 return <g role="img" aria-label="Dois dentes de engrenagens transmitem rotacao em sentidos opostos e com velocidade inversa ao numero de dentes">
   {/* Mancais e dois eixos: montagem contínua, sem cartão de etapas. */}
   <path d="M 222 918 H 789" stroke="#B2A495" strokeWidth="15" strokeLinecap="round"/>
   <path d={['M',d[0],d[1],'V',916].join(' ')}
     stroke="#5B7A7E" strokeWidth="28" opacity=".28"/>
   <path d={['M',e[0],e[1],'V',916].join(' ')}
     stroke="#5B7A7E" strokeWidth="34" opacity=".25"/>
   <Gear x={d[0]} y={d[1]} r={g.driverRadius} teeth={g.driverTeeth}
     angle={st.rotation} fill="url(#paper-gold-metal)" highlight="#AD763E"
     opacity={st.assembly}/>
   <Gear x={e[0]} y={e[1]} r={g.drivenRadius} teeth={g.drivenTeeth}
     angle={st.outputRotation} fill="url(#paper-teal-metal)"
     highlight="#40757B" opacity={st.assembly}/>
   <g opacity={st.showTeeth}>
     <circle cx={d[0]+g.driverRadius} cy={d[1]} r="11"
       fill={PAPER.gold} stroke={PAPER.white} strokeWidth="3"/>
     <Text x={520} y={1022} size={22} color={PAPER.muted}>CONTATO DOS DENTES</Text>
   </g>
   <ArcArrow cx={d[0]} cy={d[1]} r={g.driverRadius+34}
     stroke={PAPER.gold} opacity={st.showRatio}/>
   <ArcArrow cx={e[0]} cy={e[1]} r={g.drivenRadius+33} reverse
     stroke={PAPER.teal} opacity={st.showRatio}/>
   <Text x={d[0]} y={967} color={PAPER.gold} size={24}>ENTRADA · {g.driverTeeth} DENTES</Text>
   <Text x={e[0]} y={967} color={PAPER.teal} size={24}>SAÍDA · {g.drivenTeeth} DENTES</Text>
   <g opacity={st.showResult}>
     <Text x={521} y={1058} color={PAPER.ink} size={26}>{st.ratio.toFixed(1).replace('.',',')}× TORQUE IDEAL</Text>
   </g>
 </g>;
};

export const Mechanism2DOtherModels:React.FC<Props>=({kind,private_review_only=true})=>{
 const frame=useCurrentFrame(),fps=useVideoConfig().fps,t=frame/fps;
 const isPulley=kind==='pulley';
 const a=isPulley?probes.demo.pulley:probes.demo.gears;
 const state=isPulley?pulleyState(t):gearState(t);
 const captions=a.cues;
 const idx=Math.max(0,captions.findIndex(c=>c.action===state.current.action));
 return <PaperLayout title={a.headline as [string,string]}
   section={a.section} index={idx+1} total={captions.length}
   caption={state.current.label} privateReviewOnly={private_review_only}>
   {isPulley?<PulleyDrawing t={t}/>:<GearDrawing t={t}/>}
 </PaperLayout>;
};
