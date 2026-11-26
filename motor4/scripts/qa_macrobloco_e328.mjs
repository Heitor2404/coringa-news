// E328: compare real versioned media; synthetic captions, not semantic review.
import {bundle} from '@remotion/bundler';
import {selectComposition,renderStill} from '@remotion/renderer';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e286'),input=JSON.parse(readFileSync(resolve(root,'props.json'),'utf8'));
const dest=resolve(root,'e328');mkdirSync(dest,{recursive:true});
const result={publish:false,actual_app_ui_verified:false,semantic_review:'PENDING',frames:[],errors:[]};
const save=()=>writeFileSync(resolve(dest,'comparison.json'),JSON.stringify(result,null,2));
try{
 const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
 const browserExecutable=process.env.REMOTION_CHROME;
 const scenarios=input.shots.map(s=>({id:s.id,shot:s}));
 for(const scenario of scenarios)for(const trial of [false,true]){
  const props={...input,documentary_text_probe:true,shots:input.shots.map(s=>s.id===scenario.id?{...s,documentary_composition_v2:trial}:s)};
  const composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps:props,browserExecutable});
  const logs=[];
  await renderStill({serveUrl,composition,inputProps:props,browserExecutable,frame:Math.round((scenario.shot.start+1)*composition.fps),
    output:resolve(dest,scenario.id+(trial?'-trial':'-baseline')+'.png'),logLevel:'info',
    onBrowserLog:log=>{const text=String(log.text||'');const i=text.indexOf('E290_TEXT ');if(i>=0){try{logs.push(JSON.parse(text.slice(i+10)))}catch{result.errors.push('PARSE')}}}});
  const rows=['section','subtitle','source'].map(role=>logs.filter(x=>x.shot===scenario.id&&x.role===role).at(-1));
  if(rows.some(r=>!r)){result.errors.push('MISSING '+scenario.id);continue;}
  const geometry=rows[0].media,inside=rows.every(r=>r.actual[0]>=149&&r.actual[1]>=299&&r.actual[2]<=771&&r.actual[3]<=1241);
  const collision=rows.some(r=>r.evidenceCollision),fits=rows.every(r=>r.fits),mode=rows[0].safeTrialStatus;
  const status=!trial?'BASELINE':!inside||collision||!fits?'REVIEW_PENDING':'GEOMETRY_CANDIDATE';
  if(trial&&mode==='V2_INTEGRAL_SAFE'&&(!inside||collision||!fits))result.errors.push('INTEGRAL_SAFE_TEXT '+scenario.id);
  if(trial&&scenario.shot.source_dimensions[0]<scenario.shot.source_dimensions[1]){
   const baseline=result.frames.find(r=>r.id===scenario.id&&!r.trial);
   if(baseline&&baseline.geometry.join(',')!==geometry.join(','))result.errors.push('PORTRAIT_CHANGED '+scenario.id);
  }
  result.frames.push({id:scenario.id,trial,status,mode,geometry,inside,collision,fits,measurements:rows});save();
 }
}catch(e){result.errors.push(String(e))}
save();
console.log('E328',result.frames.map(r=>[r.id,r.trial,r.status,r.mode]),result.errors);
if(result.frames.length!==8||result.errors.length||!result.frames.some(r=>r.trial&&r.mode==='V2_INTEGRAL_SAFE'&&r.status==='GEOMETRY_CANDIDATE'))process.exitCode=1;
