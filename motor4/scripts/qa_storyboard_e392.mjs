import {bundle} from '@remotion/bundler';import {selectComposition,renderStill} from '@remotion/renderer';import {readFileSync,writeFileSync} from 'node:fs';import {resolve} from 'node:path';
const root=resolve('../stage_documental/e392'),p=JSON.parse(readFileSync(resolve(root,'board.json'),'utf8')),out={publish:false,rows:[],errors:[],visual_approval:'PENDING'};
try{const serveUrl=await bundle({entryPoint:resolve('remotion/src/e392-index.tsx'),publicDir:resolve('remotion/public')});const browserExecutable=process.env.REMOTION_CHROME;
for(const board of p.boards){const inputProps={board,private_review_only:true,probe:true},composition=await selectComposition({serveUrl,id:'StoryboardE392',inputProps,browserExecutable});const logs=[];
await renderStill({serveUrl,composition,inputProps,browserExecutable,frame:0,output:resolve(root,'board-'+board.index+'.png'),logLevel:'info',onBrowserLog:l=>{const v=String(l.text||''),prefix='E392_BOARD ',i=v.indexOf(prefix);if(i>=0)try{logs.push(JSON.parse(v.slice(i+prefix.length)))}catch{out.errors.push('PARSE')}}});
const row=logs.at(-1);if(!row?.fit||row.index!==board.index||row.caption!==board.caption.map(w=>w.w).join(' ')||row.collisions!==false||JSON.stringify(row.state)!==JSON.stringify(board.state))out.errors.push('BOARD '+board.index);out.rows.push(row||{index:board.index,missing:true});}}
catch(e){out.errors.push(String(e))}
writeFileSync(resolve(root,'comparison.json'),JSON.stringify(out,null,2));if(out.errors.length||out.rows.length!==4)process.exitCode=1;
