/** FILME EDITORIAL — compositor visual-first independente do ATLAS de cartões.
 * Stage 0: documentação real preenchendo a tela; câmera e revelações de cada assunto.
 * Não há palco-mapa persistente, slots pequenos, nem fluxo de cards como ação.
 * Todos os títulos vêm do roteiro; o compositor não inventa fatos.
 */
import React from 'react';
import {SignatureBackground,signatureHasVisibleArea} from './SignatureBackground';
import {LockCausal} from './LockCausal';
import {LockCausalCycle} from './LockCausalCycle';
import {MotionEditorial, type MotionEditorialData} from './MotionEditorial';
import {SceneGraphE201, type SceneData, type SceneDataV2} from './SceneGraphE201';
import {OpticalProjection} from './OpticalProjection';
import safety from './safe-zones-vertical.json';
import animationPolicy from './animation-policy.json';
import {AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

export type Cue = {at: number; label: string; kind?: 'callout' | 'fact'; x?: number; y?: number; action?: 'closed' | 'water_enter' | 'rise' | 'equalize' | 'release' | 'enter' | 'seal' | 'valves' | 'open' | 'exit'};
export type FilmShot = {
  id: string;
  start: number;
  end: number;
  type: 'photo' | 'video' | 'comparison' | 'mechanism' | 'atlas_map' | 'cad_preview' | 'scene_graph' | 'animation_clip';
  animation_proof?: {schema:string;renderer:string;sha256:string;run:number;frames:number;fps:number;dimensions:number[];duration_s:number;status:string;publish:boolean;viewport:string;geometry_approval:string;acao:string;lacuna:string;motivo_lacuna:string;midia_adequada:boolean};
  scene_graph?: SceneData | SceneDataV2;
  cad_source_roi?: [number,number,number,number]; // private E28 stage ROI
  cad_phrase_captions?: {start:number;end:number;text:string}[]; // measured phrase-level audio, private QA
  cad_compact_panel?: boolean; // E46C private, preserve hero viewport
  cad_transmissao?: {schema:string;modo:string;razao:string;entrada:string;saida:string;publish:boolean};
  cad_warning?: string; // private CAD QA warning, never a publication clearance
  cad_reflow?: {schema:string;scale:number;tx:number;ty:number;viewport:number[];publish:boolean}; // E31 private
  asset?: string; // caminho relativo a motor4/remotion/public, verificado pelo preflight Python
  assetB?: string;
  source_in_seconds?: number; // corte verdadeiro dentro do master local do arquivo
  video_zoom?: number; // enquadramento dirigido para o portão, não zoom decorativo
  documentary_viewport?: '4:5' | '1:1'; // private adaptive review, never stretches source
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
  photo_framing?: 'integral';
  photo_crop_preview?: {height:number;position:[number,number];status:string;essential_screen?:number[]}; // private geometric alternative
  documentary_roi_points?: {at:number;bbox:number[]}[]; // preflight validated source observations only
  source_dimensions?: [number,number]; // actual decoded dimensions; no assumed aspect ratio
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
  reference_style_preview?: boolean; // SOMENTE QA privado: visual antigo para comparação; bloqueado para publicação
  portrait_experiment?: boolean; // flag privada; não trocar o padrão sem homologação estética
  safe_zone_debug?: boolean; // somente QA, nunca publicar o overlay vermelho
  subtitle_mode?: boolean; // quando a Camada de fala está presente, ela ocupa lane própria
  safe_area_profile?: 'MULTIPLATAFORMA_CONSERVADOR_V1';
  direitos_pendentes?: string[];
  cad_narration_asset?: string;
  // E202: narração privada medida (hash no nome), somente prévia privada com cenas declarativas
  scene_narration_asset?: string;
  documentary_captions?: {start:number;end:number;words:{w:string;hl?:boolean}[]}[];
  animation_policy_mode?: 'EDITORIAL'|'LEGADO_REJEITADO_SOMENTE_QA';
  documentary_caption_origin?: 'PALAVRAS_MEDIDAS'|'FRASES_MEDIDAS_LAB';
  documentary_media_preview?: boolean; // silent private QA uses the same documentary composition
  documentary_text_probe?: boolean; // private browser measurement, not visual approval
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
const HERO = safety.cad_hero_private;
const BALANCED = safety.cad_hero_balanced_private;
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

// Private narrated real-media review: the picture is not a text-safe slot.
const realMedia=(s:FilmShot)=>s.type==='video'||(s.type==='photo'&&!s.graphic_original);
// E295: private editorial composition, NOT a new certified platform-safe profile.
// Anchor at x120 (largest configured left exclusion), maintain right x760.
// Lower lanes deliberately need real app UI review; legacy SAFE is unchanged.
const DOC_MEDIA={brand:[120,300,500,338],section:[120,347,760,397],subtitle:[120,1380,760,1470],source:[120,1478,760,1600]} as const;
// E290: same conservative text perimeter and same ROI; no new background design.
// A 16:9 integral source has room for its actual pixels between header and caption.
// Taller sources retain the previous maximum height (730px), not a blind crop.
const integralMediaRect=(shot:FilmShot):readonly number[]=>{
  const [w,h]=shot.source_dimensions||[16,9];
  return w/h<=1.15?[0,0,1080,1920]:w/h>=1080/610?[0,405,1080,1015]:[0,405,1080,1135];
};
const nativePortrait=(shot:FilmShot)=>Boolean(shot.source_dimensions&&
  shot.source_dimensions.every(v=>Number.isFinite(v)&&v>0)&&shot.source_dimensions[0]<shot.source_dimensions[1]);
const nativeIntegral=(shot:FilmShot)=>nativePortrait(shot)&&!shot.documentary_viewport&&
  !shot.framing_positions?.length&&shot.photo_crop_preview?.status!=='PRIVATE_CANDIDATE_REVIEW_PENDING';
const originalDocumentaryPixelRect=(shot:FilmShot):readonly number[]=>{
  if(nativeIntegral(shot))return containPixels([0,0,W,H],shot.source_dimensions!);
  if(shot.type==='video'&&shot.documentary_viewport)
    return [0,370,1080,370+(shot.documentary_viewport==='4:5'?1350:1080)];
  if(shot.type==='photo'&&shot.photo_crop_preview?.status==='PRIVATE_CANDIDATE_REVIEW_PENDING'&&
      [1080,1350].includes(shot.photo_crop_preview.height))
    return [0,0,1080,shot.photo_crop_preview.height];
  const integral=shot.type==='photo'?shot.photo_framing==='integral':
    ['cena_integral','quadro_integral'].includes(shot.video_context_layout||'');
  if(!integral)return [0,0,W,H];
  const [x,y,r,b]=integralMediaRect(shot),[w,h]=shot.source_dimensions||[16,9];
  if(!(w>0&&h>0))return [x,y,r,b];
  const scale=Math.min((r-x)/w,(b-y)/h);
  const dx=((r-x)-w*scale)/2,dy=((b-y)-h*scale)/2;
  return [x+dx,y+dy,r-dx,b-dy];
};
const intersects=(a:readonly number[],b:readonly number[])=>a[0]<b[2]&&a[2]>b[0]&&a[1]<b[3]&&a[3]>b[1];
type DocSlots={brand:readonly number[];section:readonly number[];subtitle:readonly number[];source:readonly number[]};
type DocLayout={slots:DocSlots;mode:'STANDARD'|'UPPER_TEXT'|'LOWER_TEXT'|'MIDDLE_TEXT'|'PORTRAIT_REVIEW'|'INTEGRAL_PROTECTED'|'CENTERED_INTEGRAL'|'CENTERED_CROP_REVIEW'|'CENTERED_CROP_OBSERVED';media:readonly number[];protected:readonly number[][];roiStatus:'OBSERVED'|'FULL_SOURCE_PROTECTED'|'UNKNOWN_REVIEW';separateStage?:readonly number[];centeredStage?:readonly number[];centeredFit?:'contain'|'cover'};
const stackedDocSlots=(y:number):DocSlots=>({
  brand:[120,y,500,y+38],section:[120,y+43,760,y+93],
  subtitle:[120,y+101,760,y+191],source:[120,y+199,760,y+321],
});
const docRects=(slots:DocSlots)=>[slots.brand,slots.section,slots.subtitle,slots.source,
  [slots.brand[0],slots.brand[3]+1,slots.brand[0]+130,slots.brand[3]+4]];
const normalizedBox=(b:readonly number[])=>b.length===4&&b.every(Number.isFinite)&&
  0<=b[0]&&b[0]<b[2]&&b[2]<=1&&0<=b[1]&&b[1]<b[3]&&b[3]<=1;
const expandBox=(b:readonly number[],n:number)=>[b[0]-n,b[1]-n,b[2]+n,b[3]+n];
const containPixels=(stage:readonly number[],dims:readonly number[])=>{
  const [x,y,r,b]=stage,[w,h]=dims;
  const scale=Math.min((r-x)/w,(b-y)/h);
  const dx=((r-x)-w*scale)/2,dy=((b-y)-h*scale)/2;
  return [x+dx,y+dy,r-dx,b-dy];
};
// The preflight already establishes the crop. Project observed boxes through
// that SAME viewport and camera positions. A swept envelope conservatively
// covers the combinations of sampled positions/boxes (not unobserved action).
const documentaryProtected=(shot:FilmShot,media:readonly number[]):number[][]|null=>{
  if(shot.type==='photo'&&shot.photo_crop_preview?.status==='PRIVATE_CANDIDATE_REVIEW_PENDING'){
    const b=shot.photo_crop_preview.essential_screen;
    if(b?.length===4&&b.every(Number.isFinite)&&b[0]>=0&&b[1]>=0&&b[2]<=1080&&b[3]<=shot.photo_crop_preview.height&&b[0]<b[2]&&b[1]<b[3])return [expandBox(b,12)];
  }
  const points=shot.documentary_roi_points,positions=shot.framing_positions,dims=shot.source_dimensions;
  if(shot.type==='video'&&points?.length&&positions?.length&&dims&&dims.every(v=>Number.isFinite(v)&&v>0)&&
      points.length===positions.length&&points.every((p,i)=>normalizedBox(p.bbox)&&Math.abs(p.at-positions[i].at)<.001)&&
      positions.every(p=>p.position.every(v=>Number.isFinite(v)&&v>=0&&v<=1))){
    const [x,y,r,b]=media,[w,h]=dims;
    const scale=Math.max((r-x)/w,(b-y)/h),sw=w*scale,sh=h*scale;
    const boxes=points.flatMap(p=>positions.map(k=>{
      const ox=x-(sw-(r-x))*k.position[0],oy=y-(sh-(b-y))*k.position[1];
      return [ox+p.bbox[0]*sw,oy+p.bbox[1]*sh,ox+p.bbox[2]*sw,oy+p.bbox[3]*sh];
    }));
    return [expandBox([Math.min(...boxes.map(b=>b[0])),Math.min(...boxes.map(b=>b[1])),
      Math.max(...boxes.map(b=>b[2])),Math.max(...boxes.map(b=>b[3]))],12)];
  }
  // Missing annotation is not proof of collision, nor proof of safety.
  return null;
};
const centeredLandscape=(shot:FilmShot):DocLayout|null=>{
  const dims=shot.source_dimensions;
  if(!dims||!dims.every(v=>Number.isFinite(v)&&v>0)||dims[0]<=dims[1])return null;
  // The visual midpoint is always y960. Full-width 16:9 = 607.5px.
  // 810px maximum (4:3) is a moderate ~1.33x scale on 16:9.
  const stage=[0,555,1080,1365];
  const pixels=containPixels(stage,dims);
  const full:DocLayout={mode:'CENTERED_INTEGRAL',slots:DOC_MEDIA,media:pixels,protected:[pixels],
    roiStatus:'FULL_SOURCE_PROTECTED',centeredStage:stage,centeredFit:'contain'};
  // Without a pre-existing private crop candidate or observed framing,
  // there is no authorization to remove source context.
  const requested=shot.type==='video'&&(Boolean(shot.documentary_viewport)||Boolean(shot.framing_positions?.length));
  if(!requested||pixels[3]-pixels[1]>=810-1)return full;
  const observed=documentaryProtected(shot,stage);
  if(observed){
    // Sweep all sampled ROI/position combinations; reject a crop that would
    // remove any protected pixels or place text on them.
    if(!observed.every(b=>b[0]>=stage[0]&&b[1]>=stage[1]&&b[2]<=stage[2]&&b[3]<=stage[3]&&
      docRects(DOC_MEDIA).every(r=>!intersects(r,b))))return full;
    return {...full,mode:'CENTERED_CROP_OBSERVED',media:stage,protected:observed,roiStatus:'OBSERVED',centeredFit:'cover'};
  }
  // Historical reviewed crop candidate only, private human review pending.
  // Less aggressive than the existing square/4:5 crop. Never claim ROI proof.
  if(shot.documentary_viewport&&shot.video_context_layout==='recorte_relacional_seguro')
    return {...full,mode:'CENTERED_CROP_REVIEW',media:stage,protected:[],roiStatus:'UNKNOWN_REVIEW',centeredFit:'cover'};
  return full;
};
const documentaryLayout=(shot:FilmShot):DocLayout=>{
  const centered=centeredLandscape(shot);
  if(centered)return centered;
  const media=originalDocumentaryPixelRect(shot),observed=documentaryProtected(shot,media);
  // E292: native portrait gets maximum undistorted size by default. Unknown
  // subject location is a semantic REVIEW item, not a reason to miniaturize.
  if(nativePortrait(shot)&&!observed)
    return {mode:'PORTRAIT_REVIEW',slots:DOC_MEDIA,media,protected:[],roiStatus:'UNKNOWN_REVIEW'};
  const protectedBoxes=observed??[Array.from(media)];
  const roiStatus=observed?'OBSERVED':'FULL_SOURCE_PROTECTED';
  const candidates:[DocLayout['mode'],DocSlots][]=[['STANDARD',DOC_MEDIA],['UPPER_TEXT',stackedDocSlots(312)],['LOWER_TEXT',stackedDocSlots(910)],['MIDDLE_TEXT',stackedDocSlots(620)]];
  for(const [mode,slots] of candidates){
    if(docRects(slots).every(r=>protectedBoxes.every(b=>!intersects(r,b))))
      return {mode,slots,media,protected:protectedBoxes,roiStatus};
  }
  // If no text placement can preserve the known evidence, restore ALL source
  // pixels in a separate stage; never invent a different crop or cover the ROI.
  // This fallback trades immersion for protection and remains a private review.
  const separateStage=[0,0,1080,900],dims=shot.source_dimensions||[16,9];
  const pixels=containPixels(separateStage,dims.every(v=>Number.isFinite(v)&&v>0)?dims:[16,9]);
  return {mode:'INTEGRAL_PROTECTED',slots:stackedDocSlots(910),media:pixels,protected:[pixels],roiStatus:'FULL_SOURCE_PROTECTED',separateStage};
};
const documentaryPixelRect=(shot:FilmShot):readonly number[]=>documentaryLayout(shot).media;
const documentaryOverlay=(shot:FilmShot,rect:readonly number[])=>intersects(documentaryPixelRect(shot),rect);
// Use the actual browser font metrics and wrapping, not character-count estimates.
// Overflow at the readable floor is a diagnostic for editorial review, never silent ellipsis.
const MeasuredDocText:React.FC<{role:'section'|'subtitle'|'source';shot:FilmShot;rect:readonly number[];
  text:string;children?:React.ReactNode;probe?:boolean}>=({role,shot,rect,text,children,probe=false})=>{
  const host=React.useRef<HTMLDivElement>(null),inner=React.useRef<HTMLDivElement>(null);
  const size=role==='subtitle'?[52,36]:role==='source'?[30,24]:[30,22];
  const overlay=documentaryOverlay(shot,rect);
  const signature=rect.join(',');
  React.useLayoutEffect(()=>{
    const h=host.current,e=inner.current;if(!h||!e)return;
    const range=document.createRange();range.selectNodeContents(e);
    const hr=h.getBoundingClientRect();
    const sx=hr.width/h.clientWidth||1,sy=hr.height/h.clientHeight||1;
    const measure=()=>{
      const rr=range.getBoundingClientRect();
      return [rect[0]+(rr.left-hr.left)/sx,rect[1]+(rr.top-hr.top)/sy,
        rect[0]+(rr.right-hr.left)/sx,rect[1]+(rr.bottom-hr.top)/sy];
    };
    let font=size[0],fits=false,actual:number[]=[];
    for(;font>=size[1];font--){
      e.style.fontSize=font+'px';actual=measure();
      fits=e.scrollHeight<=h.clientHeight&&e.scrollWidth<=h.clientWidth&&
        actual[0]>=rect[0]-1&&actual[1]>=rect[1]-1&&actual[2]<=rect[2]+1&&actual[3]<=rect[3]+1;
      if(fits)break;
    }
    font=Math.max(size[1],font);e.style.fontSize=font+'px';actual=measure();
    const er=e.getBoundingClientRect();
    const painted=[rect[0]+(er.left-hr.left)/sx,rect[1]+(er.top-hr.top)/sy,
      rect[0]+(er.right-hr.left)/sx,rect[1]+(er.bottom-hr.top)/sy];
    const actualOverlay=documentaryOverlay(shot,painted);
    const layout=documentaryLayout(shot);
    const signatureBackground=document.querySelector('[data-layout-review] [data-documentary-background]')?.getAttribute('data-documentary-background')??null;
    // Soft local contrast for full-height portrait, without a full-width
    // opaque panel; stronger local contrast stays for other layouts.
    const portraitReview=layout.mode==='PORTRAIT_REVIEW';
    e.style.background=actualOverlay?(portraitReview?'linear-gradient(90deg,rgba(4,11,20,.78),rgba(4,11,20,.62))':'rgba(4,11,20,.84)'):'transparent';
    e.style.textShadow=actualOverlay?'0 1px 3px #000':'none';
    h.dataset.docOverlay=actualOverlay?'review':'none';
    h.dataset.roiStatus=layout.roiStatus;
    const evidenceCollision=layout.protected.some(b=>intersects(painted,b));
    const bounds={width:e.scrollWidth,height:e.scrollHeight,slotWidth:h.clientWidth,slotHeight:h.clientHeight,actual,painted,
      actualOverlay,evidenceCollision,layout:layout.mode,roiStatus:layout.roiStatus,protected:layout.protected,signatureBackground,centeredFit:layout.centeredFit??null};
    h.dataset.docFit=fits?'FIT':'OVERFLOW_REVIEW';h.dataset.docFont=String(font);
    if(probe)console.log('E290_TEXT '+JSON.stringify({shot:shot.id,role,font,fits,overlay,rect,media:documentaryPixelRect(shot),text,...bounds}));
  },[text,role,signature,overlay,shot.id,probe]);
  return <div ref={host} data-safe-role={role} data-documentary-text={role} data-documentary-credit={role==='source'?'full':undefined}
    data-doc-overlay={overlay?'review':'none'} style={{...rectStyle(rect),display:'flex',alignItems:'center',
      justifyContent:'flex-start',textAlign:'left',pointerEvents:'none'}}>
    <div ref={inner} style={{width:'fit-content',maxWidth:'100%',boxSizing:'border-box',fontFamily:'Inter,Arial,sans-serif',
      fontWeight:role==='subtitle'?850:role==='section'?800:500,fontSize:size[0],lineHeight:role==='source'?1.12:role==='section'?1:1.08,
      color:role==='source'?'#DCE3E9':OFF_WHITE,whiteSpace:'normal',overflowWrap:'anywhere',
      padding:overlay?(role==='section'?'2px 8px':'4px 8px'):'0',background:overlay?'rgba(4,11,20,.84)':'transparent',
      borderRadius:overlay?4:0,textShadow:overlay?'0 1px 3px #000':'none'}}>
      {children??text}
    </div>
  </div>;
};
const Body: React.FC<{shot: FilmShot;p:number;t:number;portrait?:boolean;mediaFirst?:boolean;photoHero?:boolean}> = ({shot,p,t,portrait=false,mediaFirst=false,photoHero=false}) => {
  if(shot.type==='mechanism' && shot.mechanism==='optical_projection')
    return <OpticalProjection t={t} events={shot.cues || []} portrait={portrait}/>;
  if(shot.type==='mechanism' && shot.mechanism==='lock_explainer')
    return <LockCausal t={t} events={(shot.cues || []).map(c => ({
      at:c.at,label:c.label,action:c.action as 'closed' | 'water_enter' | 'rise' | 'equalize' | 'release' | undefined
    }))} visualMode={portrait?'portrait':'editorial'}/>;
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
  if(shot.type === 'animation_clip' || shot.type === 'atlas_map') {
    // É um MP4 do Formato/PalcoMapa ORIGINAL, com seu próprio raster, créditos,
    // destaques e câmera. Nunca redesenhar mapa, crop ou duplicar títulos.
    return <AbsoluteFill><Sequence from={Math.round(shot.start*30)}
      durationInFrames={Math.ceil((shot.end-shot.start)*30)}>
      <OffthreadVideo src={staticFile(shot.asset || '')} muted
        style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'contain'}}/>
    </Sequence></AbsoluteFill>;
  }
  const docLayout=mediaFirst&&realMedia(shot)?documentaryLayout(shot):undefined;
  if(docLayout?.centeredStage){
    const position=enquadramentoNoTempo(shot.framing_positions,t,shot.focus||[.5,.5]);
    const fit=docLayout.centeredFit||'contain';
    const style={position:'absolute' as const,inset:0,width:'100%',height:'100%',objectFit:fit,
      objectPosition:fit==='cover'?`${position[0]*100}% ${position[1]*100}%`:'50% 50%'};
    return <AbsoluteFill>
      <div data-media-layout="centered-editorial" data-media-fit={fit} style={{...rectStyle(docLayout.centeredStage),overflow:'hidden'}}>
        {shot.type==='video'?<Sequence from={Math.round(shot.start*30)} durationInFrames={Math.ceil((shot.end-shot.start)*30)}>
          <OffthreadVideo src={staticFile(shot.asset||'')} muted startFrom={Math.max(0,Math.round((shot.source_in_seconds||0)*30))} style={style}/>
        </Sequence>:<Img src={staticFile(shot.asset||'')} style={style}/>}
      </div>
    </AbsoluteFill>;
  }
  const separateStage=docLayout?.separateStage;
  if(separateStage){
    // Same source/sequence; no crop, no zoom, no duplicate blurred video.
    const stage={...rectStyle(separateStage),overflow:'hidden' as const};
    return <AbsoluteFill>
      <div data-media-layout="integral-protected" style={stage}>
        {shot.type==='video'?<Sequence from={Math.round(shot.start*30)} durationInFrames={Math.ceil((shot.end-shot.start)*30)}>
          <OffthreadVideo src={staticFile(shot.asset||'')} muted startFrom={Math.max(0,Math.round((shot.source_in_seconds||0)*30))}
            style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'contain'}}/>
        </Sequence>:<Img src={staticFile(shot.asset||'')} style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'contain'}}/>}
      </div>
    </AbsoluteFill>;
  }
  if(mediaFirst&&realMedia(shot)&&nativeIntegral(shot)){
    // A native 9:16 is exactly full canvas. Other portrait ratios use maximum
    // contain without distortion or unverified crop. Preserve original frames.
    return <AbsoluteFill data-media-layout="native-portrait-full">
      {shot.type==='video'?<Sequence from={Math.round(shot.start*30)} durationInFrames={Math.ceil((shot.end-shot.start)*30)}>
        <OffthreadVideo src={staticFile(shot.asset||'')} muted startFrom={Math.max(0,Math.round((shot.source_in_seconds||0)*30))}
          style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'contain'}}/>
      </Sequence>:<Img src={staticFile(shot.asset||'')} style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'contain'}}/>}
    </AbsoluteFill>;
  }
  if(shot.type === 'video') {
    if(mediaFirst && shot.documentary_viewport) {
      const height=shot.documentary_viewport==='4:5'?1350:1080;
      if(!['4:5','1:1'].includes(shot.documentary_viewport)||shot.video_context_layout!=='recorte_relacional_seguro')
        throw new Error('E229-VIEWPORT');
      const position=enquadramentoNoTempo(shot.framing_positions,t,shot.focus||[.5,.5]);
      return <AbsoluteFill>
        <div data-media-layout={shot.documentary_viewport} style={{position:'absolute',left:0,top:370,width:1080,height,overflow:'hidden'}}>
          <Sequence from={Math.round(shot.start*30)} durationInFrames={Math.ceil((shot.end-shot.start)*30)}>
            <OffthreadVideo src={staticFile(shot.asset||'')} muted startFrom={Math.max(0,Math.round((shot.source_in_seconds||0)*30))}
              style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover',
                objectPosition:`${position[0]*100}% ${position[1]*100}%`}}/>
          </Sequence>
        </div>
      </AbsoluteFill>;
    }
    if(mediaFirst && (shot.video_context_layout==='cena_integral'||shot.video_context_layout==='quadro_integral')) {
      // Preserve all source pixels, but give the shot the FULL canvas width.
      // Integral is an exception for essential context, never the default crop.
      return <AbsoluteFill>
        <div data-media-layout="integral-wide" style={{...rectStyle(integralMediaRect(shot)),overflow:'hidden'}}>
          <Sequence from={Math.round(shot.start*30)} durationInFrames={Math.ceil((shot.end-shot.start)*30)}>
            <OffthreadVideo src={staticFile(shot.asset||'')} muted startFrom={Math.max(0,Math.round((shot.source_in_seconds||0)*30))}
              style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'contain'}}/>
          </Sequence>
        </div>
      </AbsoluteFill>;
    }
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
  if(shot.type==='photo'&&shot.photo_framing==='integral'&&!shot.graphic_original){
    // Preserve the complete scientific/archival photograph without inventing
    // borders or cutting essential context. The editorial layers remain separate.
    const crop=mediaFirst&&shot.photo_crop_preview?.status==='PRIVATE_CANDIDATE_REVIEW_PENDING'?shot.photo_crop_preview:null;
    if(crop&&[1080,1350].includes(crop.height))return <AbsoluteFill>
      <Img data-media-layout="photo-roi-private-candidate" src={staticFile(shot.asset||'')} style={{position:'absolute',left:0,top:0,width:1080,height:crop.height,objectFit:'cover',objectPosition:`${crop.position[0]*100}% ${crop.position[1]*100}%`}}/>
    </AbsoluteFill>;
    return <AbsoluteFill style={{background:mediaFirst?'transparent':'#08121E',overflow:'hidden'}}>
      <Img data-media-layout={mediaFirst?'integral-photo-adaptive':'integral-photo-legacy'} src={staticFile(shot.asset||'')} style={{...(mediaFirst?rectStyle(integralMediaRect(shot)):{position:'absolute' as const,left:0,top:360,width:1080,height:1110}),objectFit:'contain'}}/>
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
const SafeBody: React.FC<{shot:FilmShot;p:number;t:number;subtitleMode:boolean;portraitExperiment:boolean}> = ({shot,p,t,subtitleMode,portraitExperiment}) => {
  if (portraitExperiment && !subtitleMode && shot.type==='mechanism' &&
      (MECH.native_portrait as readonly string[]).includes(shot.mechanism||'')) {
    // Vertical-first: objetos novos em SVG 620x682; não existe zoom nem crop
    // de uma arte feita para 1080x1920. Toda ação essencial fica na mesma
    // janela segura e a informação do roteiro não é repetida no SVG.
    // O renderer imersivo dispõe de DUAS faixas independentes autorizadas
    // pelos perfis de UI: largo acima de y840; estreito abaixo.
    // Não aplicar a voz: subtitle_mode preserva exclusivamente sua faixa.
    return <AbsoluteFill style={{background:'radial-gradient(ellipse at 46% 53%,#193950,#081B2B 57%,#050F1B 100%)'}}>
      <AbsoluteFill style={{opacity:.11,backgroundSize:'94px 94px',
        backgroundImage:'linear-gradient(to right,#7A9FB4 1px,transparent 1px),linear-gradient(to bottom,#7A9FB4 1px,transparent 1px)'}}/>
      {/* Atmosfera FULL BLEED, sem textos nem atores essenciais:
          aumenta a continuidade visual fora da zona de leitura do app.
          A física, os rótulos e as causas permanecem dentro do palco protegido. */}
      <svg viewBox="0 0 1080 1920" width="100%" height="100%"
        aria-hidden="true" style={{position:'absolute',inset:0,opacity:.37,pointerEvents:'none'}}>
        <defs>
          <linearGradient id="atmospheric-water" x1="0" y1="0" x2="0" y2="1">
            <stop stopColor="#327B95" stopOpacity=".28"/>
            <stop offset="1" stopColor="#102B43" stopOpacity=".06"/>
          </linearGradient>
        </defs>
        {shot.mechanism==='optical_projection'?<g>
          <ellipse cx="530" cy="1560" rx="576" ry="171" fill="#0B3349"
            stroke="#5891AB" strokeWidth="6" opacity=".38"/>
          <ellipse cx="530" cy="1545" rx="535" ry="135" fill="none"
            stroke="#68D8E4" strokeWidth="4" opacity=".28"/>
          {Array.from({length:14},(_,i)=><path key={i}
            d={`M${-60+i*91} 1440 L${-30+i*91} 1680`}
            stroke="#6093AA" strokeWidth="3" opacity=".14"/>)}
          <path d="M36 1684 H1044 M120 1736 H960 M188 1790 H890"
            stroke="#69DDEC" fill="none" strokeWidth="3" opacity=".33"/>
          <path d="M122 1200 V1460 H320 M968 1010 V1450 H850"
            fill="none" stroke="#659AAE" strokeWidth="7" opacity=".30"/>
        </g>:<g>
          <rect x="0" y="1350" width="1080" height="410"
            fill="url(#atmospheric-water)"/>
          {[0,1,2,3,4,5].map(i=><path key={i}
            d={`M-40 ${1390+i*63} Q205 ${1371+i*63} 510 ${1390+i*63} T1120 ${1390+i*63}`}
            fill="none" stroke="#72BFD1" strokeWidth="5" opacity={.13+i*.024}/>)}
          <path d="M35 1760 H1045 M120 1815 H960"
            stroke="#4C829B" strokeWidth="8" opacity=".3"/>
          <path d="M115 1330 V1710 H955 V1330"
            fill="none" stroke="#487489" strokeWidth="10" opacity=".21"/>
        </g>}
      </svg>
      <Body shot={shot} p={p} t={t} portrait/>
    </AbsoluteFill>;
  }
  if (shot.type==='cad_preview' && shot.cad_reflow) {
    const r=shot.cad_reflow;
    const wide=(r.schema==='coringa.cad.hero.private.v1'&&r.viewport.join(',')===HERO.viewport.join(','))||(r.schema==='coringa.cad.hero.balanced.private.v1'&&r.viewport.join(',')===BALANCED.viewport.join(','));
    const old=r.schema==='coringa.cad.reflow.private.v1'&&(r.viewport.join(',')==='50,400,1030,1092'||(shot.cad_transmissao&&r.viewport.join(',')==='50,400,1030,962'));
    if (subtitleMode || (!wide&&!old) || r.publish!==false ||
      ![r.scale,r.tx,r.ty].every(Number.isFinite) || r.scale<.35 || r.scale>(wide?2.4:1.6))
      throw new Error('E31-PRIVATE-REFLOW');
    const [x,y,ex,ey]=r.viewport;
    return <AbsoluteFill style={{background:'radial-gradient(ellipse at 46% 47%,#10202C,#070D14 80%)'}}>
      <div data-cad-experimental-reflow="true"
        style={{position:'absolute',left:x,top:y,width:ex-x,height:ey-y,overflow:'hidden'}}>
        <div style={{position:'absolute',left:r.tx-x,top:r.ty-y,width:1080,height:1920,
          transform:`scale(${r.scale})`,transformOrigin:'top left'}}>
          <Sequence from={Math.round(shot.start*30)}
            durationInFrames={Math.round((shot.end-shot.start)*30)}>
            <OffthreadVideo src={staticFile(shot.asset||'')} muted
              style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'contain'}}/>
          </Sequence>
        </div>
      </div>
    </AbsoluteFill>;
  }
  if (shot.type==='cad_preview') {
    const roi=shot.cad_source_roi;
    if (!roi || roi.join(',')!=='86,288,994,1230' || shot.evidence!=='explainer')
      throw new Error('E28-CAD-ROI-OR-EVIDENCE');
    const [sx,sy,ex,ey]=roi;
    const dw=SAFE.visual[2]-SAFE.visual[0],dh=SAFE.visual[3]-SAFE.visual[1];
    const scale=Math.min(dw/(ex-sx),dh/(ey-sy));
    return <AbsoluteFill style={{background:'#0B1926'}}>
      <div data-safe-role="visual" style={{...safeSlot('visual'),overflow:'hidden'}}>
        <div style={{position:'absolute',left:(dw-(ex-sx)*scale)/2,
          top:(dh-(ey-sy)*scale)/2,width:ex-sx,height:ey-sy,overflow:'hidden',
          transform:`scale(${scale})`,transformOrigin:'top left'}}>
          <div style={{position:'absolute',left:-sx,top:-sy,width:1080,height:1920}}>
            <Sequence from={Math.round(shot.start*30)}
              durationInFrames={Math.round((shot.end-shot.start)*30)}>
              <OffthreadVideo src={staticFile(shot.asset||'')} muted
                style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'contain'}}/>
            </Sequence>
          </div>
        </div>
      </div>
    </AbsoluteFill>;
  }
  if (shot.type==='mechanism') {
    // Fallback conservador para mecanismos que AINDA não possuem reflow
    // vertical nativo; não declarar estes tipos homologados sem inspeção.
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

const FilmShotView: React.FC<{shot:FilmShot;total:number;index:number;subtitleMode:boolean;legacyVisualPreview:boolean;portraitExperiment:boolean;mediaFirst:boolean;textProbe?:boolean}> = ({shot,subtitleMode,legacyVisualPreview,portraitExperiment,mediaFirst,textProbe}) => {
  const frame=useCurrentFrame(),fps=useVideoConfig().fps;
  const now=frame/fps;
  const duration=Math.max(.01,shot.end-shot.start);
  const p=clamp((now-shot.start)/duration);
  const active=shot.cues?.filter(c=>now>=shot.start+c.at).slice(-1)[0];
  const age=active?now-shot.start-active.at:0;
  const reflowCAD=shot.type==='cad_preview'&&Boolean(shot.cad_reflow);
  const balancedCAD=reflowCAD&&shot.cad_reflow?.schema==='coringa.cad.hero.balanced.private.v1';
  const heroCAD=reflowCAD&&(balancedCAD||shot.cad_reflow?.schema==='coringa.cad.hero.private.v1');
  const heroLayout=balancedCAD?BALANCED:HERO;
  const painelCAD=reflowCAD&&shot.cad_reflow?.viewport.join(',')==='50,400,1030,962'?shot.cad_transmissao:undefined;
  const compactoCAD=reflowCAD&&shot.cad_compact_panel&&(heroCAD||shot.cad_reflow?.viewport.join(',')==='50,400,1030,1092')?shot.cad_transmissao:undefined;
  const dadosCAD=painelCAD||compactoCAD;
  const frasesCAD=balancedCAD?shot.cad_phrase_captions:undefined;
  const fraseCAD=frasesCAD?.find(c=>now-shot.start>=c.start&&now-shot.start<c.end);
  if(dadosCAD&&(dadosCAD.schema!=='coringa.cad.transmission.panel.v1'||dadosCAD.publish!==false||
    !['REDUÇÃO OBSERVADA','MULTIPLICAÇÃO OBSERVADA'].includes(dadosCAD.modo)||
    ![dadosCAD.razao,dadosCAD.entrada,dadosCAD.saida].every(s=>typeof s==='string'&&s.length<=20)))
    throw new Error('E46-PANEL');
  if(legacyVisualPreview && shot.type==='mechanism') {
    // Volta ao visual ORIGINAL 20/11 somente em prévia privada: SVG
    // integral em tela, títulos do PRÓPRIO mecanismo e rótulos grandes.
    // Esta referência é propositalmente FORA do contrato safe e não pode
    // ser confundida com o caminho liberado para produção.
    return <AbsoluteFill data-layout-review="REFERENCE_ONLY_NOT_SAFE"
      style={{background:'#071522',overflow:'hidden'}}>
      <Body shot={shot} p={p} t={now-shot.start}/>
      <div style={{position:'absolute',top:248,left:62,right:62,
        display:'flex',justifyContent:'space-between',alignItems:'center',
        color:OFF_WHITE,fontFamily:'Inter,Arial',fontSize:28,fontWeight:800,letterSpacing:2.1}}>
        <span>CORINGA <span style={{color:GOLD}}>EXPLICA</span></span>
        <span style={{fontSize:24,fontWeight:600,color:'#C2CCD5'}}>{shot.lead.toUpperCase()}</span>
      </div>
      <div style={{position:'absolute',top:302,left:62,width:140,height:5,
        background:GOLD,transformOrigin:'left',transform:`scaleX(${ease(p)})`}}/>
      <div style={{position:'absolute',left:64,right:64,bottom:206,
        color:'#CFD6E0',fontFamily:'Inter,Arial',fontWeight:600,fontSize:25}}>
        ESQUEMA ILUSTRATIVO · NÃO É FILMAGEM REAL
      </div>
      <div style={{position:'absolute',left:64,right:64,bottom:163,
        fontFamily:'Inter,Arial',color:'#ACBBC7',fontSize:22}}>
        FONTE: {shot.source_display||shot.source}
      </div>
    </AbsoluteFill>;
  }
  // Restore the media-led documentary grammar for narrated footage/photos.
  // Keep the existing protected laboratory layout for mechanisms and graphics.
  if(mediaFirst&&realMedia(shot)) {
    const credit=(shot.evidence==='representative'?'Contexto · ':'')+(shot.source_display||shot.source);
    const section=shot.lead?.toUpperCase();
    const layout=documentaryLayout(shot),slots=layout.slots;
    const brandOverlay=documentaryOverlay(shot,slots.brand);
    return <AbsoluteFill data-layout-review="MEDIA_FIRST_REVIEW_V5" data-documentary-layout={layout.mode} data-roi-status={layout.roiStatus} style={{background:'#08101A',overflow:'hidden'}}>
      {signatureHasVisibleArea(layout.media)&&<SignatureBackground/>}
      <Body shot={shot} p={p} t={now-shot.start} mediaFirst/>
      {layout.mode==='PORTRAIT_REVIEW'&&<div aria-hidden="true" style={{position:'absolute',inset:0,pointerEvents:'none',
        background:'linear-gradient(180deg,rgba(4,11,20,.16) 0%,transparent 35%,transparent 48%,rgba(4,11,20,.48) 65%,rgba(4,11,20,.10) 83%,transparent 100%)'}}/>}
      <div style={{...rectStyle(slots.brand),display:'flex',alignItems:'center',fontFamily:'Inter,Arial,sans-serif',
        fontSize:30,fontWeight:850,color:OFF_WHITE,letterSpacing:1,
        background:brandOverlay?'rgba(4,11,20,.84)':'transparent'}}>
        CORINGA <span style={{color:GOLD,marginLeft:7}}>EXPLICA</span>
      </div>
      <div style={{position:'absolute',left:slots.brand[0],top:slots.brand[3]+1,width:130,height:3,background:GOLD}}/>
      {section&&<MeasuredDocText role="section" shot={shot} rect={slots.section} text={section} probe={textProbe}/>}
      <MeasuredDocText role="source" shot={shot} rect={slots.source} text={credit} probe={textProbe}/>
    </AbsoluteFill>;
  }
  if(shot.type==='scene_graph') {
    if(!shot.scene_graph||shot.evidence!=='explainer')throw new Error('E201-ESQUEMA');
    return <SceneGraphE201 data={shot.scene_graph} t={now-shot.start} duration={duration} headline={shot.headline} source={shot.source_display||shot.source}/>;
  }
  if(shot.type==='animation_clip') {
    // Reproduce the verified full vertical clip, never crop or duplicate its baked labels.
    return <AbsoluteFill style={{background:'#08101A'}}><Body shot={shot} p={p} t={now-shot.start}/></AbsoluteFill>;
  }
  if(shot.type==='atlas_map') {
    // O clip ATLAS antigo tem tipografia/attribution rasterizadas internamente.
    // Não fingir que o render está homologado pela área segura nova.
    // Gate Python bloqueia safe_area_profile em atlas_map até recertificação.
    return <AbsoluteFill style={{background:'#08101A'}}>
      <Body shot={shot} p={p} t={now-shot.start}/>
    </AbsoluteFill>;
  }
  return <AbsoluteFill style={{background:'#08101A',overflow:'hidden'}}>
    <SafeBody shot={shot} p={p} t={now-shot.start} subtitleMode={subtitleMode} portraitExperiment={portraitExperiment}/>
    {!shot.graphic_original&&shot.type!=='mechanism'&&shot.type!=='video'&&shot.type!=='cad_preview'&&
      <AbsoluteFill style={{pointerEvents:'none',background:
        'linear-gradient(180deg,rgba(3,8,16,.38),transparent 40%,rgba(3,8,16,.68))'}}/>}
    {/* Camada editorial universal. Não repetir logo+linha no topo de cada card. */}
    <div data-safe-role="brand" style={{...(heroCAD?rectStyle(heroLayout.brand):safeSlot('brand')),
      fontFamily:'Inter,Arial,sans-serif',fontSize:heroCAD?19:26,fontWeight:900,
      color:OFF_WHITE,letterSpacing:.8,whiteSpace:'nowrap'}}>
      CORINGA <span style={{color:GOLD}}>EXPLICA</span>
    </div>
    <div data-safe-role="section" style={{...(heroCAD?rectStyle(heroLayout.section):portraitExperiment&&shot.type==='mechanism'&&
      (MECH.native_portrait as readonly string[]).includes(shot.mechanism||'')?
      rectStyle(MECH.mechanism_section):safeSlot('section')),
      fontFamily:'Inter,Arial,sans-serif',fontWeight:750,fontSize:heroCAD?16:22,
      color:shot.type==='cad_preview'&&shot.cad_warning?'#FFB1A0':'#B8CCD8',letterSpacing:1.35,overflow:'hidden',
      textOverflow:'ellipsis',whiteSpace:'nowrap'}}>
      {shot.type==='cad_preview'&&shot.cad_warning?(shot.cad_warning.includes('INTERFERÊNCIA DETECTADA')?'INTERFERÊNCIA · NÃO VALIDADO':'CONTATO PENDENTE · NÃO VALIDADO'):shot.lead.toUpperCase()}
    </div>
    {shot.type==='mechanism'&&!subtitleMode&&
      (MECH.native_portrait as readonly string[]).includes(shot.mechanism||'')&&
      <div data-safe-role="mechanism_headline"
        style={{...rectStyle(MECH.headline),color:OFF_WHITE,
          fontFamily:'Inter,Arial,sans-serif',fontWeight:900,
          lineHeight:1.06,letterSpacing:-.6,
          overflow:'hidden',overflowWrap:'break-word',
          fontSize:shot.headline.length>50?31:shot.headline.length>38?36:
            shot.headline.length>27?42:46}}>
        {shot.headline}
      </div>}
    {shot.type==='mechanism'&&!subtitleMode&&<div data-safe-role="mechanism_step"
      style={{...rectStyle(MECH.step),display:'flex',alignItems:'center',
        fontFamily:'Inter,Arial,sans-serif',fontSize:(active?.label||shot.headline).length>46?28:34,
        fontWeight:900,lineHeight:1.07,color:OFF_WHITE,letterSpacing:-.45,
        textShadow:'0 2px 12px rgba(0,0,0,.8)'}}>
      <span style={{color:GOLD,marginRight:8}}>●</span>{active?.label||shot.headline}
    </div>}
    {!subtitleMode&&active&&!reflowCAD&&!shot.graphic_original&&shot.type!=='mechanism'&&<div data-safe-role="cue"
      style={{...safeSlot('cue'),fontFamily:'Inter,Arial,sans-serif',
        fontSize:active.label.length>32?24:28,fontWeight:900,color:GOLD,
        opacity:ease(age/.20),overflow:'hidden',lineHeight:1.15,
        transform:`translateY(${(1-ease(age/.20))*8}px)`}}>
      {active.label}
    </div>}
    {!subtitleMode&&!reflowCAD&&shot.type!=='mechanism'&&!shot.graphic_original&&<div data-safe-role="headline"
      style={{...safeSlot('headline'),color:OFF_WHITE,
        textShadow:'0 2px 14px rgba(0,0,0,.78)',
        overflow:'hidden',opacity:ease((now-shot.start-.08)/.25)}}>
      <Caption text={shot.headline} highlighted={shot.highlight}/>
    </div>}
    {!subtitleMode&&!reflowCAD&&shot.type!=='mechanism'&&<div data-safe-role="subject" style={{...safeSlot('subject'),
      color:'#D4E1E9',fontFamily:'Inter,Arial',fontSize:21,
      fontWeight:650,lineHeight:1.15,overflow:'hidden'}}>
      {shot.evidence==='representative'?'IMAGEM DE CONTEXTO · '+shot.subject:shot.subject}
    </div>}
    {painelCAD&&!subtitleMode&&<div data-cad-transmission-panel="true"
      style={{...rectStyle([160,974,760,1187]),fontFamily:"Inter,Arial,sans-serif",color:OFF_WHITE,overflow:"hidden"}}>
      <div style={{display:"flex",alignItems:"baseline",gap:20,borderBottom:"2px solid #344858",paddingBottom:8}}>
        <span style={{fontSize:53,fontWeight:900,color:GOLD,letterSpacing:-2}}>{painelCAD.razao}</span>
        <span style={{fontSize:22,fontWeight:750,letterSpacing:.6}}>{painelCAD.modo}</span>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 35px 1fr",alignItems:"center",gap:12,marginTop:10}}>
        <div><div style={{fontSize:19,color:"#B8CCD8",fontWeight:700}}>ENTRADA</div><div style={{fontSize:painelCAD.entrada.length>12?27:38,fontWeight:850}}>{painelCAD.entrada}</div></div>
        <div style={{fontSize:30,color:GOLD}}>→</div>
        <div><div style={{fontSize:19,color:"#B8CCD8",fontWeight:700}}>SAÍDA</div><div style={{fontSize:painelCAD.saida.length>12?27:38,fontWeight:850}}>{painelCAD.saida}</div></div>
      </div>
      <div style={{fontSize:19,color:"#B8CCD8",marginTop:8}}>Totais da trajetória calculada</div>
    </div>}
    {compactoCAD&&!frasesCAD&&!subtitleMode&&<div data-cad-compact-panel="true" data-safe-role="mechanism_step"
      style={{...rectStyle(balancedCAD?BALANCED.step:MECH.step),fontFamily:"Inter,Arial,sans-serif",color:OFF_WHITE,overflow:"hidden",display:"flex",alignItems:"center",gap:18}}>
      {p<.5?<><div style={{fontSize:48,fontWeight:900,letterSpacing:-1.4,color:GOLD,whiteSpace:"nowrap"}}>{compactoCAD.razao}</div>
      <div style={{fontSize:23,fontWeight:800,lineHeight:1.06}}>{compactoCAD.modo}</div></>:<>
        <div style={{flex:1,minWidth:0}}><div style={{fontSize:18,color:"#B8CCD8",fontWeight:700}}>ENTRADA · TOTAL</div><div style={{fontSize:compactoCAD.entrada.length>12?24:36,fontWeight:850,lineHeight:1.08}}>{compactoCAD.entrada}</div></div>
        <span style={{fontSize:30,color:GOLD}}>→</span>
        <div style={{flex:1,minWidth:0}}><div style={{fontSize:18,color:"#B8CCD8",fontWeight:700}}>SAÍDA · TOTAL</div><div style={{fontSize:compactoCAD.saida.length>12?24:36,fontWeight:850,lineHeight:1.08}}>{compactoCAD.saida}</div></div>
      </>}
    </div>}
    {reflowCAD&&!painelCAD&&!compactoCAD&&!frasesCAD&&!subtitleMode&&<div data-safe-role="mechanism_step"
      style={{...rectStyle(balancedCAD?BALANCED.step:MECH.step),overflow:'hidden',fontFamily:'Inter,Arial,sans-serif',
        color:OFF_WHITE,fontWeight:800,lineHeight:1.12}}>
      <div style={{fontSize:25,color:GOLD}}>{active?.label||''}</div>
      <div style={{fontSize:29,overflowWrap:'break-word'}}>{shot.headline}</div>
    </div>}
    {frasesCAD&&!subtitleMode&&<div data-safe-role="mechanism_step" data-cad-phrase="true" style={{...rectStyle(BALANCED.step),fontFamily:"Inter,Arial,sans-serif",fontSize:30,fontWeight:800,color:OFF_WHITE,lineHeight:1.12,display:"flex",alignItems:"center",overflow:"hidden"}}>{fraseCAD?.text||""}</div>}
    <div data-safe-role="source" style={{...(balancedCAD?rectStyle(BALANCED.source):safeSlot('source')),
      color:'#B9C9D4',fontFamily:'Inter,Arial',fontSize:18.5,
      lineHeight:1.12,fontWeight:550,overflow:'hidden'}}>
      {shot.type==='mechanism'?'ESQUEMA ILUSTRATIVO · ':shot.type==='cad_preview'?'REPRESENTAÇÃO CAD · ':''}FONTE: {shot.source_display || shot.source}
    </div>
  </AbsoluteFill>;
};
export const FilmeEditorial: React.FC<FilmProps> = ({shots,duracao,preview=true,
  private_review_only=false,safe_zone_debug=false,subtitle_mode=false,reference_style_preview=false,portrait_experiment=false,cad_narration_asset,scene_narration_asset,documentary_captions,documentary_caption_origin,animation_policy_mode,documentary_media_preview=false,documentary_text_probe=false}) => {
  const frame=useCurrentFrame(),fps=useVideoConfig().fps,t=frame/fps;
  // E211: check actual resolved renderer on every input, including cached or manually authored props.
  const legacyQA=animation_policy_mode===animationPolicy.legacy_mode;
  if(documentary_text_probe&&(!preview||!private_review_only))throw new Error('E290-TEXT-PROBE-PRIVATE');
  if(documentary_media_preview&&(!preview||!private_review_only||legacyQA||reference_style_preview||portrait_experiment))
    throw new Error('E260-MEDIA-PREVIEW-PRIVATE');
  if(animation_policy_mode!==undefined&&animation_policy_mode!=='EDITORIAL'&&!legacyQA)
    throw new Error('E211-MODO-INVALIDO');
  if(legacyQA&&(!preview||!private_review_only||documentary_captions?.length||scene_narration_asset||cad_narration_asset))
    throw new Error('E211-LEGADO-SOMENTE-QA-SEM-NARRACAO');
  const registry=animationPolicy.renderers as Record<string,{status:string}>;
  for(const s of shots){
    const key=s.type==='mechanism'?'mechanism:'+(s.mechanism||''):
      s.type==='scene_graph'?'scene_graph:'+(s.scene_graph?.schema||''):
      s.type==='cad_preview'?'cad_preview':s.type==='animation_clip'?'animation_clip:'+(s.animation_proof?.schema||''):null;
    if(!key)continue;
    if(s.type==='animation_clip'){
      const p=s.animation_proof;
      const candidates=animationPolicy.external_candidates as Record<string,{status:string;reference_sha256?:string;reference_run?:number;frames?:number;fps?:number;dimensions?:number[]}>;
      const e=p?candidates[p.renderer]:undefined;
      if(!p||!e||e.status!=='CANDIDATO'||!e.frames||!e.fps||p.sha256!==e.reference_sha256||p.run!==e.reference_run||
        p.frames!==e.frames||p.fps!==e.fps||p.dimensions?.join(',')!==e.dimensions?.join(',')||
        p.publish!==false||p.viewport!=='INTEGRAL_SEM_CROP'||p.status!=='CANDIDATO'||p.geometry_approval!=='PENDENTE'||
        p.midia_adequada!==false||s.evidence!=='explainer'||s.asset!=='animation_e213/'+p.sha256+'.mp4'||
        !p.acao?.trim()||!p.lacuna?.trim()||!['BUSCA_SEM_REGISTRO_ADEQUADO','IMPOSSIVEL_FILMAR'].includes(p.motivo_lacuna)||
        Math.abs(p.duration_s-e.frames/e.fps)>1e-6||
        Math.abs(s.end-s.start-Math.ceil(e.frames/e.fps*30-1e-8)/30)>1e-6||
        Math.abs(s.start*30-Math.round(s.start*30))>1e-6)
        throw new Error('E213-PROVA-INVALIDA '+s.id);
    }
    const status=registry[key]?.status;
    if(!status||(status==='REPROVADO'&&!legacyQA)||
      ((status==='LABORATORIO'||status==='CANDIDATO')&&(!preview||!private_review_only)))
      throw new Error('E211-ROTA-BLOQUEADA '+s.id+' '+key);
  }
  if(shots.some(s=>s.type==='cad_preview'||s.type==='scene_graph'||s.type==='animation_clip') && (!preview || !private_review_only))
    throw new Error('E28-CAD-PRIVATE-ONLY');
  if(cad_narration_asset&&(!preview||!private_review_only||subtitle_mode||!/^cad_e47\/[0-9a-f]{64}\.wav$/.test(cad_narration_asset)||shots.some(s=>s.type!=='cad_preview'||s.cad_reflow?.schema!=='coringa.cad.hero.balanced.private.v1')))
    throw new Error('E47-PRIVATE-AUDIO');
  if(scene_narration_asset&&(!preview||!private_review_only||cad_narration_asset||!/^e202\/[0-9a-f]{64}\.wav$/.test(scene_narration_asset)||(!documentary_captions?.length&&!shots.some(s=>s.type==='scene_graph'))))
    throw new Error('E202-PRIVATE-AUDIO');
  if(documentary_captions?.length&&(!preview||!private_review_only||!scene_narration_asset||
      !['PALAVRAS_MEDIDAS','FRASES_MEDIDAS_LAB'].includes(documentary_caption_origin||'')))
    throw new Error('E207-PRIVATE-CAPTIONS');
  const shot=shots.findIndex(s=>t>=s.start&&t<s.end);
  const docCap=shot>=0&&shots[shot].type!=='scene_graph'?documentary_captions?.find(g=>t>=g.start&&t<g.end):undefined;
  return <AbsoluteFill style={{background:'#050A12'}}>
    {cad_narration_asset&&<Audio src={staticFile(cad_narration_asset)}/>}
    {scene_narration_asset&&<Audio src={staticFile(scene_narration_asset)}/>}
    {shot>=0&&<FilmShotView shot={shots[shot]} total={duracao} index={shot} subtitleMode={subtitle_mode||Boolean(documentary_captions?.length&&shots[shot].type!=='scene_graph')} legacyVisualPreview={Boolean(preview&&private_review_only&&reference_style_preview)} portraitExperiment={Boolean(preview&&private_review_only&&portrait_experiment)} mediaFirst={Boolean(preview&&private_review_only&&(documentary_captions?.length||documentary_media_preview))} textProbe={documentary_text_probe}/>}
    {docCap&&shots[shot].type==='animation_clip'&&(()=>{throw new Error('E213-LEGENDA-NAO-RECERTIFICADA')})()}
    {docCap&&realMedia(shots[shot])&&<MeasuredDocText role="subtitle" shot={shots[shot]} rect={documentaryLayout(shots[shot]).slots.subtitle}
      text={docCap.words.map(w=>w.w).join(' ')} probe={documentary_text_probe}>
      {docCap.words.map((w,i)=><span key={i} style={{color:w.hl?GOLD:OFF_WHITE}}>{w.w}{i<docCap.words.length-1?' ':''}</span>)}
    </MeasuredDocText>}
    {docCap&&!realMedia(shots[shot])&&<div data-safe-role="subtitle" style={{...safeSlot('subtitle'),display:'flex',alignItems:'center',
        justifyContent:'center',textAlign:'center',pointerEvents:'none'}}>
      <div style={{fontFamily:'Inter,Arial,sans-serif',fontWeight:900,fontSize:44,lineHeight:1.08,color:OFF_WHITE,
        padding:'8px 14px',background:'rgba(4,11,20,.74)',borderRadius:8,textShadow:'0 2px 8px #000'}}>
        {docCap.words.map((w,i)=><span key={i} style={{color:w.hl?GOLD:OFF_WHITE}}>{w.w}{i<docCap.words.length-1?' ':''}</span>)}
      </div>
    </div>}
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
    {legacyQA&&<div style={{position:'absolute',top:210,left:0,right:0,zIndex:100,
        color:'#FFF',background:'#8D2525',padding:12,textAlign:'center',fontSize:28,fontWeight:900}}>
      ESTILO REPROVADO · REGRESSÃO HISTÓRICA · NÃO ENTREGAR
    </div>}
    {preview&&private_review_only&&reference_style_preview&&<div
      style={{position:'absolute',top:105,left:0,right:0,
        color:GOLD,textAlign:'center',fontSize:20,fontWeight:850,
        fontFamily:'Inter,Arial'}}>
      REFERÊNCIA VISUAL · FORA DA SAFE · NÃO PUBLICAR
    </div>}
    {preview&&<div style={{position:'absolute',bottom:40,left:0,right:0,textAlign:'center',
      fontFamily:'Inter,Arial',color:'#CFD6E0',opacity:.7,fontSize:20,letterSpacing:1.1}}>
      {private_review_only ? 'PRÉVIA TÉCNICA · DIREITOS PENDENTES · NÃO PUBLICAR' : 'PRÉVIA PRIVADA · NÃO PUBLICADO'}
    </div>}
  </AbsoluteFill>;
};
