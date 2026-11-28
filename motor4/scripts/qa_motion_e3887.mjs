import {bundle} from '@remotion/bundler';
import {selectComposition,renderStill,renderMedia} from '@remotion/renderer';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e3887');
const out={publish:false,actual_app_ui_verified:false,visual_approval:'PENDING',rows:[],errors:[]};
const save=()=>writeFileSync(resolve(root,'comparison.json'),JSON.stringify(out,null,2));
try{
 const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
 const browserExecutable=process.env.REMOTION_CHROME;
 const p=JSON.parse(readFileSync(resolve(root,'pair.json'),'utf8'));
 const input={...p,documentary_text_probe:true};
 const composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps:input,browserExecutable});
 const fps=composition.fps;
 for(const s of p.shots){
  const a=s.start+s.documentary_chart_anchor.at,id=s.id,measurements=[];
  const frames=new Set([Math.round(s.start*fps),Math.ceil(a*fps)-1,Math.ceil(a*fps),Math.ceil((a+.06)*fps),Math.ceil((a+.18)*fps),Math.ceil((a+.30)*fps),Math.ceil((a+.85)*fps),Math.ceil((a+1.25)*fps),Math.ceil(s.end*fps)-1,...p.documentary_captions.filter(g=>g.start>=s.start&&g.end<=s.end).map(g=>Math.ceil((g.start+g.end)/2*fps))]);
  for(const frame of [...frames].filter(x=>x/fps>=s.start&&x/fps<s.end&&x<composition.durationInFrames).sort((a,b)=>a-b)){
   const logs=[],subs=[],contexts=[];
   const log=l=>{const v=String(l.text||'');for(const [prefix,list] of [['E3883_CHART ',logs],['E290_TEXT ',subs],['E38851_CONTEXT ',contexts]]){const i=v.indexOf(prefix);if(i>=0)try{list.push(JSON.parse(v.slice(i+prefix.length)))}catch{out.errors.push('PARSE '+id)}}};
   await renderStill({serveUrl,composition,inputProps:input,browserExecutable,frame,output:resolve(root,'motion-'+id+'-'+frame+'.png'),logLevel:'info',onBrowserLog:log});
   const time=frame/fps,elapsed=time-a,active=elapsed>.12,fade=Math.max(0,Math.min(1,(elapsed-.12)/.12)),contextOpacity=Math.max(0,Math.min(1,1-elapsed/.12)),expected=p.documentary_captions.find(g=>g.start<=time&&time<g.end);
   const row=logs.at(-1),sub=subs.at(-1),role=s.documentary_chart_relation.role;
   if(active?(!row?.fit||row.title!==s.documentary_chart_trial.title||Math.abs(row.opacity-fade)>1e-6||row.relation!==role):Boolean(row))out.errors.push('CHART '+id+' '+frame);
   if(contextOpacity<=0?contexts.length>0:!contexts.some(c=>c.asset===s.documentary_chart_context.asset&&c.shot===id&&Math.abs(c.opacity-contextOpacity)<1e-6))out.errors.push('CONTEXT '+id+' '+frame);
   if(expected?(!sub?.fits||sub.text!==expected.words.map(w=>w.w).join(' ')):Boolean(sub))out.errors.push('CAPTION '+id+' '+frame);
   if(active&&row){const total=row.boxes.find(b=>b.role==='total'),part=row.boxes.find(b=>b.role==='part');const ratio=s.documentary_chart_relation.part.values[0].value/s.documentary_chart_relation.total.values[0].value;
    if(!total||total.w!==450||total.h!==450||total.x!==12||total.y!==32||(role==='total'?Boolean(part):!part||Math.abs(part.w*part.h/(total.w*total.h)-ratio)>1e-8||part.x!==total.x||Math.abs(part.y+part.h-total.y-total.h)>1e-6))out.errors.push('AREA_GEOMETRY '+id+' '+frame);
    if(role==='total'&&row.rows.some(r=>/TERRA NOVA|3,54|10%/.test(r.text)))out.errors.push('EARLY_PART '+id+' '+frame);
    if(role==='part'){const show=elapsed/Math.min(1.5,s.end-s.start-s.documentary_chart_anchor.at)>=.68;const pct=row.rows.some(r=>/10%/.test(r.text));if(show!==pct)out.errors.push('PERCENT_TIMING '+id+' '+frame);}
   }
   if(contexts.length&&logs.length)out.errors.push('OVERLAP '+id+' '+frame);
   measurements.push({frame,time,active,fade,contextOpacity,row,subtitle:sub,context:contexts.at(-1)});
  }
  if(!measurements.some(m=>m.fade>0&&m.fade<1)||!measurements.some(m=>m.fade===1)||!measurements.some(m=>m.contextOpacity>0&&m.contextOpacity<1)||!measurements.some(m=>!m.active))out.errors.push('SAMPLE_COVERAGE '+id);
  out.rows.push({id,at:a,measurements,voice:true,source:s.documentary_chart_trial.source});save();
 }
 await renderMedia({serveUrl,composition,inputProps:p,browserExecutable,codec:'h264',outputLocation:resolve(root,'motion-area-continuity.mp4'),scale:.5,concurrency:2,logLevel:'error'});
}catch(e){out.errors.push(String(e))}
save();console.log('E3887',out.rows.map(r=>[r.id,r.measurements.length]),out.errors);
if(out.rows.length!==2||out.errors.length)process.exitCode=1;
