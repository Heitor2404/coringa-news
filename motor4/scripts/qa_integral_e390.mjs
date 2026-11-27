import {bundle} from '@remotion/bundler';
import {selectComposition,renderMedia,renderStill} from '@remotion/renderer';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e390'),read=n=>JSON.parse(readFileSync(resolve(root,n),'utf8'));
const p=read('props-current.json'),proof=read('consolidation.json'),out={publish:false,shots:[],errors:[],actual_app_ui_verified:false};
const save=()=>writeFileSync(resolve(root,'review.json'),JSON.stringify(out,null,2));
try{
 const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
 const browserExecutable=process.env.REMOTION_CHROME;
 const input={...p,documentary_text_probe:true};
 const composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps:input,browserExecutable});
 if(composition.durationInFrames!==2492||composition.fps!==30)throw Error('E390-TIMELINE');
 for(const s of p.shots){
  const route=proof.routes.find(r=>r.id===s.id).route,rows=[];
  const a=s.documentary_chart_anchor?.at;
  const frames=new Set([Math.ceil((s.start+s.end)/2*30)]);
  if(a!==undefined){frames.add(Math.ceil((s.start+a+.55)*30));frames.add(Math.ceil(s.end*30)-1);}
  for(const frame of frames){
   const logs=[],charts=[];
   await renderStill({serveUrl,composition,inputProps:input,browserExecutable,frame,output:resolve(root,'qa-'+s.id+'-'+frame+'.png'),logLevel:'info',onBrowserLog:l=>{const v=String(l.text||'');for(const [prefix,dest] of [['E290_TEXT ',logs],['E3883_CHART ',charts]]){const i=v.indexOf(prefix);if(i>=0)try{dest.push(JSON.parse(v.slice(i+prefix.length)))}catch{out.errors.push('PARSE '+s.id)}}}});
   const t=frame/30,g=p.documentary_captions.find(g=>g.start<=t&&t<g.end),sub=logs.filter(l=>l.role==='subtitle').at(-1),chart=charts.at(-1);
   if(s.type!=='atlas_map'&&g&&(!sub?.fits||sub.text!==g.words.map(w=>w.w).join(' ')))out.errors.push('SUBTITLE '+s.id+' '+frame);
   if(route==='TAIWAN_CURRENT_OVERLAY'&&g&&sub?.safeTrialStatus!=='E388_TAIWAN_OVERLAY_PENDING')out.errors.push('OLD_OR_BLOCKED_OVERLAY '+s.id);
   if(route==='APPROVED_NARRATED_GRAPH'&&t-s.start>=a+.25&&!chart?.fit)out.errors.push('CHART '+s.id+' '+frame);
   if(logs.some(l=>!l.fits||l.evidenceCollision))out.errors.push('TEXT_OR_EVIDENCE '+s.id+' '+frame);
   rows.push({frame,t,subtitle:sub,chart,route});
  }
  out.shots.push({id:s.id,route,rows});save();
 }
 if(out.errors.length)throw Error(out.errors.join(';'));
 await renderMedia({serveUrl,composition,inputProps:p,browserExecutable,codec:'h264',crf:20,scale:.5,concurrency:4,muted:true,outputLocation:resolve(root,'current-render.mp4'),logLevel:'error'});
}catch(e){out.errors.push(String(e))}
save();if(out.errors.length||out.shots.length!==24)process.exitCode=1;
