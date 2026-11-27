import {bundle} from '@remotion/bundler';
import {selectComposition,renderStill,renderMedia} from '@remotion/renderer';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e387');
const input=name=>JSON.parse(readFileSync(resolve(root,name+'.json'),'utf8'));
const out={publish:false,actual_app_ui_verified:false,semantic_approval:false,frames:[],errors:[]};
const save=()=>writeFileSync(resolve(root,'comparison.json'),JSON.stringify(out,null,2));
const profiles=JSON.parse(readFileSync(resolve('../src/v4/formatos/plataformas.json'),'utf8'));
function risks(rect,names){
 return names.filter(n=>{const p=profiles.perfis[n],r=p.direita;return rect[0]<p.esquerda||rect[1]<p.topo||rect[3]>1920-p.base||(rect[2]>1080-r.largura&&rect[3]>r.de_y&&rect[1]<r.ate_y)});
}
try{
 const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
 const browserExecutable=process.env.REMOTION_CHROME;
 for(const name of ['fixtures','narrated']){
  const p=input(name);
  for(const trial of [false,true]){
   const props={...p,documentary_text_probe:true,shots:p.shots.map(s=>({...s,documentary_taiwan_typography_trial:true,documentary_clean_credit:trial?s.documentary_clean_credit:undefined}))};
   const composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps:props,browserExecutable});
   for(const s of props.shots){
    const g=props.documentary_captions.find(g=>g.start<s.end&&g.end>s.start);
    const t=(Math.max(s.start,g.start)+Math.min(s.end,g.end))/2;
    const logs=[],file=s.id+(trial?'-clean':'-baseline')+'.png';
    await renderStill({serveUrl,composition,inputProps:props,browserExecutable,frame:Math.round(t*composition.fps),output:resolve(root,file),logLevel:'info',
     onBrowserLog:log=>{const v=String(log.text||''),i=v.indexOf('E290_TEXT ');if(i>=0)try{logs.push(JSON.parse(v.slice(i+10)))}catch{out.errors.push('PARSE')}}});
    const rows=logs.filter(x=>x.shot===s.id).filter((x,i,a)=>a.findLastIndex(z=>z.role===x.role)===i);
    const sub=rows.find(x=>x.role==='subtitle'),source=rows.find(x=>x.role==='source');
    if(!sub||(!trial&&!source)){out.errors.push('MISSING '+file);continue;}
    const base=out.frames.find(x=>x.id===s.id&&!x.trial);
    const active=sub.safeTrialStatus==='E387_TAIWAN_CLEAN_PENDING';
    if(trial&&base&&s.source_dimensions[0]<=s.source_dimensions[1]&&JSON.stringify(base.media)!==JSON.stringify(sub.media))out.errors.push('PORTRAIT_CHANGED '+file);
    if(trial&&(!active||source||!rows.every(x=>x.fits&&!x.evidenceCollision)||sub.rect[1]<1100||(s.source_dimensions[0]>s.source_dimensions[1]&&(sub.centeredFit!=='contain'||sub.media[3]>sub.rect[1]-10))))out.errors.push('CLEAN_TEXT_OR_ROI '+file);
    out.frames.push({id:s.id,trial,file,t,active,mode:sub.safeTrialStatus,media:sub.media,measurements:rows.map(x=>({...x,legacyUiRisk:risks(x.painted,profiles.ativos),conservativeUiRisk:risks(x.painted,profiles.ativos_seguros)}))});save();
   }
   if(name==='narrated'){
    await renderMedia({serveUrl,composition,inputProps:{...props,documentary_text_probe:false},browserExecutable,codec:'h264',outputLocation:resolve(root,trial?'narrated-clean.mp4':'narrated-baseline.mp4'),scale:.5,concurrency:2,logLevel:'error'});
   }
  }
 }
}catch(e){out.errors.push(String(e))}
save();console.log('E387',out.frames.map(f=>[f.id,f.trial,f.mode]),out.errors);
if(out.frames.length!==10||out.errors.length||!out.frames.some(f=>f.trial&&f.active&&f.id==='c3-1')||!out.frames.some(f=>f.trial&&f.active&&f.id==='video_vertical_nasa'))process.exitCode=1;
