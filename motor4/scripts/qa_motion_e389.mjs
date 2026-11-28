import {bundle} from '@remotion/bundler';
import {selectComposition,renderStill,renderMedia} from '@remotion/renderer';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e389');
const out={publish:false,visual_approval:'PENDING',rows:[],errors:[]};
const save=()=>writeFileSync(resolve(root,'comparison.json'),JSON.stringify(out,null,2));
try{
 const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
 const browserExecutable=process.env.REMOTION_CHROME;
 const p=JSON.parse(readFileSync(resolve(root,'variant.json'),'utf8')),base=JSON.parse(readFileSync(resolve(root,'baseline.json'),'utf8'));
 if(JSON.stringify(p.shots.slice(1,3))!==JSON.stringify(base.shots.slice(1,3))||JSON.stringify(p.documentary_captions)!==JSON.stringify(base.documentary_captions)||p.scene_narration_asset!==base.scene_narration_asset)throw Error('E389-PRESERVE');
 const input={...p,documentary_text_probe:true};
 const composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps:input,browserExecutable});
 const fps=composition.fps;
 for(const s of p.shots){
  const st=s.documentary_causal_stage,measurements=[];
  const frames=new Set([Math.ceil(s.start*fps),Math.ceil((s.start+s.end)/2*fps),Math.ceil(s.end*fps)-1,...(st?.highlights||[]).flatMap(h=>[Math.ceil((s.start+h.at)*fps)-1,Math.ceil((s.start+h.at+.25)*fps)])]);
  for(const frame of [...frames].filter(x=>x/fps>=s.start&&x/fps<s.end&&x<composition.durationInFrames).sort((a,b)=>a-b)){
   const stages=[],subs=[];
   const log=l=>{const v=String(l.text||'');for(const [prefix,list] of [['E389_STAGE ',stages],['E290_TEXT ',subs]]){const i=v.indexOf(prefix);if(i>=0)try{list.push(JSON.parse(v.slice(i+prefix.length)))}catch{out.errors.push('PARSE '+s.id)}}};
   await renderStill({serveUrl,composition,inputProps:input,browserExecutable,frame,output:resolve(root,'motion-'+s.id+'-'+frame+'.png'),logLevel:'info',onBrowserLog:log});
   const time=frame/fps,expected=p.documentary_captions.find(g=>g.start<=time&&time<g.end),row=stages.at(-1),sub=subs.filter(x=>x.role==='subtitle').at(-1);
   if(st){const active=st.highlights.filter(h=>time-s.start>=h.at).at(-1)?.label||null;if(!row?.fit||row.stage!==st.stage||row.active!==active||JSON.stringify(row.panel)!==JSON.stringify(st.panel)||row.geometry.y+row.geometry.height>1092.001)out.errors.push('STAGE '+s.id+' '+frame);}
   else if(stages.length)out.errors.push('RECORD '+s.id+' '+frame);
   if(expected&&(!sub?.fits||sub.text!==expected.words.map(w=>w.w).join(' ')))out.errors.push('CAPTION '+s.id+' '+frame);
   measurements.push({frame,time,row,subtitle:sub,record:!st});
  }
  out.rows.push({id:s.id,measurements});save();
 }
 await renderMedia({serveUrl,composition,inputProps:p,browserExecutable,codec:'h264',outputLocation:resolve(root,'motion-causal-sequence.mp4'),scale:.5,concurrency:2,logLevel:'error'});
}catch(e){out.errors.push(String(e))}
save();console.log('E389',out.rows.map(r=>[r.id,r.measurements.length]),out.errors);
if(out.rows.length!==4||out.errors.length)process.exitCode=1;
