/** FILME EDITORIAL — compositor visual-first independente do ATLAS de cartões.
 * Stage 0: documentação real preenchendo a tela; câmera e revelações de cada assunto.
 * Não há palco-mapa persistente, slots pequenos, nem fluxo de cards como ação.
 * Todos os títulos vêm do roteiro; o compositor não inventa fatos.
 */
import React from 'react';
import {LockCausal} from './LockCausal';
import {LockCausalCycle} from './LockCausalCycle';
import {MotionEditorial, type MotionEditorialData} from './MotionEditorial';
import {OpticalProjection} from './OpticalProjection';
import safety from './safe-zones-vertical.json';
import {AbsoluteFill, Img, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

export type Cue = {at: number; label: string; kind?: 'callout' | 'fact'; x?: number; y?: number; action?: 'closed' | 'water_enter' | 'rise' | 'equalize' | 'release' | 'enter' | 'seal' | 'valves' | 'open' | 'exit'};
export type FilmShot = {
  id: string;
  start: number;
  end: number;
  type: 'photo' | 'video' | 'comparison' | 'mechanism' | 'atlas_map';
  asset?: string; // caminho relativo a motor4/remotion/public, verificado pelo preflight Python
  assetB?: string;
  source_in_seconds?: number; // corte verdadeiro dentro do master local do arquivo
  video_zoom?: number; // enquadramento dirigido para o portão, não zoom decorativo
  video_context_layout?: 'quadro_integral' | 'cena_integral' | 'recorte_relacional_seguro'; // inferido pelo preflight das bboxes de TODOS os referentes
  // Calculado pelo preflight Python a partir de ROIs observadas no original.
  // Posições normais CSS object-position, não pixels falsamente interpolados.
  framing_positions?: {at:number; position:[number,number]}[];
  graphic_original?: boolean; // Infografia autoral com dados embutidos, sem título duplicado
  motion_graphic?: MotionEditorialData; // Dados editoriais animados; não cria fatos
  compareLabels?: [string, string]; // story-specific, never hard-code Taiwan into engine
  source: string;
  source_display?: string; // crédito curto em tela, URL integral nos props
  sourceB?: string;
  evidence: 'literal' | 'representative' | 'explainer';
  mechanism?: 'lock_filling' | 'lock_causal' | 'lock_cycle' | 'lock_cycle_standalone' | 'lock_explainer' | 'optical_projection';
  reference_asset?: string;
  reference_from_seconds?: number;
  subject: string;
  // O crop é uma escolha de DIREÇÃO: coordenadas normalizadas do objeto central.
  focus?: [number, number];
  focusB?: [number, number];
  lead: string;
  headline: string;
  highlight?: string;
  cues?: Cue[];
};
export type FilmProps = {
  duracao: number;
  shots: FilmShot[];
  label?: string;
  // Em prévia privada não há voz; o runtime pode acrescentar camada de narração
  // e legenda separadamente depois do plano aprovado.
  preview?: boolean;
  private_review_only?: boolean;
  safe_zone_debug?: boolean; // somente QA, nunca publicar o overlay vermelho
  subtitle_mode?: boolean; // quando a Camada de fala está presente, ela ocupa lane própria
  safe_area_profile?: 'MULTIPLATAFORMA_CONSERVADOR_V1';
  direitos_pendentes?: string[];
};

const W = 1080, H = 1920;
const OFF_WHITE = '#F5F2EB', GOLD = '#FFD21F';
const SAFE = safety.slots;
type SlotName = keyof typeof SAFE;
const safeSlot=(part: SlotName): React.CSSProperties => {
  const [left,top,right,bottom] = SAFE[part];
  return {position:'absolute',left,top,width:right-left,height:bottom-top};
};
const squareStage = safeSlot('visual');
/** O componente declara o enquadramento e as ações; o episódio só fornece cues.
 * Não confundir zoom editorial com validação pixel-a-pixel de personagens móveis.
 */
const MECH = safety.mechanism_layout;
const rectStyle = (r: readonly number[]):React.CSSProperties=>({
  position:'absolute',left:r[0],top:r[1],width:r[2]-r[0],height:r[3]-r[1],
});
const lerpRect=(a:readonly number[],b:readonly number[],p:number):number[] =>
  a.map((v,i)=>v+(b[i]-v)*p);
const mecanismoFoco=(shot:FilmShot,segundo:number):number[]=>{
  const catalog=MECH.focus as Record<string,Record<string,number[]>>;
  const camera=catalog[shot.mechanism||''] || {};
  const padrao=camera.default||MECH.default_bounds;
  const stages=(shot.cues||[]).filter(c=>c.action && camera[c.action])
    .slice().sort((a,b)=>a.at-b.at);
  const atual=stages.filter(c=>c.at<=segundo).slice(-1)[0];
  if(!atual?.action) return padrao;
  const idx=stages.indexOf(atual);
  const antes=idx>0 && stages[idx-1].action ? camera[stages[idx-1].action!] : camera[atual.action];
  const alvo=camera[atual.action];
  const trans=idx>0?ease((segundo-atual.at)/MECH.transition_seconds):1;
  return lerpRect(antes||padrao,alvo,trans);
};

const clamp = (n: number, a=0, b=1) => Math.max(a, Math.min(b, n));
const ease = (v: number) => 1 - Math.pow(1 - clamp(v), 3);

const enquadramentoNoTempo = (
  posicoes: {at:number;position:[number,number]}[] | undefined,
  segundo: number,
  padrao:[number,number],
):[number,number] => {
  if (!posicoes?.length) return padrao;
  if (segundo<=posicoes[0].at) return posicoes[0].position;
  for(let i=1;i<posicoes.length;i++){
    const anterior=posicoes[i-1], atual=posicoes[i];
    if (segundo<=atual.at){
      // Movimento da câmera apenas acompanha a área curada; não é
      // considerado progressão de conteúdo pelo fiscal.
      const frac=clamp((segundo-anterior.at)/Math.max(.001,atual.at-anterior.at));
      return [
        anterior.position[0]+(atual.position[0]-anterior.position[0])*frac,
        anterior.position[1]+(atual.position[1]-anterior.position[1])*frac
      ];
    }
  }
  return posicoes[posicoes.length-1].position;
};

const photograph = (asset: string, p: number, focus: [number,number], travel: number, side: 'full'|'left'|'right'='full') => {
  const zoom = 1.04 + ease(p)*0.13;
  // subject full-bleed, zoom subtly; the image NEVER becomes a 500px photo card.
  const cx = (focus[0] - 0.5) * 32 * ease(p);
  const cy = (focus[1] - 0.5) * 16 * ease(p);
  return <Img src={staticFile(asset)} style={{
    position:'absolute', left:0, top:0, width:'100%', height:'100%',
    objectFit:'cover', objectPosition:`${focus[0]*100}% ${focus[1]*100}%`,
    transform:`translate3d(${-cx}%,${-cy}%,0) scale(${zoom + travel}, ${zoom+travel})`,
    transformOrigin:`${focus[0]*100}% ${focus[1]*100}%`,
    filter:'brightness(.84) saturate(1.02) contrast(1.06)',
  }}/>;
};
/** Não é um vídeo da eclusa real: simulação ilustrativa do princípio de funcionamento.
 * Os movimentos SÃO o conteúdo: o nível de água sobe e arrasta o casco.
 */
const LockFilling: React.FC<{p:number}> = ({p}) => {
  const progress=ease((p-.11)/.74), waterY=1095-275*progress;
  const surfWave=Math.sin(p*37)*3;
  return <AbsoluteFill style={{background:'radial-gradient(ellipse at 50% 42%,#12273A,#06101D 75%)'}}>
    <svg viewBox="0 0 1080 1920" width="100%" height="100%" style={{fontFamily:'Inter, Arial, sans-serif'}} aria-label="Esquema ilustrativo: a água entra, sobe e eleva o navio dentro da eclusa">
      <defs>
        <linearGradient id="lock-water" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#55C8E4" stopOpacity=".88"/>
          <stop offset="100%" stopColor="#145477" stopOpacity=".95"/>
        </linearGradient>
        <pattern id="lock-grid" width="62" height="62" patternUnits="userSpaceOnUse">
          <path d="M62 0H0V62" stroke="#5C829A" strokeOpacity=".14" fill="none" strokeWidth="1.7"/>
        </pattern>
      </defs>
      <rect width="1080" height="1920" fill="url(#lock-grid)"/>
      <text x="90" y="440" fill="#F3F2ED" fontSize="45" fontWeight="900">COMO FUNCIONA UMA ECLUSA</text>
      <rect x="130" y="595" width="820" height="610" fill="#08121F" stroke="#7A9BAE" strokeWidth="3"/>
      <rect x="180" y="670" width="720" height="510" fill="#091726"/>
      <rect x="180" y={waterY+surfWave} width="720" height={1180-waterY-surfWave} fill="url(#lock-water)"/>
      {Array.from({length:5},(_,i)=><path key={i} d={`M ${198+i*140} ${waterY+surfWave+25} h 68`}
        fill="none" stroke="#A3E6F1" strokeWidth="4" opacity={.45}/>)}
      <path d="M 170 595 V 1220 H 210 V 670 H 170 Z" fill="#7A8D9B"/>
      <path d="M 870 670 V 1220 H 910 V 595 H 870 Z" fill="#7A8D9B"/>
      <g transform={`translate(0,${waterY-90})`}>
        <path d="M 328 35 L 743 35 L 704 102 L 373 102 Z" fill="#D5DCE1" stroke="#ECF4F7" strokeWidth="4"/>
        <rect x="408" y="-38" width="270" height="72" rx="6" fill="#F4F3EF" stroke="#96B0BA" strokeWidth="3"/>
        <rect x="438" y="-70" width="205" height="30" rx="4" fill="#EDF1F2"/>
        <rect x="524" y="-116" width="14" height="47" fill="#C8E4EA"/>
        {Array.from({length:5},(_,i)=><rect key={i} x={445+i*44} y="-12" width="30" height="19" rx="3" fill="#1B4E68"/>)}
      </g>
      <path d={`M 280 ${1095} H 790`} stroke="#C4D8E0" strokeWidth="3" strokeDasharray="15 12" opacity=".24"/>
      <path d={`M 780 1095 V ${waterY}`} stroke="#FFD21F" strokeWidth="8" strokeDasharray="14 9" opacity={progress>.04?1:.1}/>
      <path d={`M 780 ${waterY-12} l -19 31 h 38 Z`} fill="#FFD21F" opacity={progress>.04?1:.1}/>
      {progress>.15 && <text x="540" y="550" fill="#FFD21F" fontSize="36" fontWeight="900" textAnchor="middle">NAVIO SOBE COM A ÁGUA</text>}
      <path d="M 210 1140 H 340" stroke="#FFD21F" strokeWidth="13" opacity=".83"/>
      <path d="M 345 1140 l-32 -21 v42 Z" fill="#FFD21F"/>

    </svg>
  </AbsoluteFill>;
};

const Body: React.FC<{shot: FilmShot;p:number;t:number}> = ({shot,p,t}) => {
  if(shot.type==='mechanism' && shot.mechanism==='optical_projection')
    return <OpticalProjection t={t} events={shot.cues || []}/>;
  if(shot.type==='mechanism' && shot.mechanism==='lock_explainer')
    return <LockCausal t={t} events={(shot.cues || []).map(c => ({
      at:c.at,label:c.label,action:c.action as 'closed' | 'water_enter' | 'rise' | 'equalize' | 'release' | undefined
    }))} visualMode="editorial"/>;
  if(shot.type==='mechanism' && ['lock_cycle','lock_cycle_standalone'].includes(shot.mechanism || ''))
    return <LockCausalCycle t={t} events={shot.cues || []}
      referenceAsset={shot.mechanism==='lock_cycle'?shot.reference_asset:undefined}
      duration={shot.end-shot.start}/>;
  if(shot.type==='mechanism' && shot.mechanism==='lock_causal')
    return <LockCausal t={t} events={(shot.cues || []).map(c => ({
      at:c.at,label:c.label,action: c.action as 'closed' | 'water_enter' | 'rise' | 'equalize' | 'release' | undefined
    }))} referenceAsset={shot.reference_asset}/>;
  if(shot.type==='mechanism'&&shot.mechanism==='lock_filling')
    return <LockFilling p={p}/>;
  if(shot.type === 'atlas_map') {
    // É um MP4 do Formato/PalcoMapa ORIGINAL, com seu próprio raster, créditos,
    // destaques e câmera. Nunca redesenhar mapa, crop ou duplicar títulos.
    return <AbsoluteFill><Sequence from={Math.round(shot.start*30)}
      durationInFrames={Math.ceil((shot.end-shot.start)*30)}>
      <OffthreadVideo src={staticFile(shot.asset || '')} muted
        style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'contain'}}/>
    </Sequence></AbsoluteFill>;
  }
  if(shot.type === 'video') {
    if(shot.video_context_layout==='quadro_integral') {
      // Cameras quadradas de missões, bancadas e registros de processos:
      // preservar o arquivo INTEIRO, sem aplicar object-fit:cover.
      // Nunca falsificar continuidade temporal do original.
      return <AbsoluteFill style={{background:'linear-gradient(180deg,#112536 0%,#07121E 75%,#050A12 100%)'}}>
        <div data-safe-role="visual" style={{...squareStage,
          overflow:'hidden',background:'#061320',border:'2px solid #456273'}}>
          <Sequence from={Math.round(shot.start*30)}
            durationInFrames={Math.ceil((shot.end-shot.start)*30)}>
            <OffthreadVideo src={staticFile(shot.asset || '')} muted
              startFrom={Math.max(0,Math.round((shot.source_in_seconds||0)*30))}
              style={{position:'absolute',width:'100%',height:'100%',objectFit:'contain'}}/>
          </Sequence>
        </div>
      </AbsoluteFill>;
    }
    if(shot.video_context_layout==='cena_integral') {
      // Filme horizontal contextualmente importante: fonte completa preserva
      // pesquisador E equipamento. Não duplique o clipe no fundo desfocado.
      // A horizontalidade é honesta; nunca cortar o conteúdo para preencher 9:16.
      return <AbsoluteFill style={{background:'linear-gradient(180deg,#12293D 0%,#07121E 55%,#050A12 100%)'}}>
        <div data-safe-role="visual" style={{...squareStage,
          overflow:'hidden',background:'#07131D',
          borderTop:'3px solid #456273',borderBottom:'3px solid #456273'}}> 
          <Sequence from={Math.round(shot.start*30)}
            durationInFrames={Math.ceil((shot.end-shot.start)*30)}>
            <OffthreadVideo src={staticFile(shot.asset || '')} muted
              startFrom={Math.max(0,Math.round((shot.source_in_seconds||0)*30))}
              style={{position:'absolute',width:'100%',height:'100%',
                      objectFit:'contain'}}/>
          </Sequence>
        </div>
      </AbsoluteFill>;
    }
    const position=enquadramentoNoTempo(shot.framing_positions,t,shot.focus||[.5,.5]);
    return <AbsoluteFill><Sequence from={Math.round(shot.start * 30)}
      durationInFrames={Math.ceil((shot.end - shot.start) * 30)}>
      <OffthreadVideo src={staticFile(shot.asset || '')} muted
        startFrom={Math.max(0, Math.round((shot.source_in_seconds || 0) * 30))}
        style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover',
          objectPosition:`${position[0]*100}% ${position[1]*100}%`,
          filter:'brightness(.98) saturate(1.04)',
          transform:shot.framing_positions?.length?'none':`scale(${shot.video_zoom || 1})`,
          transformOrigin:'50% 30%'}}/>
    </Sequence></AbsoluteFill>;
  }
  if(shot.type === 'comparison' && shot.assetB) {
    const right = clamp((p-.13)/.44);
    return <AbsoluteFill>
      <div style={{position:'absolute',inset:0,overflow:'hidden'}}>{photograph(shot.asset || '',p,shot.focus||[.5,.5],.02)}</div>
      <div style={{position:'absolute',inset:0,clipPath:`inset(0 ${(1-right)*100}% 0 0)`}}>
        {photograph(shot.assetB,p,shot.focusB||[.5,.5],0)}
      </div>
      {right>.04 && <div style={{position:'absolute',left:`${right*100}%`,top:0,bottom:0,width:4,background:GOLD,boxShadow:`0 0 22px ${GOLD}`}}/>}
      <div style={{position:'absolute',top:470,left:42,background:'rgba(5,14,24,.85)',padding:'9px 18px',fontWeight:900,fontSize:31,letterSpacing:1.2,color:OFF_WHITE}}>{shot.compareLabels?.[0] || 'ANTES'}</div>
      {right>.6 && <div style={{position:'absolute',top:470,right:42,background:'rgba(5,14,24,.85)',padding:'9px 18px',fontWeight:900,fontSize:31,letterSpacing:1.2,color:GOLD}}>{shot.compareLabels?.[1] || 'DEPOIS'}</div>}
    </AbsoluteFill>;
  }
  if (shot.type === 'photo' && shot.graphic_original && shot.motion_graphic) {
    return <MotionEditorial data={shot.motion_graphic} p={p}/>;
  }
  if (shot.type === 'photo' && shot.graphic_original) {
    // Infográfico com seus próprios títulos, rótulos e dados. NÃO zoom
    // progressivo: isso cortaria palavras e números no formato vertical.
    return <AbsoluteFill><Img src={staticFile(shot.asset || '')}
      style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'contain'}}/></AbsoluteFill>;
  }
  return <AbsoluteFill>{photograph(shot.asset || '',p,shot.focus||[.5,.5],.01)}</AbsoluteFill>;
};
/** Conteúdo visual real ocupa uma janela protegida; o resto continua
 * como FUNDO cênico, sem afirmar que detalhes nas bordas são essenciais.
 * Mecanismos 2D são reenquadrados pelo tipo de renderizador, nunca pelo tema.
 */
