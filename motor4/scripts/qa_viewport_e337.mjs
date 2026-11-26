import {bundle} from '@remotion/bundler';
import {selectComposition,renderStill} from '@remotion/renderer';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e337'),prep=JSON.parse(readFileSync(resolve(root,'replay.json'),'utf8'));
const out={publish:false,semantic_approval:false,actual_app_ui_verified:false,frames:[],errors:[]};
const save=()=>writeFileSync(resolve(root,'comparison.json'),JSON.stringify(out,null,2));
const area=b=> (b[2]-b[0])*(b[3]-b[1])/(1080*1920);
try{
 const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
 const browserExecutable=process.env.REMOTION_CHROME;
 for(const r of prep.records.filter(r=>r.status==='READY_PRIVATE_FRAGMENT')){
  const input=JSON.parse(readFileSync(resolve(root,r.id,'props.json'),'utf8'));
  for(const trial of [false,true]){
   const props={...input,shots:input.shots.map(s=>({...s,documentary_observed_viewport_trial:trial&&s.documentary_observed_viewport_trial===true}))};
   const composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps:props,browserExecutable});
   for(const t of [.8,2.7]){
    const logs=[],name=r.id+'-'+t+(trial?'-trial':'-baseline')+'.png';
    await renderStill({serveUrl,composition,inputProps:props,browserExecutable,frame:Math.round(t*composition.fps),output:resolve(root,name),logLevel:'info',
     onBrowserLog:log=>{const text=String(log.text||'');const i=text.indexOf('E290_TEXT ');if(i>=0){try{logs.push(JSON.parse(text.slice(i+10)))}catch{out.errors.push('PARSE')}}}});
    const rows=['section','subtitle','source'].map(role=>logs.filter(x=>x.role===role).at(-1));
    if(rows.some(r=>!r)){out.errors.push('MISSING '+name);continue;}
    const geo=rows[0].media,mode=rows[0].safeTrialStatus,inside=rows.every(r=>r.actual[0]>=149&&r.actual[1]>=299&&r.actual[2]<=771&&r.actual[3]<=1241);
    const collision=rows.some(r=>r.evidenceCollision),fits=rows.every(r=>r.fits),unknown=rows.some(r=>r.unknownEvidenceOverlay);
    const base=out.frames.find(x=>x.id===r.id&&x.t===t&&!x.trial);
    const fraction=area(geo),gain=base?fraction/base.fraction-1:0;
    if(trial&&mode==='V3_OBSERVED_VIEWPORT'&&(!r.trial_authorized||r.integral_required||!inside||collision||!fits||unknown||gain<.149))out.errors.push('UNSAFE OR NO GAIN '+name);
    if(trial&&mode!=='V3_OBSERVED_VIEWPORT'&&base&&JSON.stringify(base.geometry)!==JSON.stringify(geo))out.errors.push('FALLBACK CHANGED '+name);
    out.frames.push({id:r.id,t,trial,name,mode,geometry:geo,fraction,gain,inside,collision,fits,unknown,measurements:rows});save();
   }
  }
 }
}catch(e){out.errors.push(String(e))}
save();
console.log('E337',out.frames.map(r=>[r.id,r.t,r.trial,r.mode,r.fraction,r.gain]),out.errors);
if(prep.records.some(r=>r.status!=='READY_PRIVATE_FRAGMENT')||out.frames.length!==12||out.errors.length)process.exitCode=1;
