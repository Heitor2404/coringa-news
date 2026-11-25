// E290 private full-resolution browser measurements; no new media or external AI.
import {bundle} from '@remotion/bundler';
import {selectComposition,renderStill} from '@remotion/renderer';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';

const root=resolve('../stage_documental/e286');
const props=JSON.parse(readFileSync(resolve(root,'props.json'),'utf8'));
props.documentary_text_probe=true;
// Same media and credit as failed E290; additionally exercise a long section.
props.shots.find(s=>s.id==='video_vertical_nasa').lead='REGISTRO DOCUMENTAL DO TELESCÓPIO ESPACIAL';
// Real source bytes, synthetic boxes/positions: these test geometry, NOT
// claims about the ship's actual action or an approved crop.
const original=props.shots[0];
const cases=[['4:5',.39,[.30,.32,.69,.54]],['1:1',.49,[.255,.35,.745,.52]],
  ['9:16',.20,[.40,.35,.60,.55]],['4:5-collision',.39,[.30,.05,.69,.95]]];
for(const [mode,width,bbox] of cases){
  const i=props.shots.length,start=i*3;
  const s={...original,id:'qa-'+mode.replace(':','-'),start,end:start+3,
    video_context_layout:'recorte_relacional_seguro',documentary_viewport:mode.startsWith('4:5')?'4:5':mode==='1:1'?'1:1':undefined,
    framing_positions:[{at:0,position:[.5,.5]},{at:2.9,position:[.51,.5]}],
    documentary_roi_points:[{at:0,bbox},{at:2.9,bbox}]};
  props.shots.push(s);
  props.documentary_captions.push({start:start+.3,end:start+2.8,words:[{w:'TESTE'},{w:'GEOMÉTRICO',hl:true}]});
}
// Reuse the native 9:16 footage with synthetic validated-style ROIs:
 // one can keep the picture large, one conflicts with every text lane.
const native=props.shots.find(s=>s.id==='video_vertical_nasa');
for(const [id,bbox] of [['portrait-observed-free',[.15,.35,.85,.48]],['portrait-observed-conflict',[.05,.10,.95,.85]]]){
  const start=props.shots.length*3;
  props.shots.push({...native,id:'qa-'+id,start,end:start+3,video_context_layout:undefined,
    framing_positions:[{at:0,position:[.5,.5]},{at:2.9,position:[.5,.5]}],
    documentary_roi_points:[{at:0,bbox},{at:2.9,bbox}]});
  props.documentary_captions.push({start:start+.3,end:start+2.8,words:[{w:'TESTE'},{w:'VERTICAL',hl:true}]});
}
props.duracao=props.shots.length*3;
const longWords='O REGISTRO MOSTRA A CENA EM DETALHES'.split(' ');
props.documentary_captions=props.documentary_captions.flatMap((cap,i)=>[
  {...cap,end:props.shots[i].start+1.5},
  {start:props.shots[i].start+1.5,end:cap.end,words:longWords.map((w,j)=>({w,hl:j===2}))},
]);
const dest=resolve(root,'e290');mkdirSync(dest,{recursive:true});
const result={publish:false,visual_approval:'PENDING',narration:false,
  kind:'REAL_MEDIA_LAYOUT_PROBE_SYNTHETIC_CAPTIONS',background:'SIGNATURE_B_V1',resolution:[1080,1920],frames:[],errors:[]};