const SafeBody: React.FC<{shot:FilmShot;p:number;t:number;subtitleMode:boolean}> = ({shot,p,t,subtitleMode}) => {
  if (shot.type==='mechanism') {
    // Close editorial de uma ETAPA, não redução de todo o SVG original.
    // Bounding boxes vêm do catálogo do componente, nunca do nome do tema.
    const palco=subtitleMode?SAFE.visual:MECH.visual;
    const [sx,sy,ex,ey]=mecanismoFoco(shot,t);
    const dw=palco[2]-palco[0],dh=palco[3]-palco[1];
    const scale=Math.min(dw/(ex-sx),dh/(ey-sy));
    // Enforce both source ROI AND destination safe box. Otherwise headers
    // outside the source bounds bleed into the padded stage and duplicate
    // the public title, despite a green safe-area report.
    const left=(dw-(ex-sx)*scale)/2;
    const top=(dh-(ey-sy)*scale)/2;
    return <AbsoluteFill style={{background:'radial-gradient(ellipse at 50% 54%,#173047,#0B1D2D 52%,#050F1C 100%)'}}>
      <AbsoluteFill style={{opacity:.10,backgroundSize:'94px 94px',
        backgroundImage:'linear-gradient(to right,#7A9FB4 1px,transparent 1px),linear-gradient(to bottom,#7A9FB4 1px,transparent 1px)'}}/>
      <div data-safe-role="visual" style={{...rectStyle(palco),overflow:'hidden'}}>
        <div style={{position:'absolute',left,top,width:ex-sx,height:ey-sy,
          overflow:'hidden',transform:`scale(${scale})`,transformOrigin:'top left'}}>
          <div style={{position:'absolute',left:-sx,top:-sy,width:1080,height:1920}}>
            <Body shot={shot} p={p} t={t}/>
          </div>
        </div>
      </div>
    </AbsoluteFill>;
  }
  if (shot.graphic_original && shot.motion_graphic) {
    // Gráficos autorais conservam o enquadramento anterior até serem
    // certificados separadamente. Não aplicar câmera de mecanismo a dados.
    const scale=.565,sourceY=450;
    const dw=SAFE.visual[2]-SAFE.visual[0],dh=SAFE.visual[3]-SAFE.visual[1];
    const left=(dw-1080*scale)/2;
    const top=-sourceY*scale;
    return <AbsoluteFill style={{background:'#0B1D2D'}}>
      <div data-safe-role="visual" style={{...safeSlot('visual'),overflow:'hidden'}}>
        <div style={{position:'absolute',left,top,width:1080,height:1920,
          transform:`scale(${scale})`,transformOrigin:'top left'}}>
          <Body shot={shot} p={p} t={t}/>
        </div>
      </div>
    </AbsoluteFill>;
  }
  if (shot.type==='comparison' || (shot.type==='photo' && shot.graphic_original)) {
    return <AbsoluteFill style={{background:'#071523'}}>
      <div data-safe-role="visual" style={{...safeSlot('visual'),overflow:'hidden'}}>
        <Body shot={shot} p={p} t={t}/>
      </div>
    </AbsoluteFill>;
  }
  return <Body shot={shot} p={p} t={t}/>;
};
const Caption: React.FC<{text:string; highlighted?:string}> = ({text,highlighted}) => {
  const total=text.replace(/\n/g,' ').length;
  const size=total>53?31:total>40?35:total>26?39:43;
  const parts=highlighted?text.split(highlighted):[text];
  return <div style={{fontFamily:'Inter,Arial,sans-serif',fontSize:size,
    lineHeight:1.07,fontWeight:900,textTransform:'uppercase',
    letterSpacing:-.8,whiteSpace:'pre-line',overflowWrap:'break-word'}}>
    {parts.map((part,i)=><React.Fragment key={i}>{part}{highlighted&&i<parts.length-1&&
      <span style={{color:GOLD}}>{highlighted}</span>}</React.Fragment>)}
  </div>;
};

