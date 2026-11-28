export type Point=[number,number];
export type Layer={id:string;kind:'rock'|'magma'|'void'|'boundary';points:Point[]};
export type State={id:string;title:string;label:string;at:number;anchorWord:string;transition:number;layers:Layer[];arrows:{from:Point;to:Point}[]};
export type CausalSequence={schema:'coringa.causal.vector.private.v1';publish:false;scale:'illustrative_not_to_scale';sourceSha:string;review:string;credit:string;states:State[]};
const finite=(v:unknown):v is number=>typeof v==='number'&&Number.isFinite(v);
const str=(s:unknown,n:number)=>typeof s==='string'&&s.trim().length>0&&s.length<=n;
const point=(p:unknown):p is Point=>Array.isArray(p)&&p.length===2&&p.every(finite)&&p[0]>=8&&p[0]<=832&&p[1]>=8&&p[1]<=542;
export function validateCausalSequence(c:CausalSequence,duration:number){
 if(!c||c.schema!=='coringa.causal.vector.private.v1'||c.publish!==false||c.scale!=='illustrative_not_to_scale'||!str(c.review,200)||!str(c.credit,100)||! /^[a-f0-9]{64}$/.test(c.sourceSha)||!finite(duration)||!Array.isArray(c.states)||c.states.length<2||c.states.length>6)throw Error('E391-CONTRACT');
 const ids=new Set<string>();
 for(const [i,s] of c.states.entries()){
  if(!str(s.id,40)||ids.has(s.id)||!str(s.title,40)||!str(s.label,58)||!str(s.anchorWord,30)||!finite(s.at)||!finite(s.transition)||s.transition<0||s.transition>1.5||s.at<0||(i===0?(s.at!==0||s.transition!==0):(s.at<=c.states[i-1].at||s.transition<.15))||s.at+s.transition+.65>(c.states[i+1]?.at??duration))throw Error('E391-STATE');
  ids.add(s.id);
  if(!Array.isArray(s.layers)||s.layers.length<1||s.layers.length>16||new Set(s.layers.map(l=>l.id)).size!==s.layers.length||s.layers.some(l=>!str(l.id,40)||!['rock','magma','void','boundary'].includes(l.kind)||!Array.isArray(l.points)||l.points.length<3||l.points.length>32||!l.points.every(point)))throw Error('E391-LAYER');
  if(i&&(s.layers.length!==c.states[0].layers.length||s.layers.some((l,j)=>l.id!==c.states[0].layers[j].id||l.kind!==c.states[0].layers[j].kind||l.points.length!==c.states[0].layers[j].points.length)))throw Error('E391-TOPOLOGY');
  if(!Array.isArray(s.arrows)||s.arrows.length>4||s.arrows.some(a=>!point(a.from)||!point(a.to)||Math.hypot(a.to[0]-a.from[0],a.to[1]-a.from[1])<20))throw Error('E391-ARROW');
 }
 return c;
}
export function causalFrame(c:CausalSequence,t:number){
 let i=0;for(let j=1;j<c.states.length;j++)if(c.states[j].at<=t)i=j;
 const s=c.states[i],prior=c.states[Math.max(0,i-1)],p=i?Math.max(0,Math.min(1,(t-s.at)/s.transition)):1;
 const layers=s.layers.map((l,j)=>({...l,points:l.points.map((v,k)=>[prior.layers[j].points[k][0]+(v[0]-prior.layers[j].points[k][0])*p,prior.layers[j].points[k][1]+(v[1]-prior.layers[j].points[k][1])*p] as Point)}));
 return {index:i,id:s.id,title:s.title,label:s.label,progress:p,layers,arrows:s.arrows};
}
