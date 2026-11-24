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