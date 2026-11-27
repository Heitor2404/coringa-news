// Generic causal timeline for a reviewed, serialized graph. Progress is editorial, not physical time.
export type Event={acao:string;tempo_s:number;depois:Record<string,string>};
export const smooth=(p:number)=>{const q=Math.max(0,Math.min(1,p));return q*q*(3-2*q)};
export function causalAt(events:Event[],durations:number[],initial:Record<string,string>,t:number){
 if(events.length!==durations.length||events.some((e,i)=>!Number.isFinite(e.tempo_s)||durations[i]<=0||i>0&&e.tempo_s<events[i-1].tempo_s+durations[i-1]))throw Error('E393-TIMELINE');
 const progress=events.map((e,i)=>smooth((t-e.tempo_s)/durations[i]));
 let index=0;const state={...initial};events.forEach((e,i)=>{if(t>=e.tempo_s){index=i+1;Object.assign(state,e.depois)}});
 return {index,state,progress};
}
// Matched SVG samples; endpoints preserve original reviewed geometry exactly.
// Closed shapes align at an explicit visual anchor, not at arbitrary path starts.
export function morphPath(a:string,b:string,p:number,closed:boolean,anchor?:[number,number]){
 if(p<=0)return a;if(p>=1)return b;
 const sample=(d:string)=>{const e=document.createElementNS('http://www.w3.org/2000/svg','path');e.setAttribute('d',d);const length=e.getTotalLength(),n=96;
 let pts=Array.from({length:n+(closed?0:1)},(_,i)=>{const q=e.getPointAtLength(length*i/n);return [q.x,q.y]});
 if(closed&&anchor){let best=Infinity,k=0;pts.forEach((q,i)=>{const v=(q[0]-anchor[0])**2+(q[1]-anchor[1])**2;if(v<best){best=v;k=i}});pts=[...pts.slice(k),...pts.slice(0,k)]}
 return pts;};
 const x=sample(a),y=sample(b);return x.map((q,i)=>(i?'L':'M')+q.map((v,j)=>(v+(y[i][j]-v)*p).toFixed(2)).join(' ')).join(' ')+(closed?' Z':'');
}
