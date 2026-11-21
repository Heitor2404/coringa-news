/** PROVA PRIVADA: linguagem técnica 2D-first para o motor documental.
 * A cena preserva uma barra/fulcro/carga/esforço físicos durante todo
 * o vídeo; o mesmo estado angular desloca a extremidade da carga e
 * a extremidade do esforço. NÃO é produção nem substitui o renderer
 * homologado. Nenhum elemento/gráfico do vídeo de referência foi copiado.
 */
import React from 'react';
import {AbsoluteFill,useCurrentFrame,useVideoConfig} from 'remotion';
import contract from './lever2d-contract.json';
import {
  clamp01,smooth,eventAt,eventTime,rotateAbout,leverAdvantage,
  type MechanismEvent,type Point2D
} from './Mechanism2DCore';

export type LeverPhase='introduce'|'load'|'effort'|'actuate'|'explain';
export type LeverGeometry={
  pivot:[number,number];beamStartX:number;beamEndX:number;beamThickness:number;
  loadX:number;loadWidth:number;loadHeight:number;
  effortX:number;maxTiltDeg:number;
};
export type LeverProps={
  duracao?:number;
  variant?:'paper'|'graphite';
  private_review_only?:boolean;
  cues?:MechanismEvent<LeverPhase>[];
  geometry?:Partial<LeverGeometry>;
};
const DEFAULT_CUES:MechanismEvent<LeverPhase>[]=
  contract.cues.map(c=>({at:c.at,action:c.action as LeverPhase,label:c.label}));
const DEFAULT_GEOMETRY:LeverGeometry={
  pivot:contract.geometry.pivot as [number,number],
  beamStartX:contract.geometry.beamStartX,
  beamEndX:contract.geometry.beamEndX,
  beamThickness:contract.geometry.beamThickness,
  loadX:contract.geometry.loadX,
  loadWidth:contract.geometry.loadWidth,
  loadHeight:contract.geometry.loadHeight,
  effortX:contract.geometry.effortX,
  maxTiltDeg:contract.geometry.maxTiltDeg,
};
type Palette={
  backgroundTop:string;backgroundBottom:string;floor:string;
  ink:string;muted:string;subtle:string;brand:string;
  teal:string;tealShade:string;metal:string;beamTop:string;beamBottom:string;
  load:string;loadFace:string;effort:string;label:string;
};
const palettes:Record<'paper'|'graphite',Palette>={
  paper:{
    backgroundTop:'#F1ECE1',backgroundBottom:'#E6DECF',floor:'#B5A591',
    ink:'#182A34',muted:'#53636A',subtle:'#A9A395',brand:'#C38B26',
    teal:'#3D8D92',tealShade:'#205A63',metal:'#F5F5EF',
    beamTop:'#DBB280',beamBottom:'#9F6942',
    load:'#273B47',loadFace:'#395668',effort:'#C88722',label:'#FFFFFF',
  },
  graphite:{
    backgroundTop:'#182730',backgroundBottom:'#101A23',floor:'#33434C',
    ink:'#F5F1E8',muted:'#A8BCC0',subtle:'#536873',brand:'#FFD21F',
    teal:'#5AB3BB',tealShade:'#276C7B',metal:'#F5F3E8',
    beamTop:'#DCB683',beamBottom:'#97653F',
    load:'#263B49',loadFace:'#577482',effort:'#FFD21F',label:'#FFFFFF',
  }
};
const font='Inter,Arial,sans-serif';

const Label:React.FC<{x:number;y:number;children:React.ReactNode;color:string;size?:number}>=
({x,y,children,color,size=26})=><text x={x} y={y} textAnchor="middle" fill={color}
  fontFamily={font} fontWeight="850" fontSize={size}>{children}</text>;

const VerticalArrow:React.FC<{
  x:number;from:number;to:number;color:string;up?:boolean;opacity:number
}>=({x,from,to,color,up=false,opacity})=><g opacity={opacity}>
  <line x1={x} y1={from} x2={x} y2={to}
    stroke={color} strokeWidth="9" strokeLinecap="round"/>
  <path d={up?
    `M${x-18} ${to+23} L${x} ${to-5} L${x+18} ${to+23}`:
    `M${x-18} ${to-23} L${x} ${to+5} L${x+18} ${to-23}`}
    fill="none" stroke={color} strokeWidth="9" strokeLinejoin="round"
    strokeLinecap="round"/>
</g>;

