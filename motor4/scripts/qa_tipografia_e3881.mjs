import {bundle} from '@remotion/bundler';
import {selectComposition,renderStill,renderMedia} from '@remotion/renderer';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e3881');
const out={publish:false,actual_app_ui_verified:false,semantic_approval:false,motion:[],errors:[]};
const save=()=>writeFileSync(resolve(root,'comparison.json'),JSON.stringify(out,null,2));
const profiles=JSON.parse(readFileSync(resolve('../src/v4/formatos/plataformas.json'),'utf8'));
function risks(rect,names){return names.filter(n=>{const p=profiles.perfis[n],r=p.direita;return rect[0]<p.esquerda||rect[1]<p.topo||rect[3]>1920-p.base||(rect[2]>1080-r.largura&&rect[3]>r.de_y&&rect[1]<r.ate_y)})}
try{
 const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
 const browserExecutable=process.env.REMOTION_CHROME;
 for(const id of ['c3-2','c6-1']){
  const props=JSON.parse(readFileSync(resolve(root,id+'.json'),'utf8')),s=props.shots[0],f=s.documentary_reported_fact;
  const composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps:props,browserExecutable});
  const probe={...props,documentary_text_probe:true},logs=[],stats=[];
  const at=Math.min(s.end-.1,f.at+.55);
  const log=l=>{const v=String(l.text||'');for(const [prefix,a] of [['E290_TEXT ',logs],['E3881_STAT ',stats]]){const i=v.indexOf(prefix);if(i>=0)try{a.push(JSON.parse(v.slice(i+prefix.length)))}catch{out.errors.push('PARSE '+id)}}};
  await renderStill({serveUrl,composition,inputProps:probe,browserExecutable,frame:Math.round(at*composition.fps),output:resolve(root,'motion-'+id+'.png'),logLevel:'info',onBrowserLog:log});
  const sub=logs.filter(x=>x.shot===id&&x.role==='subtitle').at(-1),stat=stats.at(-1);
  if(!sub||sub.safeTrialStatus!=='E3881_TAIWAN_FACT_PENDING'||!sub.fits||sub.evidenceCollision||sub.rect[0]!==66||sub.rect[1]!==1190||sub.font>60||logs.some(x=>x.role==='source')||!stat?.taiwan||!stat.fit||stat.rect[0]!==66||stat.value!==f.value||stat.scope!==f.scope)out.errors.push('TAIWAN_CONTRACT '+id);
  // Before the speech anchor there must be no number or old source line.
  const preLogs=logs.length,preStats=stats.length;
  await renderStill({serveUrl,composition,inputProps:probe,browserExecutable,frame:0,output:resolve(root,'motion-'+id+'-before.png'),logLevel:'info',onBrowserLog:log});
  if(logs.slice(preLogs).some(x=>x.role==='source')||stats.length!==preStats)out.errors.push('BEFORE_ANCHOR '+id);
  out.motion.push({id,value:f.value,scope:f.scope,at:f.at,hold:s.end-f.at,subtitle:sub,stat,uiRisks:stat?risks(stat.rect,profiles.ativos_seguros):[],visual_review:'PENDING'});save();
  await renderMedia({serveUrl,composition,inputProps:props,browserExecutable,codec:'h264',outputLocation:resolve(root,'motion-'+id+'.mp4'),scale:.5,concurrency:2,logLevel:'error'});
 }
}catch(e){out.errors.push(String(e))}
save();console.log('E3881',out.motion.map(x=>[x.id,x.stat?.fit,x.subtitle?.safeTrialStatus]),out.errors);
if(out.motion.length!==2||out.errors.length)process.exitCode=1;
