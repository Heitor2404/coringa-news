import {bundle} from '@remotion/bundler';
import {selectComposition,renderMedia,renderStill} from '@remotion/renderer';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../stage_documental/e348'),read=n=>JSON.parse(readFileSync(resolve(root,n),'utf8'));
const proof=read('proof.json'),inputProps=read('props-candidate.json');
const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
const browserExecutable=process.env.REMOTION_CHROME;
const composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps,browserExecutable});
if(composition.durationInFrames!==proof.total_frames||composition.fps!==30)throw Error('E345-COMPOSITION');
const probeProps={...inputProps,documentary_text_probe:true};
const probeComposition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps:probeProps,browserExecutable});
const review={publish:false,semantic_approval:false,frames:[],errors:[]};
for(const r of proof.changes){
 const t=r.at_s+.4,logs=[],name=r.shot+'-panel.png',p=probeProps;
 await renderStill({serveUrl,composition:probeComposition,inputProps:p,browserExecutable,frame:Math.round(t*30),output:resolve(root,name),logLevel:'info',
  onBrowserLog:l=>{const s=String(l.text||''),i=s.indexOf('E290_TEXT ');if(i>=0){try{logs.push(JSON.parse(s.slice(i+10)))}catch{review.errors.push('PARSE')}}}});
 const rows=['section','source','subtitle'].map(role=>logs.filter(x=>x.shot===r.shot&&x.role===role).at(-1));
 if(rows.some(x=>!x)||rows[0]?.text!==r.label||!rows[1]?.text.includes('Recorte')||rows.some(x=>x&&(x.signatureBackground!=='BLACK_SOLID_V1'||!x.fits||x.evidenceCollision||x.unknownEvidenceOverlay||x.actual[0]<149||x.actual[1]<299||x.actual[2]>771||x.actual[3]>1241)))review.errors.push('PANEL '+name);
 review.frames.push({name,t,measurements:rows});
}
import {writeFileSync} from 'node:fs';
writeFileSync(resolve(root,'panel-review.json'),JSON.stringify(review,null,2));
if(review.errors.length)throw Error(review.errors.join(';'));

if(!process.argv.includes('--stills-only'))for(const [i,p] of proof.parts.entries()){
 if(!p.changed)continue;
 await renderMedia({serveUrl,composition,inputProps,browserExecutable,codec:'h264',crf:20,scale:.5,concurrency:4,muted:true,frameRange:[p.start,p.end-1],outputLocation:resolve(root,'fragment-'+i+'.mp4'),logLevel:'error'});
 console.log('E348_FRAGMENT',i,p.start,p.end,p.shots);
}

