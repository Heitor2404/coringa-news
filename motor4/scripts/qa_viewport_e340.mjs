import {bundle} from '@remotion/bundler';
import {selectComposition,renderStill} from '@remotion/renderer';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e340'),prep=JSON.parse(readFileSync(resolve(root,'replay.json'),'utf8'));
const out={publish:false,semantic_approval:false,actual_app_ui_verified:false,frames:[],errors:[]};
const save=()=>writeFileSync(resolve(root,'comparison.json'),JSON.stringify(out,null,2));
const area=b=> (b[2]-b[0])*(b[3]-b[1])/(1080*1920);
try{
 const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
 const browserExecutable=process.env.REMOTION_CHROME;
 for(const r of prep.records.filter(r=>r.status==='READY_PRIVATE_FRAGMENT')){
  const input=JSON.parse(readFileSync(resolve(root,r.id,'props.json'),'utf8'));
  for(const trial of [false,true]){
   const props={...input,shots:input.shots.map(s=>({...s,documentary_observed_viewport_trial:s.documentary_observed_viewport_trial===true,documentary_balance_trial:trial&&s.documentary_balance_trial===true}))};
   const composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps:props,browserExecutable});
   for(const t of (r.id==='lava'?[.8,2.7]:[.8])){
    const logs=[],name=r.id+'-'+t+(trial?'-balanced':'-v3')+'.png';
    await renderStill({serveUrl,composition,inputProps:props,browserExecutable,frame:Math.round(t*composition.fps),output:resolve(root,name),logLevel:'info',
     onBrowserLog:log=>{const text=String(log.text||'');const i=text.indexOf('E290_TEXT ');if(i>=0){try{logs.push(JSON.parse(text.slice(i+10)))}catch{out.errors.push('PARSE')}}}});
    const rows=['section','subtitle','source'].map(role=>logs.filter(x=>x.role===role).at(-1));
    if(rows.some(r=>!r)){out.errors.push('MISSING '+name);continue;}
    const geo=rows[0].media,mode=rows[0].safeTrialStatus,inside=rows.every(r=>r.actual[0]>=149&&r.actual[1]>=299&&r.actual[2]<=771&&r.actual[3]<=1241);
    const collision=rows.some(r=>r.evidenceCollision),fits=rows.every(r=>r.fits),unknown=rows.some(r=>r.unknownEvidenceOverlay);
    const base=out.frames.find(x=>x.id===r.id&&x.t===t&&!x.trial);
    const fraction=area(geo),gain=base?fraction/base.fraction-1:0;
    const center=(geo[1]+geo[3])/2,shift=base?(base.geometry[1]+base.geometry[3])/2-center:0;
    if(trial&&mode==='V4_BALANCED_VIEWPORT'&&(!r.balance_authorized||r.integral_required||!inside||collision||!fits||unknown||Math.abs(gain)>.0001||shift<59.9||center>1080))out.errors.push('UNSAFE OR UNBALANCED '+name);
    if(trial&&r.id!=='lava'&&base&&JSON.stringify(base.geometry)!==JSON.stringify(geo))out.errors.push('CONTROL CHANGED '+name);
    if(trial&&r.id==='lava'&&mode!=='V4_BALANCED_VIEWPORT')out.errors.push('NO BALANCED EXPANSION '+name);
    out.frames.push({id:r.id,t,trial,name,mode,geometry:geo,fraction,gain,center,shift,inside,collision,fits,unknown,measurements:rows});save();
   }
  }
 }
}catch(e){out.errors.push(String(e))}
save();
console.log('E340',out.frames.map(r=>[r.id,r.t,r.trial,r.mode,r.fraction,r.gain]),out.errors);
if(prep.records.some(r=>r.status!=='READY_PRIVATE_FRAGMENT')||out.frames.length!==8||out.errors.length)process.exitCode=1;