/** Configuração ilustrativa de uma alavanca ideal de 1a classe.
 * Diagrama NÃO é simulação de massas reais: o equilíbrio e os esforços
 * dependem de torque; a rotação aqui apenas demonstra o sentido.
 */
export const leverVisualState=(
  t:number,
  cues:readonly MechanismEvent<LeverPhase>[],
  cfg:LeverGeometry,
)=>{
  const fallback=cues[0]||{at:0,action:'introduce' as LeverPhase,label:'ALAVANCA'};
  const active=eventAt(t,cues,fallback);
  const cue=(a:LeverPhase)=>eventTime(cues,a)??Number.POSITIVE_INFINITY;
  const assembled=smooth((t-cue('introduce'))/.58);
  const loaded=smooth((t-cue('load'))/.46);
  const effort=smooth((t-cue('effort'))/.54);
  const move=smooth((t-cue('actuate'))/1.96);
  const explained=smooth((t-cue('explain'))/.45);
  const tilt=cfg.maxTiltDeg*move;
  const pivot:Point2D={x:cfg.pivot[0],y:cfg.pivot[1]};
  const loadPoint=rotateAbout(pivot,{x:cfg.loadX,y:pivot.y},tilt);
  const effortPoint=rotateAbout(pivot,{x:cfg.effortX,y:pivot.y},tilt);
  return {active,assembled,loaded,effort,move,explained,tilt,
    loadPoint,effortPoint,pivot,
    advantage:leverAdvantage(pivot.x,cfg.loadX,cfg.effortX)};
};