const save=()=>writeFileSync(resolve(dest,'medidas.json'),JSON.stringify(result,null,2));
try {
  const serveUrl=await bundle({entryPoint:resolve('remotion/src/index.ts'),publicDir:resolve('remotion/public')});
  const browserExecutable=process.env.REMOTION_CHROME;
  const composition=await selectComposition({serveUrl,id:'FilmeEditorial',inputProps:props,browserExecutable});
  if(composition.width!==1080||composition.height!==1920)throw new Error('E290 resolution');
  for(const shot of props.shots){
    for(const offset of [1,2]){
      const frame=Math.round((shot.start+offset)*composition.fps);
      const logs=[];
      const output=resolve(dest,shot.id+'-'+offset+'.png');
      await renderStill({serveUrl,composition,inputProps:props,browserExecutable,frame,output,logLevel:'info',
        onBrowserLog:log=>{
          const text=String(log.text||'');
          const index=text.indexOf('E290_TEXT ');
          if(index<0)return;
          try{logs.push(JSON.parse(text.slice(index+10)));}catch(error){result.errors.push('PARSE '+text);}
        }});
      const expectedCaption=props.documentary_captions.find(c=>frame/composition.fps>=c.start&&frame/composition.fps<c.end);
      const expected={section:shot.lead.toUpperCase(),source:(shot.evidence==='representative'?'Contexto · ':'')+(shot.source_display||shot.source),subtitle:expectedCaption?.words.map(w=>w.w).join(' ')};
      const rows=[];
      for(const role of ['section','subtitle','source']){
        const row=logs.filter(x=>x.shot===shot.id&&x.role===role&&x.text===expected[role]).at(-1);
        if(!row){result.errors.push('MISSING_MEASURE '+shot.id+' '+offset+' '+role);continue;}
        rows.push(row);
        const [x,y,r,b]=row.actual;
        if(!row.fits||x<119||y<299||r>771||b>1601||row.font<({section:22,subtitle:36,source:24}[role]))
          result.errors.push('OVERFLOW '+shot.id+' '+offset+' '+role);
        if(row.evidenceCollision)result.errors.push('EVIDENCE_COLLISION '+shot.id+' '+offset+' '+role);
        const [mx,my,mr,mb]=row.media;
        const hasGap=mx>.5||my>.5||mr<1079.5||mb<1919.5;
        if(row.signatureBackground!==(hasGap?'SIGNATURE_B_V1':null))
          result.errors.push('SIGNATURE_SCOPE '+shot.id+' '+offset+' '+role);
        if(shot.video_context_layout==='cena_integral'&&shot.source_dimensions[0]/shot.source_dimensions[1]>=1080/610&&row.actualOverlay)
          result.errors.push('PANORAMIC_OVERLAP '+shot.id+' '+offset+' '+role);
      }
      const modes=new Set(rows.map(x=>x.layout));
      if(modes.size!==1)result.errors.push('LAYOUT_MISMATCH '+shot.id);
      if(shot.id==='qa-portrait-observed-conflict'&&!modes.has('INTEGRAL_PROTECTED'))result.errors.push('FALLBACK_MISSING '+shot.id);
      if(shot.id==='qa-4-5-collision'&&!modes.has('CENTERED_INTEGRAL'))result.errors.push('LANDSCAPE_FALLBACK_MISSING '+shot.id);
      if(shot.source_dimensions[0]>shot.source_dimensions[1]){
        for(const row of rows){
          const [x,y,r,b]=row.media;
          if(Math.abs((y+b)/2-960)>.01||!row.layout.startsWith('CENTERED_')||row.rect[0]!==120)
            result.errors.push('CENTER_OR_ANCHOR '+shot.id+' '+row.role);
          if(row.centeredFit==='cover'&&(!row.layout.startsWith('CENTERED_CROP')||b-y!==810))
            result.errors.push('CROP_GEOMETRY '+shot.id);
        }
      }
      if(['video_vertical_nasa','foto_vertical_salto_angel'].includes(shot.id)){
        if(!modes.has('PORTRAIT_REVIEW')||rows.some(r=>r.roiStatus!=='UNKNOWN_REVIEW'))
          result.errors.push('NATIVE_PORTRAIT_DEFAULT '+shot.id);
        for(const row of rows){
          const [x,y,r,b]=row.media;
          if((r-x)*(b-y)<.90*1080*1920||!row.actualOverlay)
            result.errors.push('NATIVE_PORTRAIT_SHRUNK '+shot.id+' '+row.role);
          if(shot.id==='video_vertical_nasa'&&[x,y,r,b].join(',')!=='0,0,1080,1920')
            result.errors.push('NATIVE_9_16_NOT_FULL '+shot.id);
        }
      }
      if(shot.id==='qa-portrait-observed-free'&&(modes.has('INTEGRAL_PROTECTED')||rows.some(r=>r.roiStatus!=='OBSERVED'||r.media.join(',')!=='0,0,1080,1920')))
        result.errors.push('OBSERVED_PORTRAIT_SHRUNK '+shot.id);
      if(['qa-4-5','qa-1-1','qa-9-16'].includes(shot.id)&&!modes.has('CENTERED_CROP_OBSERVED'))result.errors.push('UNNECESSARY_FALLBACK '+shot.id);
      result.frames.push({shot:shot.id,frame,offset,dimensions:shot.source_dimensions,measurements:rows});
      save();
    }
  }
} catch(error){result.errors.push(String(error));}
save();
console.log('E290 measured frames',result.frames.length,'errors',result.errors);
if(result.frames.length!==props.shots.length*2||result.errors.length)process.exitCode=1;
