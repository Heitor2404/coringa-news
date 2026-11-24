/** Declarative illustrative scene, not a physical solver or a factual certification. */
import {progresso} from './TempoVisualE200';
export type Shape={d:string;fill:string;stroke?:string;sw?:number};
export type State={t:number;x:number;y:number;scale:number;angle:number;opacity:number};
export type Actor={id:string;shapes:Shape[];states:State[];curve?:'linear'|'easeIO'|'easeOut'};
export type SceneData={schema:'coringa.scene_graph.private.v1';nature:'esquema_sem_escala';actors:Actor[];beats:{t:number;text:string}[];source:string;publish:false};
const finite=(x:unknown)=>typeof x==='number'&&Number.isFinite(x);
const color=(x:unknown)=>typeof x==='string'&&/^(#[0-9a-fA-F]{6}|none)$/.test(x);
export function validateScene(d:SceneData,dur:number){
  if(!d||d.schema!=='coringa.scene_graph.private.v1'||d.nature!=='esquema_sem_escala'||d.publish!==false||!finite(dur)||dur<=0||typeof d.source!=='string'||!d.source.startsWith('https://')||!Array.isArray(d.actors)||!d.actors.length||d.actors.length>100||!Array.isArray(d.beats)||!d.beats.length)throw new Error('E201-CONTRACT');
  const ids=new Set<string>();
  for(const a of d.actors){
    if(!a.id||ids.has(a.id)||!Array.isArray(a.shapes)||!a.shapes.length||a.shapes.length>100||!Array.isArray(a.states)||!a.states.length||a.states.length>100||!['linear','easeIO','easeOut'].includes(a.curve||'linear'))throw new Error('E201-ACTOR');
    ids.add(a.id);
    for(const s of a.shapes){
      if(typeof s.d!=='string'||s.d.length>8000||!/^[-+0-9., eEMmLlHhVvCcSsQqTtAaZz]+$/.test(s.d)||!color(s.fill)||(s.stroke!==undefined&&!color(s.stroke))||(s.sw!==undefined&&(!finite(s.sw)||s.sw<0||s.sw>40)))throw new Error('E201-SHAPE');
    }
    for(let i=0;i<a.states.length;i++){
      const k=a.states[i];
      if(![k.t,k.x,k.y,k.scale,k.angle,k.opacity].every(finite)||k.t<0||k.t>dur+1e-8||Math.abs(k.x)>2000||Math.abs(k.y)>2000||k.scale<=0||k.scale>5||k.opacity<0||k.opacity>1||(i===0&&k.t!==0)||(i>0&&k.t<=a.states[i-1].t))throw new Error('E201-STATE');
    }
  }
  if(d.beats.some((b,i)=>!finite(b.t)||b.t<0||b.t>=dur||typeof b.text!=='string'||!b.text.trim()||b.text.length>65||(i===0?b.t!==0:b.t<=d.beats[i-1].t)))throw new Error('E201-BEATS');
  return true;
}
export function stateAt(a:Actor,t:number):State{
  const ks=a.states;
  for(let i=1;i<ks.length;i++)if(t<ks[i].t){
    const l=ks[i-1],r=ks[i],p=progresso(t,l.t,r.t,a.curve||'linear');
    return {t,x:l.x+(r.x-l.x)*p,y:l.y+(r.y-l.y)*p,scale:l.scale+(r.scale-l.scale)*p,angle:l.angle+(r.angle-l.angle)*p,opacity:l.opacity+(r.opacity-l.opacity)*p};
  }
  return ks[ks.length-1];
}
/* ───── E202: contrato v2 gerado pelo compilador de cena (src/v4/formatos/cena_declarativa_e202.py) ─────
   Acrescenta, sem alterar o v1: caixa de visão por ator, tamanho, rótulo, camada, saturação, sx/sy,
   câmera mundo→tela por quadros-chave e legendas por palavra medida. Continua sem scripts, URLs ou HTML. */
export type StateV2=State&{sx:number;sy:number;sat:number;draw:number;tint:number};
export type ActorV2={id:string;label?:string|null;label_t?:[number,number];layer:'contexto'|'essencial'|'efeito'|'particula';view:[number,number,number,number];size:number;shapes:Shape[];states:StateV2[];curve?:'linear';origem:string;tracado?:boolean;tint_color?:string};
export type CamKey={t:number;x:number;y:number;zoom:number};
export type CaptionV2={start:number;end:number;words:{w:string;s:number;e:number}[]};
export type SceneDataV2={schema:'coringa.scene_graph.private.v2';nature:'esquema_sem_escala'|'esquema_com_dado_real';publish:false;source:string;sources:string[];credits:string[];headline:string;actors:ActorV2[];camera:CamKey[];beats:{t:number;text:string}[];captions:CaptionV2[];captions_origin:string};
export const BOX_V2=[36,510,1044,1450] as const;
export const CAPTION_V2=[150,365,770,485] as const;
export function validateSceneV2(d:SceneDataV2,dur:number){
  const url=(s:unknown)=>typeof s==='string'&&s.startsWith('https://');
  if(!d||d.schema!=='coringa.scene_graph.private.v2'||!['esquema_sem_escala','esquema_com_dado_real'].includes(d.nature)||d.publish!==false||!finite(dur)||dur<=0||!url(d.source)||!Array.isArray(d.sources)||!d.sources.every(url)||!Array.isArray(d.credits)||typeof d.headline!=='string'||!Array.isArray(d.actors)||!d.actors.length||d.actors.length>400||!Array.isArray(d.camera)||!d.camera.length||!Array.isArray(d.captions))throw new Error('E202-CONTRACT');
  const ids=new Set<string>();
  for(const a of d.actors){
    if(!a.id||ids.has(a.id)||!['contexto','essencial','efeito','particula'].includes(a.layer)||!Array.isArray(a.view)||a.view.length!==4||!a.view.every(finite)||a.view[2]<=0||a.view[3]<=0||!finite(a.size)||a.size<=0||a.size>3000||!Array.isArray(a.shapes)||!a.shapes.length||a.shapes.length>200||!Array.isArray(a.states)||!a.states.length||a.states.length>600||(a.label!=null&&(typeof a.label!=='string'||a.label.length>40))||(a.tint_color!==undefined&&!/^#[0-9a-fA-F]{6}$/.test(a.tint_color))||(a.label_t!==undefined&&(!Array.isArray(a.label_t)||a.label_t.length!==2||!a.label_t.every(finite)||a.label_t[1]<=a.label_t[0]))||typeof a.origem!=='string')throw new Error('E202-ACTOR');
    ids.add(a.id);
    for(const s of a.shapes)if(typeof s.d!=='string'||s.d.length>12000||!/^[-+0-9., eEMmLlHhVvCcSsQqTtAaZz]+$/.test(s.d)||!color(s.fill)||(s.stroke!==undefined&&!color(s.stroke))||(s.sw!==undefined&&(!finite(s.sw)||s.sw<0||s.sw>40)))throw new Error('E202-SHAPE');
    for(let i=0;i<a.states.length;i++){const k=a.states[i];
      if(![k.t,k.x,k.y,k.scale,k.sx,k.sy,k.angle,k.opacity,k.sat,k.draw,k.tint].every(finite)||k.draw<0||k.draw>1||k.tint<0||k.tint>1||k.t<0||k.t>dur+1e-6||Math.abs(k.x)>8000||Math.abs(k.y)>8000||k.scale<=0||k.scale>8||k.sx<=0||k.sx>20||k.sy<=0||k.sy>20||k.opacity<0||k.opacity>1||k.sat<0||k.sat>1.5||(i===0&&k.t!==0)||(i>0&&k.t<=a.states[i-1].t))throw new Error('E202-STATE');}
  }
  for(let i=0;i<d.camera.length;i++){const c=d.camera[i];if(![c.t,c.x,c.y,c.zoom].every(finite)||c.zoom<=0.1||c.zoom>4||(i===0&&c.t!==0)||(i>0&&c.t<=d.camera[i-1].t))throw new Error('E202-CAMERA');}
  for(const c of d.captions)if(!finite(c.start)||!finite(c.end)||c.end<=c.start||!Array.isArray(c.words)||!c.words.length||c.words.some(w=>typeof w.w!=='string'||!finite(w.s)||!finite(w.e)))throw new Error('E202-CAPTION');
  return true;
}
const lerp=(a:number,b:number,p:number)=>a+(b-a)*p;
export function stateAtV2(a:ActorV2,t:number):StateV2{
  const ks=a.states;
  for(let i=1;i<ks.length;i++)if(t<ks[i].t){const l=ks[i-1],r=ks[i],p=(t-l.t)/(r.t-l.t);
    return {t,x:lerp(l.x,r.x,p),y:lerp(l.y,r.y,p),scale:lerp(l.scale,r.scale,p),angle:lerp(l.angle,r.angle,p),opacity:lerp(l.opacity,r.opacity,p),sx:lerp(l.sx,r.sx,p),sy:lerp(l.sy,r.sy,p),sat:lerp(l.sat,r.sat,p),draw:lerp(l.draw,r.draw,p),tint:lerp(l.tint,r.tint,p)};}
  return ks[ks.length-1];
}
export function cameraAt(cs:CamKey[],t:number):CamKey{
  for(let i=1;i<cs.length;i++)if(t<cs[i].t){const l=cs[i-1],r=cs[i],p=progresso(t,l.t,r.t,'easeIO');
    // zoom interpolado em escala logarítmica: movimento percebido uniforme
    return {t,x:lerp(l.x,r.x,p),y:lerp(l.y,r.y,p),zoom:Math.exp(lerp(Math.log(l.zoom),Math.log(r.zoom),p))};}
  return cs[cs.length-1];
}
/** Função ÚNICA mundo→tela (técnica Lemo reimplementada): tudo que segue um ator passa por ela. */
export function worldToScreen(c:CamKey,x:number,y:number):[number,number]{
  const cx=(BOX_V2[0]+BOX_V2[2])/2,cy=(BOX_V2[1]+BOX_V2[3])/2;
  return [cx+(x-c.x)*c.zoom,cy+(y-c.y)*c.zoom];
}
