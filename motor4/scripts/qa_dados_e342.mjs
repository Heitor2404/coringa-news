import {bundle} from '@remotion/bundler';
import {selectComposition,renderStill} from '@remotion/renderer';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e342'),read=n=>JSON.parse(readFileSync(resolve(root,n),'utf8'));
const proof=read('proof.json'),result={publish:false,semantic_approval:false,frames:[],errors:[]};
const save=()=>writeFileSync(resolve(root,'comparison.json'),JSON.stringify(result,null,2));
try{
 const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
 const browserExecutable=process.env.REMOTION_CHROME;
 for(const kind of ['baseline','candidate']){
  const inputProps=read(kind+'.json'),composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps,browserExecutable});
  for(const r of proof.records){
   const t=r.at_s+.6,logs=[],name=r.shot+'-'+kind+'.png';
   await renderStill({serveUrl,composition,inputProps,browserExecutable,frame:Math.round(t*composition.fps),output:resolve(root,name),logLevel:'info',
    onBrowserLog:l=>{let s=String(l.text||''),i=s.indexOf('E290_TEXT ');if(i>=0){try{logs.push(JSON.parse(s.slice(i+10)))}catch{result.errors.push('PARSE')}}}});
   const rows=['section','source','subtitle'].map(role=>logs.filter(x=>x.role===role).at(-1)).filter(Boolean);
   if(kind==='candidate'){
    const section=rows.find(x=>x.role==='section'),source=rows.find(x=>x.role==='source');
    if(rows.length!==3||section?.text!==r.value||section?.font<38||section?.safeTrialStatus!=='E342_REPORTED_FACT_LANE'||!source?.text.includes(r.scope)||rows.some(x=>!x.fits||x.evidenceCollision||x.unknownEvidenceOverlay||x.actual[0]<149||x.actual[1]<299||x.actual[2]>771||x.actual[3]>1241))result.errors.push('FACT OR LAYOUT '+name);
   }
   result.frames.push({name,t,kind,shot:r.shot,measurements:rows});save();
  }
 }
}catch(e){result.errors.push(String(e))}
save();console.log('E342',result.frames.map(x=>[x.name,x.measurements.map(y=>[y.role,y.text,y.font,y.fits])]),result.errors);
if(result.errors.length||result.frames.length!==4)process.exitCode=1;
