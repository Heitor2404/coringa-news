import {bundle} from '@remotion/bundler';
import {selectComposition,renderStill,renderMedia} from '@remotion/renderer';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e38851');
const out={publish:false,actual_app_ui_verified:false,visual_approval:'PENDING',rows:[],errors:[]};
const save=()=>writeFileSync(resolve(root,'comparison.json'),JSON.stringify(out,null,2));
try{
 const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
 const browserExecutable=process.env.REMOTION_CHROME;
 for(const id of ['c6-0','c6-1']){
  const p=JSON.parse(readFileSync(resolve(root,id+'.json'),'utf8')),s=p.shots[0],a=s.documentary_chart_anchor.at;
  const input={...p,documentary_text_probe:true};
  const composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps:input,browserExecutable});
  const measurements=[];
  const frames=new Set([0,Math.max(0,Math.ceil(a*composition.fps)-1),Math.ceil((a+.6)*composition.fps),...p.documentary_captions.map(g=>Math.ceil((g.start+g.end)/2*composition.fps))]);
  for(const frame of [...frames].filter(x=>x<composition.durationInFrames).sort((a,b)=>a-b)){
   const logs=[],subs=[],contexts=[];
   const log=l=>{const v=String(l.text||'');for(const [prefix,list] of [['E3883_CHART ',logs],['E290_TEXT ',subs],['E38851_CONTEXT ',contexts]]){const i=v.indexOf(prefix);if(i>=0)try{list.push(JSON.parse(v.slice(i+prefix.length)))}catch{out.errors.push('PARSE '+id)}}};
   await renderStill({serveUrl,composition,inputProps:input,browserExecutable,frame,output:resolve(root,'motion-'+id+'-'+frame+'.png'),logLevel:'info',onBrowserLog:log});
   const time=frame/composition.fps,active=time>=a,expected=p.documentary_captions.find(g=>g.start<=time&&time<g.end);
   const row=logs.at(-1),sub=subs.at(-1);
   if(active?(!row?.fit||row.title!==s.documentary_chart_trial.title):Boolean(row))out.errors.push('CHART '+id+' '+frame);
   if(active?contexts.length>0:!contexts.some(c=>c.asset===s.documentary_chart_context.asset&&c.shot===id))out.errors.push('CONTEXT '+id+' '+frame);
   if(expected?(!sub?.fits||sub.text!==expected.words.map(w=>w.w).join(' ')||sub.safeTrialStatus!=='E3885_TAIWAN_CHART_PENDING'):Boolean(sub))out.errors.push('CAPTION '+id+' '+frame);
   measurements.push({frame,time,active,row,subtitle:sub,context:contexts.at(-1)});
  }
  out.rows.push({id,at:a,measurements,voice:true,source:s.documentary_chart_trial.source});save();
  await renderMedia({serveUrl,composition,inputProps:p,browserExecutable,codec:'h264',outputLocation:resolve(root,'motion-'+id+'.mp4'),scale:.5,concurrency:2,logLevel:'error'});
 }
}catch(e){out.errors.push(String(e))}
save();console.log('E3885',out.rows.map(r=>[r.id,r.measurements.length]),out.errors);
if(out.rows.length!==2||out.errors.length)process.exitCode=1;