export const LeverMechanism2D:React.FC<LeverProps>=({
  variant='paper',private_review_only=true,cues=DEFAULT_CUES,
  geometry,
})=>{
  const frame=useCurrentFrame();
  const fps=useVideoConfig().fps;
  const t=frame/fps;
  const cfg:LeverGeometry={...DEFAULT_GEOMETRY,...geometry};
  const s=leverVisualState(t,cues,cfg);
  const p=palettes[variant];
  const {pivot,assembled,loaded,effort,explained,loadPoint,effortPoint,tilt}=s;
  const currentIndex=cues.findIndex(c=>c.action===s.active.action);
  const stepIndex=Math.max(0,currentIndex)+1;
  const crateY=loadPoint.y-cfg.beamThickness/2-cfg.loadHeight;
  const rightY=effortPoint.y;
  const stage=contract.qa.actorStage;
  const stageTransform=`translate(${stage.origin[0]*(1-stage.scaleX)} ${stage.origin[1]*(1-stage.scaleY)}) scale(${stage.scaleX} ${stage.scaleY})`;
  const loadTopIn=crateY-(1-loaded)*35;
  return <AbsoluteFill style={{
    background:p.backgroundTop,fontFamily:font,overflow:'hidden',color:p.ink
  }}>
    <svg width="100%" height="100%" viewBox="0 0 1080 1920"
      preserveAspectRatio="xMidYMid meet" aria-label="Demonstração original de alavanca 2D: o braço da força desce e a carga no braço curto sobe">
      <defs>
        <linearGradient id="lever-backdrop" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor={p.backgroundTop}/>
          <stop offset="1" stopColor={p.backgroundBottom}/>
        </linearGradient>
        <linearGradient id="lever-wood" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor={p.beamTop}/>
          <stop offset=".48" stopColor="#CAA075"/>
          <stop offset="1" stopColor={p.beamBottom}/>
        </linearGradient>
        <linearGradient id="lever-metal" x1="0" y1="0" x2="1" y2="1">
          <stop stopColor={p.teal}/>
          <stop offset="1" stopColor={p.tealShade}/>
        </linearGradient>
        <linearGradient id="lever-crate" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor={p.loadFace}/>
          <stop offset="1" stopColor={p.load}/>
        </linearGradient>
        <linearGradient id="lever-floor" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor={p.floor} stopOpacity=".22"/>
          <stop offset="1" stopColor={p.floor} stopOpacity=".06"/>
        </linearGradient>
      </defs>

      {/* Ambiente é o próprio plano de apoio da alavanca, não uma
          camada de hologramas, grades ou objetos decorativos sem função. */}
      <rect x="0" y="0" width="1080" height="1920" fill="url(#lever-backdrop)"/>
      <rect x="0" y="1074" width="1080" height="846" fill="url(#lever-floor)"/>
      <path d="M95 1073 H983" stroke={p.subtle} strokeWidth="4" opacity=".65"/>
      <g data-safe-role="mechanism-actors" transform={stageTransform}>
      <ellipse cx={pivot.x+3} cy="1072" rx="187" ry="16"
        fill={p.ink} opacity=".12"/>

      {/* A estrutura NÃO troca de lugar em cada cue. */}
      <g opacity={assembled}>
        <path d={`M${pivot.x} ${pivot.y+14} L${pivot.x-83} 1035 L${pivot.x+83} 1035Z`}
          fill="url(#lever-metal)" stroke={p.tealShade} strokeWidth="6" strokeLinejoin="round"/>
        <path d={`M${pivot.x} ${pivot.y+50} L${pivot.x+43} 1015 H${pivot.x+62}Z`}
          fill={p.metal} opacity=".10"/>
        <rect x={pivot.x-105} y="1030" width="210" height="24" rx="8"
          fill={p.tealShade}/>
        <rect x={pivot.x-93} y="1027" width="186" height="9" rx="4"
          fill={p.teal} opacity=".75"/>
      </g>

      {/* A linha fantasma marca a posição inicial, permitindo que a subida
          seja compreendida sem segundo diagrama ou card. */}
      <path d={`M${cfg.beamStartX} ${pivot.y} H${cfg.beamEndX}`}
        fill="none" stroke={p.muted} strokeWidth="4"
        strokeDasharray="12 16" opacity={s.move*.26}/>
      {/* A barra gira rígida em volta da mesma âncora que governa a carga
          e a ponta do esforço: geometria física única, sem animações fake. */}
      <g opacity={assembled} transform={`rotate(${tilt} ${pivot.x} ${pivot.y})`}>
        <rect x={cfg.beamStartX} y={pivot.y-cfg.beamThickness/2+8}
          width={cfg.beamEndX-cfg.beamStartX} height={cfg.beamThickness}
          rx={cfg.beamThickness/2} fill={p.load} opacity=".16"/>
        <rect x={cfg.beamStartX} y={pivot.y-cfg.beamThickness/2}
          width={cfg.beamEndX-cfg.beamStartX} height={cfg.beamThickness}
          rx={cfg.beamThickness/2} fill="url(#lever-wood)"
          stroke={p.beamBottom} strokeWidth="3"/>
        <path d={`M${cfg.beamStartX+22} ${pivot.y-7} H${cfg.beamEndX-26}`}
          stroke="#FFF0D3" strokeWidth="4" opacity=".51" strokeLinecap="round"/>
        {/* A própria barra revela os braços curtos e longos no resultado. */}
        <path d={`M${cfg.loadX} ${pivot.y+4} H${pivot.x}`}
          stroke={p.teal} strokeWidth="8" strokeLinecap="round" opacity={explained*.9}/>
        <path d={`M${pivot.x} ${pivot.y+4} H${cfg.effortX}`}
          stroke={p.effort} strokeWidth="8" strokeLinecap="round" opacity={explained*.92}/>
        {[cfg.beamStartX+26,cfg.beamEndX-28].map(x=>
          <circle key={x} cx={x} cy={pivot.y} r="6" fill={p.beamBottom} opacity=".48"/>)}
      </g>

      {/* Carga mantém orientação vertical e repousa sobre a barra. */}
      <g opacity={loaded}>
        <rect x={loadPoint.x-cfg.loadWidth/2+6} y={loadTopIn+8}
          width={cfg.loadWidth} height={cfg.loadHeight} rx="7"
          fill={p.ink} opacity=".16"/>
        <rect x={loadPoint.x-cfg.loadWidth/2} y={loadTopIn}
          width={cfg.loadWidth} height={cfg.loadHeight}
          rx="7" fill="url(#lever-crate)"
          stroke={p.metal} strokeWidth="4"/>
        <path d={`M${loadPoint.x-cfg.loadWidth/2+12} ${loadTopIn+15} H${loadPoint.x+cfg.loadWidth/2-13}`}
          stroke="#C9DDE5" strokeWidth="4" opacity=".32" strokeLinecap="round"/>
        {/* Reforços visuais fazem da carga um corpo físico, não um cartão. */}
        <path d={`M${loadPoint.x-cfg.loadWidth/2+18} ${loadTopIn+35} L${loadPoint.x+cfg.loadWidth/2-18} ${loadTopIn+94}`}
          fill="none" stroke={p.metal} strokeWidth="4" opacity=".19"/>
        {[[-47,21],[47,21],[-47,92],[47,92]].map(([dx,dy],i)=>
          <circle key={i} cx={loadPoint.x+dx} cy={loadTopIn+dy}
            r="3.5" fill="#C9E0E7" opacity=".62"/>)}
        <Label x={loadPoint.x} y={loadTopIn+70} size={29} color={p.label}>CARGA</Label>
      </g>
      <g opacity={assembled}>
        <circle cx={pivot.x} cy={pivot.y} r="21" fill={p.tealShade}
          stroke={p.metal} strokeWidth="5"/>
        <circle cx={pivot.x} cy={pivot.y} r="8" fill={p.metal}/>
        <path d={`M${pivot.x-19} 988 H${pivot.x+19}`}
          stroke={p.metal} strokeWidth="4" opacity=".45"/>
        <Label x={pivot.x} y={1008} size={24} color={p.metal}>APOIO</Label>
      </g>

      {/* Um esforço longo à direita causa subida do lado curto.
          A seta segue a ponta deslocada, não outra timeline. */}
      <g opacity={effort}>
        <Label x={878} y={539} size={29} color={p.effort}>FORÇA</Label>
        <VerticalArrow x={effortPoint.x} from={559}
          to={559+(rightY-42-559)*effort}
          color={p.effort} opacity={1}/>
      </g>
      <g opacity={s.move*.92}>
        <VerticalArrow x={loadPoint.x+cfg.loadWidth/2+43} from={loadPoint.y+92}
          to={loadPoint.y-66} up color={p.tealShade} opacity={1}/>
      </g>
      {/* Medidas só aparecem quando a rotação acabou; são derivadas dos
          mesmos braços geométricos, sem fórmula ou cartão inventado.
          O traço de destaque na barra conserva a continuidade causal. */}
      {/* Duas medidas acima da barra, conectadas às extremidades e ao pivô.
          Nunca cruzar o suporte ou ocupar a faixa das legendas. */}
      <g opacity={explained}>
        <Label x={pivot.x-97} y={618} color={p.tealShade} size={21}>BRAÇO CURTO</Label>
        <Label x={pivot.x+224} y={615} color={p.effort} size={23}>BRAÇO LONGO</Label>
        <Label x={pivot.x+224} y={652} color={p.ink} size={22}>
          {s.advantage.toFixed(1).replace('.',',')}× O BRAÇO CURTO
        </Label>
      </g>
      </g>
    </svg>

    {/* Hierarquia editorial fora do SVG físico. Sem ticker/card,
        e nenhum texto essencial nas zonas orgânicas de ícones. */}
    <div style={{position:'absolute',left:157,top:300,width:610,
      display:'flex',alignItems:'center',gap:7,
      fontSize:25,fontWeight:900,letterSpacing:.5}}>
      CORINGA <span style={{color:p.brand}}>EXPLICA</span>
    </div>
    <div style={{position:'absolute',left:159,top:347,width:610,
      color:p.muted,fontSize:22,fontWeight:780,letterSpacing:1.9}}>
      MECÂNICA · 2D
    </div>
    <div style={{position:'absolute',left:156,top:378,width:670,
      fontSize:50,lineHeight:1.04,fontWeight:900,letterSpacing:-1.3}}>
      COMO UMA BARRA
      <div>LEVANTA UMA CARGA?</div>
    </div>
    <div style={{position:'absolute',left:156,top:1095,width:600,
      borderTop:`2px solid ${p.subtle}`,paddingTop:12}}>
      <div style={{color:p.effort,fontSize:20,fontWeight:850,letterSpacing:1.4,
        marginBottom:8}}>
        {String(stepIndex).padStart(2,'0')} / {String(cues.length).padStart(2,'0')}
      </div>
      <div style={{fontSize:s.active.label.length>38?30:36,
        lineHeight:1.09,letterSpacing:-.5,fontWeight:900,
        maxWidth:600}}>
        {s.active.label}
      </div>
    </div>
    <div style={{position:'absolute',left:156,top:1220,width:603,
      fontSize:17.5,fontWeight:650,color:p.muted,lineHeight:1.1}}>
      ESQUEMA AUTORAL · ALAVANCA IDEALIZADA, SEM ATRITO
    </div>
    {private_review_only&&<div style={{position:'absolute',
      left:0,right:0,bottom:58,textAlign:'center',letterSpacing:1.5,
      fontSize:19,fontWeight:700,color:p.muted,opacity:.7}}>
      PROVA VISUAL PRIVADA · NÃO PUBLICAR
    </div>}
  </AbsoluteFill>;
};
