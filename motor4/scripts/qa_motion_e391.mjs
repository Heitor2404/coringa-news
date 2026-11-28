import {bundle} from '@remotion/bundler';
import {selectComposition,renderStill,renderMedia} from '@remotion/renderer';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e391'),out={publish:false,visual_approval:'PENDING',rows:[],errors:[]};
const save=()=>writeFileSync(resolve(root,'comparison.json'),JSON.stringify(out,null,2));
try{
 const p=JSON.parse(readFileSync(resolve(root,'variant.json'),'utf8')),c=p.sequence;
 const serveUrl=await bundle({entryPoint:resolve('remotion/src/e391-index.tsx'),publicDir:resolve('remotion/public')});
 const browserExecutable=process.env.REMOTION_CHROME,input={...p,probe:true};
 const composition=await selectComposition({serveUrl,id:'Causal2D-E391',inputProps:input,browserExecutable}),fps=composition.fps;
 if(composition.durationInFrames!==428||fps!==30)throw Error('E391-DURATION');
 const frames=new Set([0,composition.durationInFrames-1,...c.states.flatMap(x=>[Math.max(0,Math.ceil(x.at*fps)-1),Math.ceil((x.at+x.transition/2)*fps),Math.ceil((x.at+x.transition+.1)*fps)]),...p.captions.map(g=>Math.ceil((g.start+g.end)/2*fps))]);
 for(const frame of [...frames].filter(f=>f<composition.durationInFrames).sort((a,b)=>a-b)){
  const logs=[];
  await renderStill({serveUrl,composition,inputProps:input,browserExecutable,frame,output:resolve(root,'motion-causal-'+frame+'.png'),logLevel:'info',onBrowserLog:l=>{const v=String(l.text||''),i=v.indexOf('E391_CAUSAL ');if(i>=0)try{logs.push(JSON.parse(v.slice(i+12)))}catch{out.errors.push('PARSE')}}});
  const t=frame/fps,index=c.states.findLastIndex(x=>x.at<=t),row=logs.at(-1),g=p.captions.find(g=>g.start<=t&&t<g.end),sub=row?.rows.find(x=>x.role==='subtitle');
  if(!row?.fit||row.index!==index)out.errors.push('STAGE '+frame);
  if(g?(!sub?.fit||sub.text!==g.words.map(w=>w.w).join(' ')):Boolean(sub))out.errors.push('CAPTION '+frame);
  if(row){const state=c.states[index],prior=c.states[Math.max(0,index-1)],alpha=index?Math.max(0,Math.min(1,(t-state.at)/state.transition)):1;
   if(Math.abs(row.progress-alpha)>1e-6||row.layers.some((l,i)=>l.points.some((q,j)=>q.some((v,k)=>Math.abs(v-(prior.layers[i].points[j][k]+(state.layers[i].points[j][k]-prior.layers[i].points[j][k])*alpha))>1e-6))))out.errors.push('GEOMETRY '+frame);}
  out.rows.push({frame,t,row,subtitle:sub});save();
 }
 if(c.states.slice(1).some((x,i)=>!out.rows.some(r=>r.row?.index===i+1&&r.row.progress>0&&r.row.progress<1)))out.errors.push('NO_MOTION_SAMPLE');
 if(!out.errors.length)await renderMedia({serveUrl,composition,inputProps:p,browserExecutable,codec:'h264',outputLocation:resolve(root,'motion-causal-2d.mp4'),scale:.5,concurrency:2,logLevel:'error'});
}catch(e){out.errors.push(String(e))}
save();if(out.errors.length||out.rows.length<12)process.exitCode=1;
