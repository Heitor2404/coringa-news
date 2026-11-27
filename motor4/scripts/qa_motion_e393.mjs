import {bundle} from '@remotion/bundler';import {selectComposition,renderStill,renderMedia} from '@remotion/renderer';import {readFileSync,writeFileSync} from 'node:fs';import {resolve} from 'node:path';
const root=resolve('../stage_documental/e393'),p=JSON.parse(readFileSync(resolve(root,'variant.json'),'utf8')),out={publish:false,visual_approval:'PENDING',rows:[],gearRows:[],errors:[]};
const save=()=>writeFileSync(resolve(root,'comparison.json'),JSON.stringify(out,null,2));
try{
 const serveUrl=await bundle({entryPoint:resolve('remotion/src/e393-index.tsx'),publicDir:resolve('remotion/public')});const browserExecutable=process.env.REMOTION_CHROME,input={...p,probe:true},composition=await selectComposition({serveUrl,id:'CausalCutawayE393',inputProps:input,browserExecutable}),fps=30;
 if(composition.durationInFrames!==428||composition.fps!==fps)throw Error('E393-DURATION');
 const frames=new Set([0,427,...p.events.flatMap((e,i)=>[-.04,.25,.5,.75,1.01].map(x=>Math.ceil((e.tempo_s+x*p.transitions[i])*fps))),...p.captions.map(g=>Math.ceil((g.start+g.end)/2*fps))]);
 for(const frame of [...frames].filter(f=>f>=0&&f<428).sort((a,b)=>a-b)){
  const logs=[];await renderStill({serveUrl,composition,inputProps:input,browserExecutable,frame,output:resolve(root,'motion-causal-'+frame+'.png'),logLevel:'info',onBrowserLog:l=>{const v=String(l.text||''),prefix='E392_BOARD ',i=v.indexOf(prefix);if(i>=0)try{logs.push(JSON.parse(v.slice(i+prefix.length)))}catch{out.errors.push('PARSE')}}});
  const t=frame/fps,row=logs.at(-1),idx=p.events.filter(e=>e.tempo_s<=t).length,expected=p.captions.find(g=>g.start<=t&&t<g.end)?.words.map(w=>w.w).join(' ')??'';
  const progress=p.events.map((e,i)=>{const q=Math.max(0,Math.min(1,(t-e.tempo_s)/p.transitions[i]));return q*q*(3-2*q)});
  if(!row?.fit||row.index!==idx||row.caption!==expected||row.collisions!==false||JSON.stringify(row.state)!==JSON.stringify(p.boards[idx].state)||!row.progress?.every((v,i)=>Math.abs(v-progress[i])<1e-7)||!row.magma||!row.top||!row.camera||row.camera.scale<1||row.camera.scale>1.04501||row.solidBlocks?.some(b=>b.opacity!=='1')){out.errors.push('FRAME '+frame);console.error('E393_QA',JSON.stringify({frame,row,expected,progress}));}
  out.rows.push({frame,t,row});save();
 }
 for(let i=0;i<3;i++){const mid=out.rows.filter(x=>x.row?.progress[i]>0&&x.row.progress[i]<1);if(mid.length<2||i<2&&new Set(mid.map(x=>i===0?x.row.magma:x.row.top)).size<2)out.errors.push('NO_CAUSAL_MOTION '+i);}
 if(!out.errors.length)await renderMedia({serveUrl,composition,inputProps:p,browserExecutable,codec:'h264',outputLocation:resolve(root,'motion-causal-2d.mp4'),scale:.75,concurrency:2,logLevel:'error'});
 const gearInput={private_review_only:true,probe:true},gear=await selectComposition({serveUrl,id:'GearMotionE394',inputProps:gearInput,browserExecutable});
 for(const frame of [0,35,70,100,135,175,220,251]){
 const logs=[];await renderStill({serveUrl,composition:gear,inputProps:gearInput,browserExecutable,frame,output:resolve(root,'motion-gears-'+frame+'.png'),logLevel:'info',onBrowserLog:l=>{const v=String(l.text||''),i=v.indexOf('E394_GEAR ');if(i>=0)logs.push(JSON.parse(v.slice(i+10)))}});
 const row=logs.at(-1);if(!row?.fit||!row.opaque||Math.abs(row.output+row.rotation*12/20)>1e-6||row.camera.scale<1||row.camera.scale>1.27001)out.errors.push('GEAR '+frame);out.gearRows.push({frame,row});save();}
 if(!out.gearRows.some(x=>Math.abs(x.row?.rotation??0)>100))out.errors.push('GEAR_MOTION');
 if(!out.errors.length)await renderMedia({serveUrl,composition:gear,inputProps:{private_review_only:true},browserExecutable,codec:'h264',outputLocation:resolve(root,'motion-gears-2d.mp4'),scale:.75,concurrency:2,logLevel:'error'});
}catch(e){out.errors.push(String(e));console.error('E393_RENDER',String(e))}
save();if(out.errors.length||out.rows.length<12)process.exitCode=1;
