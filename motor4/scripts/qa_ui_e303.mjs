// Same actual pixels and source assets in baseline and trial; no new voice.
import {bundle} from '@remotion/bundler';
import {selectComposition,renderStill} from '@remotion/renderer';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e286');
const input=JSON.parse(readFileSync(resolve(root,'props.json'),'utf8'));
const dest=resolve(root,'e303');mkdirSync(dest,{recursive:true});
const result={publish:false,actual_app_ui_verified:false,kind:'COMPOSITOR_UI_COMPARISON',frames:[],errors:[]};
const save=()=>writeFileSync(resolve(dest,'comparison.json'),JSON.stringify(result,null,2));
try{
 const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
 const browserExecutable=process.env.REMOTION_CHROME;
 // Include explicit full-source protection as a separate geometry case.
 const scenarios=[...input.shots.map(s=>({id:s.id,shot:s})),{id:'integral-contract',shot:{...input.shots[0],documentary_integral_required:true}}];
 for(const scenario of scenarios){
  let baseline;
  for(const trial of [false,true]){
   const props={...input,documentary_text_probe:true,shots:input.shots.map(s=>s.id===scenario.shot.id?{...scenario.shot,documentary_safe_trial:trial}:s)};
   const composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps:props,browserExecutable});
   const logs=[];
   await renderStill({serveUrl,composition,inputProps:props,browserExecutable,frame:Math.round((scenario.shot.start+1)*composition.fps),
     output:resolve(dest,scenario.id+(trial?'-trial':'-baseline')+'.png'),logLevel:'info',
     onBrowserLog:log=>{const text=String(log.text||'');const i=text.indexOf('E290_TEXT ');if(i>=0){try{logs.push(JSON.parse(text.slice(i+10)))}catch{result.errors.push('PARSE')}}}});
   const rows=['section','subtitle','source'].map(role=>logs.filter(x=>x.shot===scenario.shot.id&&x.role===role).at(-1));
   if(rows.some(r=>!r)){result.errors.push('MISSING '+scenario.id);continue;}
   const geometry=rows[0].media.join(',');
   if(!trial)baseline=geometry;
   else if(geometry!==baseline)result.errors.push('MEDIA_CHANGED '+scenario.id);
   const accepted=trial&&rows.every(r=>r.safeTrialStatus==='CANDIDATE_GEOMETRY');
   const textFits=rows.every(r=>r.fits);
   const inside=rows.every(r=>r.actual[0]>=149&&r.actual[1]>=299&&r.actual[2]<=771&&r.actual[3]<=1241);
   const collision=rows.some(r=>r.evidenceCollision);
   if(accepted&&collision)result.errors.push('PROTECTED_COLLISION '+scenario.id);
   const status=!trial?'BASELINE':!accepted?'BLOCKED_EVIDENCE':!textFits?'BLOCKED_TEXT_OVERFLOW':!inside?'BLOCKED_GEOMETRY':'PRIVATE_CANDIDATE';
   result.frames.push({id:scenario.id,trial,status,geometry,textFits,inside,collision,measurements:rows});
   save();
  }
 }
}catch(e){result.errors.push(String(e))}
save();
console.log('E303',result.frames.map(r=>[r.id,r.trial,r.status]),result.errors);
if(result.frames.length!==10||result.errors.length||!result.frames.some(r=>r.status==='PRIVATE_CANDIDATE'))process.exitCode=1;
