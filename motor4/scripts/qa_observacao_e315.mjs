import {bundle} from '@remotion/bundler';
import {selectComposition,renderStill} from '@remotion/renderer';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e315');
const props=JSON.parse(readFileSync(resolve(root,'props.json'),'utf8'));
props.documentary_text_probe=true;
const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
const browserExecutable=process.env.REMOTION_CHROME;
const composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps:props,browserExecutable});
const rows=[];
for(const [name,frame,expected] of [['before',30,'ATIVIDADE DA FISSURA'],['after',75,'FRAGMENTOS PROJETADOS']]){
  const logs=[];
  await renderStill({serveUrl,composition,inputProps:props,browserExecutable,frame,output:resolve(root,name+'.png'),logLevel:'info',
    onBrowserLog:log=>{const t=String(log.text||'');const i=t.indexOf('E290_TEXT ');if(i>=0)logs.push(JSON.parse(t.slice(i+10)));}});
  const row=logs.filter(x=>x.role==='section'&&x.text===expected).at(-1);
  if(!row||!row.fits||row.evidenceCollision)throw new Error('E315 text '+JSON.stringify(row));
  rows.push(row);
}
writeFileSync(resolve(root,'measures.json'),JSON.stringify({publish:false,rows},null,2));
