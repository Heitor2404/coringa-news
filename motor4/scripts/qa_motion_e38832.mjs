import {bundle} from '@remotion/bundler';
import {selectComposition,renderStill,renderMedia} from '@remotion/renderer';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e38832');mkdirSync(root,{recursive:true});
const props=JSON.parse(readFileSync('../benchmarks/e3883/props.json','utf8'));
const out={publish:false,voice:false,actual_app_ui_verified:false,visual_approval:'PENDING',rows:[],errors:[]};
const save=()=>writeFileSync(resolve(root,'proof.json'),JSON.stringify(out,null,2));
try{
 const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
 const browserExecutable=process.env.REMOTION_CHROME;
 const probe={...props,documentary_text_probe:true};
 const comp=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps:probe,browserExecutable});
 for(const s of props.shots){
  const logs=[];
  await renderStill({serveUrl,composition:comp,inputProps:probe,browserExecutable,frame:Math.round((s.start+3)*comp.fps),output:resolve(root,s.id+'.png'),logLevel:'info',onBrowserLog:l=>{const v=String(l.text||''),i=v.indexOf('E3883_CHART ');if(i>=0)try{logs.push(JSON.parse(v.slice(i+12)))}catch{out.errors.push('PARSE '+s.id)}}});
  const row=logs.at(-1);if(!row||!row.fit||row.title!==s.documentary_chart_trial.title||row.ink.h<350||row.ink.w<440||row.rect[1]!==505||row.contentHeight>665)out.errors.push('FIT '+s.id);
  out.rows.push({id:s.id,measurement:row,source:s.documentary_chart_trial.source,fixture:s.documentary_chart_trial.fixture});save();
 }
 await renderMedia({serveUrl,composition:comp,inputProps:probe,browserExecutable,codec:'h264',outputLocation:resolve(root,'motion-library.mp4'),scale:.5,concurrency:2,logLevel:'error'});
}catch(e){out.errors.push(String(e))}
save();console.log('E3883',out.rows.map(r=>[r.id,r.measurement?.kind,r.measurement?.fit]),out.errors);
if(out.rows.length!==6||out.errors.length)process.exitCode=1;
