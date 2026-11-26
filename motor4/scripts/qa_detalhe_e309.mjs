import {bundle} from '@remotion/bundler';
import {selectComposition,renderStill} from '@remotion/renderer';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e286');
const props=JSON.parse(readFileSync(resolve(root,'detail-props.json'),'utf8'));
const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
const browserExecutable=process.env.REMOTION_CHROME;
const composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps:props,browserExecutable});
const result={publish:false,visual_approval:'PENDING',rows:[]};
for(const shot of props.shots){
  const logs=[];
  await renderStill({serveUrl,composition,inputProps:props,browserExecutable,
    frame:Math.round((shot.start+1.2)*composition.fps),output:resolve(root,'detail-'+shot.id+'.png'),logLevel:'info',
    onBrowserLog:log=>{const t=String(log.text||'');const i=t.indexOf('E309_DETAIL ');if(i>=0)logs.push(JSON.parse(t.slice(i+12)));}});
  const row=logs.filter(x=>x.shot===shot.id).at(-1);
  if(!row)throw new Error('E309 missing measure '+shot.id);
  result.rows.push(row);
}
writeFileSync(resolve(root,'detail-measures.json'),JSON.stringify(result,null,2));
if(result.rows[0].box!==null||!result.rows[1].box||result.rows[2].box!==null)throw new Error('E309 geometry '+JSON.stringify(result));
