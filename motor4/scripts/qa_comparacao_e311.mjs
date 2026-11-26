import {bundle} from '@remotion/bundler';
import {selectComposition,renderStill} from '@remotion/renderer';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e311');
const props=JSON.parse(readFileSync(resolve(root,'props.json'),'utf8'));
props.documentary_text_probe=true;
const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
const browserExecutable=process.env.REMOTION_CHROME;
const composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps:props,browserExecutable});
const rows=[];
for(const shot of props.shots){
  const logs=[];
  await renderStill({serveUrl,composition,inputProps:props,browserExecutable,frame:Math.round((shot.start+1.2)*composition.fps),
    output:resolve(root,shot.id+'.png'),logLevel:'info',onBrowserLog:log=>{const t=String(log.text||'');const i=t.indexOf('E290_TEXT ');if(i>=0)logs.push(JSON.parse(t.slice(i+10)));}});
  const row=logs.filter(x=>x.shot===shot.id&&x.role==='section'&&x.text===shot.lead.toUpperCase()).at(-1);
  if(!row||!row.fits||row.evidenceCollision)throw new Error('E311 text '+JSON.stringify(row));
  rows.push(row);
}
writeFileSync(resolve(root,'comparison-measures.json'),JSON.stringify({publish:false,visual_approval:'PENDING',rows},null,2));