const FilmShotView: React.FC<{shot:FilmShot;total:number;index:number;subtitleMode:boolean}> = ({shot,subtitleMode}) => {
  const frame=useCurrentFrame(),fps=useVideoConfig().fps;
  const now=frame/fps;
  const duration=Math.max(.01,shot.end-shot.start);
  const p=clamp((now-shot.start)/duration);
  const active=shot.cues?.filter(c=>now>=shot.start+c.at).slice(-1)[0];
  const age=active?now-shot.start-active.at:0;
  if(shot.type==='atlas_map') {
    // O clip ATLAS antigo tem tipografia/attribution rasterizadas internamente.
    // Não fingir que o render está homologado pela área segura nova.
    // Gate Python bloqueia safe_area_profile em atlas_map até recertificação.
    return <AbsoluteFill style={{background:'#08101A'}}>
      <Body shot={shot} p={p} t={now-shot.start}/>
    </AbsoluteFill>;
  }
  return <AbsoluteFill style={{background:'#08101A',overflow:'hidden'}}>
    <SafeBody shot={shot} p={p} t={now-shot.start} subtitleMode={subtitleMode}/>
    {!shot.graphic_original&&shot.type!=='mechanism'&&shot.type!=='video'&&
      <AbsoluteFill style={{pointerEvents:'none',background:
        'linear-gradient(180deg,rgba(3,8,16,.38),transparent 40%,rgba(3,8,16,.68))'}}/>}
    {/* Camada editorial universal. Não repetir logo+linha no topo de cada card. */}
    <div data-safe-role="brand" style={{...safeSlot('brand'),
      fontFamily:'Inter,Arial,sans-serif',fontSize:26,fontWeight:900,
      color:OFF_WHITE,letterSpacing:.8,whiteSpace:'nowrap'}}>
      CORINGA <span style={{color:GOLD}}>EXPLICA</span>
    </div>
    <div data-safe-role="section" style={{...safeSlot('section'),
      fontFamily:'Inter,Arial,sans-serif',fontWeight:750,fontSize:22,
      color:'#B8CCD8',letterSpacing:1.35,overflow:'hidden',
      textOverflow:'ellipsis',whiteSpace:'nowrap'}}>
      {shot.lead.toUpperCase()}
    </div>
    {shot.type==='mechanism'&&!subtitleMode&&<div data-safe-role="mechanism_step"
      style={{...rectStyle(MECH.step),display:'flex',alignItems:'center',
        fontFamily:'Inter,Arial,sans-serif',fontSize:(active?.label||shot.headline).length>46?28:34,
        fontWeight:900,lineHeight:1.07,color:OFF_WHITE,letterSpacing:-.45,
        textShadow:'0 2px 12px rgba(0,0,0,.8)'}}>
      <span style={{color:GOLD,marginRight:8}}>●</span>{active?.label||shot.headline}
    </div>}
    {!subtitleMode&&active&&!shot.graphic_original&&shot.type!=='mechanism'&&<div data-safe-role="cue"
      style={{...safeSlot('cue'),fontFamily:'Inter,Arial,sans-serif',
        fontSize:active.label.length>32?24:28,fontWeight:900,color:GOLD,
        opacity:ease(age/.20),overflow:'hidden',lineHeight:1.15,
        transform:`translateY(${(1-ease(age/.20))*8}px)`}}>
      {active.label}
    </div>}
    {!subtitleMode&&shot.type!=='mechanism'&&!shot.graphic_original&&<div data-safe-role="headline"
      style={{...safeSlot('headline'),color:OFF_WHITE,
        textShadow:'0 2px 14px rgba(0,0,0,.78)',
        overflow:'hidden',opacity:ease((now-shot.start-.08)/.25)}}>
      <Caption text={shot.headline} highlighted={shot.highlight}/>
    </div>}
    {!subtitleMode&&shot.type!=='mechanism'&&<div data-safe-role="subject" style={{...safeSlot('subject'),
      color:'#D4E1E9',fontFamily:'Inter,Arial',fontSize:21,
      fontWeight:650,lineHeight:1.15,overflow:'hidden'}}>
      {shot.evidence==='representative'?'IMAGEM DE CONTEXTO · '+shot.subject:shot.subject}
    </div>}
    <div data-safe-role="source" style={{...safeSlot('source'),
      color:'#B9C9D4',fontFamily:'Inter,Arial',fontSize:18.5,
      lineHeight:1.12,fontWeight:550,overflow:'hidden'}}>
      {shot.type==='mechanism'?'ESQUEMA ILUSTRATIVO · ':''}FONTE: {shot.source_display || shot.source}
    </div>
  </AbsoluteFill>;
};
export const FilmeEditorial: React.FC<FilmProps> = ({shots,duracao,preview=true,
  private_review_only=false,safe_zone_debug=false,subtitle_mode=false}) => {
  const frame=useCurrentFrame(),fps=useVideoConfig().fps,t=frame/fps;
  const shot=shots.findIndex(s=>t>=s.start&&t<s.end);
  return <AbsoluteFill style={{background:'#050A12'}}>
    {shot>=0&&<FilmShotView shot={shots[shot]} total={duracao} index={shot} subtitleMode={subtitle_mode}/>}
    {/* QA: margem transparente demonstra riscos sem alterar o vídeo de publicação. */}
    {safe_zone_debug&&<>
      <div style={{position:'absolute',left:0,right:0,top:0,height:safety.universal[1],
        background:'rgba(210,28,47,.21)',pointerEvents:'none'}}/>
      <div style={{position:'absolute',left:0,right:0,top:safety.universal[3],
        bottom:0,background:'rgba(210,28,47,.23)',pointerEvents:'none'}}/>
      <div style={{position:'absolute',left:0,top:safety.universal[1],
        bottom:H-safety.universal[3],width:safety.universal[0],
        background:'rgba(210,28,47,.18)',pointerEvents:'none'}}/>
      <div style={{position:'absolute',left:safety.universal[2],top:safety.universal[1],
        bottom:H-safety.universal[3],right:0,background:'rgba(210,28,47,.20)',
        pointerEvents:'none'}}/>
      <div style={{position:'absolute',left:safety.universal[0],top:safety.universal[1],
        width:safety.universal[2]-safety.universal[0],
        height:safety.universal[3]-safety.universal[1],
        border:'4px dashed #66EDC4',pointerEvents:'none'}}/>
    </>}
    {/* Barra editorial única: baseada no tempo GLOBAL da composição, não no plano. */}
    <div data-testid="filme-progresso-global" style={{position:'absolute',bottom:110,left:60,right:60,
      height:4,background:'rgba(255,255,255,.25)'}}>
      <div style={{width:`${100*clamp(t/Math.max(.01,duracao))}%`,height:'100%',background:GOLD}}/>
    </div>
    {preview&&<div style={{position:'absolute',bottom:40,left:0,right:0,textAlign:'center',
      fontFamily:'Inter,Arial',color:'#CFD6E0',opacity:.7,fontSize:20,letterSpacing:1.1}}>
      {private_review_only ? 'PRÉVIA TÉCNICA · DIREITOS PENDENTES · NÃO PUBLICAR' : 'PRÉVIA PRIVADA · NÃO PUBLICADO'}
    </div>}
  </AbsoluteFill>;
};
