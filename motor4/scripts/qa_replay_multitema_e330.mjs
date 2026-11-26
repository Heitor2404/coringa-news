import {bundle} from '@remotion/bundler';
import {selectComposition,renderStill} from '@remotion/renderer';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e330'),prep=JSON.parse(readFileSync(resolve(root,'replay.json'),'utf8'));
const out={publish:false,semantic_approval:false,actual_app_ui_verified:false,frames:[],errors:[]};
const save=()=>writeFileSync(resolve(root,'frames.json'),JSON.stringify(out,null,2));
try{
 const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
 const browserExecutable=process.env.REMOTION_CHROME;
 for(const r of prep.records.filter(r=>r.status==='READY_PRIVATE_FRAGMENT')){
  const props=JSON.parse(readFileSync(resolve(root,r.id,'props.json'),'utf8'));
  const composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps:props,browserExecutable});
  for(const t of [.8,2.7]){
   const logs=[];const name=r.id+'-'+t+'.png';
   await renderStill({serveUrl,composition,inputProps:props,browserExecutable,frame:Math.round(t*composition.fps),output:resolve(root,name),logLevel:'info',
    onBrowserLog:log=>{const text=String(log.text||'');const i=text.indexOf('E290_TEXT ');if(i>=0){try{logs.push(JSON.parse(text.slice(i+10)))}catch{out.errors.push('PARSE')}}}});
   const rows=['section','subtitle','source'].map(role=>logs.filter(x=>x.role===role).at(-1));
   if(rows.some(r=>!r)){out.errors.push('MISSING '+name);continue;}
   out.frames.push({id:r.id,t,name,measurements:rows,known_collision:rows.some(x=>x.evidenceCollision),unknown_overlay:rows.some(x=>x.unknownEvidenceOverlay),text_fit:rows.every(x=>x.fits)});
   save();
  }
 }
}catch(e){out.errors.push(String(e))}
save();
if(prep.records.some(r=>r.status!=='READY_PRIVATE_FRAGMENT')||out.frames.length!==6||out.errors.length)process.exitCode=1;
