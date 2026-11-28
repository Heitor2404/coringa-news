import React from 'react';
import {AbsoluteFill} from 'remotion';
import {ACutawayMaterial,ASurfaceGrain} from './AtlasAArtKit';
import {fitCaptionLines} from './CaptionFitE392';
import {morphPath} from './CausalTimelineE393';
import {detailAt,svgCamera} from './CinematicDirectorE395';
import {solidShift} from './EditorialMotionE394';
type Board={id:string;index:number;time:number;state:Record<string,string>;camera:{scale:number;tx:number;ty:number};focus:string[];caption:{w:string;hl:boolean}[]};
const gold='#E9B949',white='#F5F5F5';
// Original stylized cross sections: reviewed USGS A/B establish topology,
// not depths, volumes, fracture positions or a measured drainage path.
const pre='M36 267 L54 260 70 253 88 252 100 265 124 266 142 281 174 281 186 269 224 269 251 269 264 250 309 252 348 257 393 262 449 268';
const post='M36 267 L54 260 70 253 88 252 100 269 120 305 152 330 179 340 197 334 223 310 244 291 269 294 294 280 307 260 320 253 348 257 393 262 449 268';
const rock=(top:string)=>top+' L449 567 L431 580 Q280 592 36 576 Z';
const initialMagma='M187 373 C176 352 184 312 174 281 L180 281 C193 318 190 350 207 361 C239 368 263 361 288 382 L313 414 321 442 310 473 290 498 270 512 263 537 276 582 217 584 228 554 Q226 530 201 514 L174 491 147 459 140 432 152 402 174 383 Z';
const lossMagma='M198 483 L219 474 242 479 266 468 290 486 298 509 282 530 262 546 261 560 274 582 217 584 225 558 216 543 190 525 177 505 Z';
const finalMagma='M162 477 L182 465 210 452 236 462 251 474 271 466 294 486 294 507 273 531 261 549 261 562 274 582 217 584 226 560 216 541 187 522 169 500 Z';
const cavity='M100 269 L120 305 152 330 179 340 197 334 223 310 244 291 269 294 294 280 307 260 L296 349 274 388 250 441 236 462 210 452 182 465 162 477 140 436 121 383 106 327 Z';
const pieces=['M121 310 L151 334 177 344 170 392 186 431 167 448 147 409 132 365 Z','M181 344 L198 338 221 318 238 350 234 402 217 417 198 400 179 387 Z','M225 315 L245 295 267 299 290 284 278 333 257 361 241 381 239 352 Z','M191 415 L216 424 233 410 239 440 229 456 208 448 201 461 183 431 Z','M241 390 L263 369 273 391 259 424 240 446 232 427 Z'];
const titles=['ANTES DO COLAPSO','PERDA DE MAGMA','REBAIXAMENTO','APÓS O COLAPSO'];
export const CalderaCutawayE392:React.FC<{board:Board;private_review_only:boolean;probe?:boolean;visualRevision?:'E395';motion?:{progress:number[];time:number}}>=({board:b,private_review_only,probe,motion,visualRevision})=>{
 if(!private_review_only||!b||b.index<0||b.index>3||!Number.isInteger(b.index))throw Error('E392-PRIVATE');
 const reduced=b.state['reservoir.material']==='reduced',lowered=b.state['roof.position']==='lowered',final=b.state['crater.depth']==='deeper';
 if(reduced!==(b.index>0)||lowered!==(b.index>1)||final!==(b.index===3))throw Error('E392-STATE');
 const ref=React.useRef<SVGSVGElement>(null);
 const [drain,collapse,reveal]=motion?.progress??[reduced?1:0,lowered?1:0,final?1:0];
 const magma=collapse>0?morphPath(lossMagma,finalMagma,collapse,true,[217,584]):morphPath(initialMagma,lossMagma,drain,true,[217,584]);
 const moving=!!motion;
 const cinematic=visualRevision==='E395'&&moving;
 const detail=cinematic?detailAt(b.time,[
 {id:'reservoir',start:3.12,end:5.08,roi:{left:138,top:360,right:321,bottom:570}},
 {id:'roof',start:6.05,end:8.12,roi:{left:104,top:250,right:310,bottom:452}}
 ],{left:43,top:259,right:330,bottom:579},1.75):null;
 const activeCamera=detail?.camera??b.camera;
 const settled=!moving||[drain,collapse,reveal].every(p=>p===0||p===1);
 React.useLayoutEffect(()=>{if(!probe||!ref.current)return;const rows=Array.from(ref.current.querySelectorAll<SVGGraphicsElement>('[data-safe-text]')).filter(e=>!e.closest('[display="none"]')).map(e=>{const q=e.getBBox(),role=e.getAttribute('data-safe-text'),c=role==='label'&&moving?b.camera:{scale:1,tx:0,ty:0};const x=q.x*c.scale+c.tx,y=q.y*c.scale+c.ty,w=q.width*c.scale,h=q.height*c.scale;return {role,text:e.textContent,x,y,w,h,fit:x>=32&&x+w<=454&&y>=145&&y+h<=690}});const cap=rows.filter(r=>r.role==='caption').map(r=>r.text).join(' ');const labels=rows.filter(r=>r.role==='label');const collisions=rows.some((r,i)=>rows.slice(i+1).some(s=>r.x<s.x+s.w&&s.x<r.x+r.w&&r.y<s.y+s.h&&s.y<r.y+r.h));console.log('E392_BOARD '+JSON.stringify({index:b.index,state:b.state,focus:b.focus,rows,caption:cap,fit:rows.every(r=>r.fit)&&!collisions&&cap===b.caption.map(w=>w.w).join(' '),collisions,labels,progress:[drain,collapse,reveal],magma,top:ref.current.querySelector('[data-e393-top]')?.getAttribute('d'),blockShift:moving?solidShift(collapse,85):0,camera:b.camera,detail:detail?{id:detail.id,roi:detail.roi,camera:detail.camera}:null,solidBlocks:Array.from(ref.current.querySelectorAll('[data-solid-block]')).map(e=>({opacity:e.getAttribute('opacity'),transform:e.getAttribute('transform')}))}));},[b,probe,motion,visualRevision]);
 const text=(s:string,x:number,y:number,size:number,color=white,weight=700,role='title')=><text data-safe-text={role} x={x} y={y} fontSize={size} fill={color} fontWeight={weight}>{s}</text>;
 // Measure the actual typeface at the rendered size, not character count.
 // Leave a small margin for SVG glyph overhang; the existing bbox gate is unchanged.
 const ctx=typeof document==='undefined'?null:document.createElement('canvas').getContext('2d');
 if(ctx)ctx.font='900 29px Inter,Arial,sans-serif';
 const width=(s:string)=>ctx?ctx.measureText(s).width:s.length*29;
 const lines=fitCaptionLines(b.caption,width,410);
 const top=morphPath(pre,post,collapse,false),shape=rock(top);
 const strata=['#827360','#5C5146','#9F8669','#51443B','#71604F','#483B35','#866B53','#392F2B'];
 return <AbsoluteFill style={{background:'#000'}}>
 <svg ref={ref} viewBox="0 0 540 960" width="100%" height="100%" style={{fontFamily:'Inter,Arial,sans-serif'}}>
 <defs>
  <clipPath id="e395-stage"><rect x="32" y="237" width="422" height="356"/></clipPath>
  <clipPath id="rockclip"><path d={shape}/></clipPath>
  <clipPath id="magmaclip"><path d={magma}/></clipPath>
  <linearGradient id="wall" x1="0" x2=".3" y1="0" y2="1"><stop stopColor="#A28A70"/><stop offset=".34" stopColor="#766051"/><stop offset="1" stopColor="#302925"/></linearGradient>
  <linearGradient id="void" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#110E0D"/><stop offset="1" stopColor="#32221D"/></linearGradient>
  <radialGradient id="heat"><stop stopColor="#FFF1AD" stopOpacity={moving ? .30 : .92}/><stop offset=".35" stopColor="#FF9F45" stopOpacity={moving ? .33 : .68}/><stop offset="1" stopColor="#D9431E" stopOpacity="0"/></radialGradient>
 </defs>
 {text('CORINGA',33,163,14,white,800)}{text('EXPLICA',108,163,14,gold,800)}
 <rect x="33" y="173" width="70" height="2.5" fill={gold}/>
 {text(titles[b.index],33,207,27,white,900)}
 {text('USGS / HVO · CORTE ILUSTRATIVO SEM ESCALA',33,225,10.5,'#B9B9B9',600)}
 <g clipPath={cinematic?"url(#e395-stage)":undefined}><g transform={svgCamera(activeCamera)}><g id="e395-geology-art">
  <path d={shape} transform="translate(3 4)" fill="#29201C"/>
  <path d={shape} fill="url(#wall)" stroke="#987C64" strokeWidth="1.2"/>
  {cinematic&&<path d={shape} transform="translate(4 5)" fill="#27201B" stroke="#75634E" strokeWidth="1.2"/>}
  <g clipPath="url(#rockclip)">
   {strata.map((c,i)=>{const y=275+i*40;return <path key={i} d={`M30 ${y} L69 ${y-5} 109 ${y+7} 149 ${y+4} 187 ${y+18} 224 ${y+14} 270 ${y+3} 308 ${y-3} 354 ${y+6} 404 ${y+5} 455 ${y+14} L455 ${y+38} 404 ${y+29} 354 ${y+26} 308 ${y+21} 270 ${y+29} 224 ${y+41} 187 ${y+44} 149 ${y+30} 109 ${y+31} 69 ${y+20} 30 ${y+24} Z`} fill={cinematic?['#6C5C4B','#454747','#857053','#4F4541','#76614C','#45413E','#685744','#353331'][i]:c} stroke="#241D1A" strokeOpacity=".34" strokeWidth="1.3"/>;})}
   {Array.from({length:moving?160:65},(_,i)=>{const x=39+(i*97)%405,y=276+(i*53)%303;return <path key={i} d={`M${x} ${y} l${3+i%8} -${2+i%4} l${4+i%5} 2`} fill="none" stroke={i%2?'#E3C4A1':'#1B1614'} strokeOpacity={i%2?.19:.32} strokeWidth={moving ? .7 : 1.1}/>;})}
   {cinematic&&<ASurfaceGrain id="e395-rock" d={shape} kind="rock" opacity={.72}/>}
   {collapse>0&&<path opacity="1" d={morphPath("M100 269 L120 269 152 281 179 281 197 269 223 269 244 269 269 255 294 252 307 260 L296 270 274 275 250 280 236 285 210 286 182 287 162 289 140 284 121 279 106 275 Z",cavity,collapse,true,[100,269])} fill="url(#void)" stroke="#AE9278" strokeWidth="1.4"/>}
   {drain>0&&collapse<1&&<path opacity={1-collapse} d={initialMagma} fill="#211813" stroke="#CE9D6C" strokeDasharray="5 4" strokeWidth="1.2"/>}
   <ACutawayMaterial id="magma" d={magma} tone="hot" offset={2}/>{cinematic&&<ASurfaceGrain id="e395-magma" d={magma} kind="hot" opacity={.56}/>}
   <g clipPath="url(#magmaclip)"><ellipse cx={moving?216+5*Math.sin((motion?.time??0)*1.7):216} cy={421+72*drain} rx="89" ry="100" fill="url(#heat)"/>{Array.from({length:14},(_,i)=><path key={i} d={`M${145+(i*19)%134} ${397+(i*23)%164} q13 -6 25 2`} stroke="#FFE1A0" strokeOpacity=".19" strokeWidth="1.6" fill="none"/>)}</g>
   {collapse>0&&pieces.map((d,i)=><g key={i} data-solid-block="true" opacity="1" transform={`translate(0 ${moving?solidShift(collapse,85+i*5):0})`}><ACutawayMaterial id={'block-'+i} d={d} tone="rock" offset={cinematic?7:moving?4:2}/>{cinematic&&<ASurfaceGrain id={'e395-block-'+i} d={d} kind="rock" opacity={.64}/>}</g>)}
  </g>
  <path data-e393-top="true" d={top} stroke="#BCA386" strokeWidth="3" strokeLinejoin="round" fill="none"/>
  {b.index===2&&<g opacity={moving?Math.min(1,collapse*3):1} stroke={gold} strokeWidth="2.8" fill="none"><path d="M168 279 V323 m-6 -8 l6 8 6 -8"/><path d="M222 262 V302 m-6 -8 l6 8 6 -8"/></g>}
  {final&&<path opacity={reveal} d="M100 269 L142 281 174 281 186 269 224 269 251 269 264 250 307 253" stroke={gold} strokeWidth="1.5" strokeDasharray="5 4" fill="none" strokeOpacity=".85"/>}
 </g></g></g>
 {detail&&<g><rect x="329" y="244" width="123" height="111" rx="3" fill="#0D0D0D" stroke="#7F735A" strokeWidth=".7"/><g transform="translate(322 196) scale(.28)"><use href="#e395-geology-art"/><rect x={detail.roi.left} y={detail.roi.top} width={detail.roi.right-detail.roi.left} height={detail.roi.bottom-detail.roi.top} fill="none" stroke={gold} strokeWidth="4"/></g>{text('VISTA GERAL',336,349,10.5,gold,800,'detail')}{text('DETALHE',35,252,11,gold,800,'detail')}</g>}
 {/* Leader endpoints are selected separately for each reviewed state.
     The loss arrow denotes transfer out of the reservoir, NOT a mapped conduit. */}
 <g display={detail?'none':undefined} transform={moving?`translate(${b.camera.tx} ${b.camera.ty}) scale(${b.camera.scale})`:undefined}>
 {b.index===0&&<g><path d="M107 420 H127 L171 435" stroke={gold} fill="none" strokeWidth="1.4"/><circle cx="171" cy="435" r="2.5" fill={gold}/>{text('MAGMA',38,415,13,gold,800,'label')}</g>}
 {b.index===1&&settled&&<g><path d="M112 521 H151 L204 510" stroke={gold} fill="none" strokeWidth="1.4"/><circle cx="204" cy="510" r="2.5" fill={gold}/>{text('MAGMA',38,516,13,gold,800,'label')}<path d="M297 497 H355 m-9 -6 l9 6 -9 6" stroke={gold} fill="none" strokeWidth="2.2"/>{text('SAÍDA',362,493,13,gold,800,'label')}{text('DE MAGMA',362,508,11.5,gold,700,'label')}{text('SENTIDO SIMBÓLICO',315,526,8.5,'#D9B976',600,'label')}</g>}
 {b.index===2&&settled&&<g><path d="M110 374 H133 L160 371" stroke={gold} fill="none" strokeWidth="1.4"/><circle cx="160" cy="371" r="2.5" fill={gold}/>{text('BLOCOS',38,368,13,gold,800,'label')}</g>}
 {final&&settled&&<g><path d="M310 254 H338" stroke={gold} fill="none" strokeWidth="1.4"/>{text('NÍVEL',343,246,12,gold,800,'label')}{text('ANTERIOR',343,260,12,gold,800,'label')}<path d="M194 280 V331 m-5 -7 l5 7 5 -7" stroke={gold} strokeWidth="1.7" fill="none"/>{text('CRATERA',38,359,13,gold,800,'label')}<path d="M104 355 H123 L150 330" stroke={gold} fill="none" strokeWidth="1.4"/></g>}
 </g>
 {lines.filter(line=>line.length).map((line,i)=><text key={i} data-safe-text="caption" x="33" y={625+i*33} fontSize="29" fontWeight="900" fill={white}>{line.map((w,j)=><tspan key={j} fill={w.hl?gold:white}>{w.w}{j<line.length-1?' ':''}</tspan>)}</text>)}
 <text x="33" y="900" fill="#999" fontSize="10">{moving?'ANIMAÇÃO ILUSTRATIVA · NÃO PUBLICAR':'STORYBOARD PRIVADO · NÃO PUBLICAR'}</text>
 </svg></AbsoluteFill>;
};
