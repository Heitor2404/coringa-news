import {bundle} from '@remotion/bundler';
import {selectComposition,renderMedia} from '@remotion/renderer';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e345'),read=n=>JSON.parse(readFileSync(resolve(root,n),'utf8'));
const proof=read('proof.json'),inputProps=read('props-candidate.json');
const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
const browserExecutable=process.env.REMOTION_CHROME;
const composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps,browserExecutable});
if(composition.durationInFrames!==proof.total_frames||composition.fps!==30)throw Error('E345-COMPOSITION');
for(const [i,p] of proof.parts.entries()){
 if(!p.changed)continue;
 await renderMedia({serveUrl,composition,inputProps,browserExecutable,codec:'h264',crf:20,scale:.5,concurrency:4,muted:true,frameRange:[p.start,p.end-1],outputLocation:resolve(root,'fragment-'+i+'.mp4'),logLevel:'error'});
 console.log('E345_FRAGMENT',i,p.start,p.end,p.shots);
}
