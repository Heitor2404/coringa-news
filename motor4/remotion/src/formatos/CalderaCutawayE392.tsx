import React from 'react';
import {AbsoluteFill} from 'remotion';
import {ACutawayMaterial} from './AtlasAArtKit';
type Board={id:string;index:number;time:number;state:Record<string,string>;camera:{scale:number;tx:number;ty:number};focus:string[];caption:{w:string;hl:boolean}[]};
const gold='#E9B949',white='#F5F5F5';
const shape='M40 299 L67 287 88 285 108 277 133 277 149 265 176 267 196 279 216 283 240 282 263 275 291 269 312 265 335 274 356 270 382 283 411 287 445 299 L445 588 Q242 612 40 588 Z';
const upper='M40 299 L67 287 88 285 108 277 133 277 149 265 176 267 196 279 216 283 240 282 263 275 291 269 312 265 335 274 356 270 382 283 411 287 445 299';
const initialMagma='M242 391 C180 388 134 426 135 473 C132 517 170 549 210 562 Q226 570 219 590 L266 590 Q261 569 282 553 C334 526 357 474 337 433 C322 401 283 389 242 391 Z';
const smallMagma='M244 485 C212 469 166 486 164 516 C165 544 204 556 222 568 L219 590 L266 590 Q262 574 281 562 C322 543 331 515 306 495 Q278 473 244 485 Z';
const afterCut='M145 266 L169 289 187 327 217 352 241 367 266 350 290 321 314 269 335 274 L335 297 306 359 280 400 259 418 220 418 187 386 161 332 141 287 Z';
const pieces=['M165 307 L194 337 220 361 215 405 193 386 175 349 Z','M222 361 L241 370 262 359 278 401 258 428 229 420 Z','M267 351 L291 320 310 300 295 353 281 391 270 406 Z'];
const titles=['ANTES DO COLAPSO','PERDA DE MAGMA','REBAIXAMENTO','APÓS O COLAPSO'];
const detail=['Reservatório sob a cratera','Menos material no reservatório','Blocos de rocha cedem','Cratera mais profunda'];
export const CalderaCutawayE392:React.FC<{board:Board;private_review_only:boolean;probe?:boolean}>=({board:b,private_review_only,probe})=>{
 if(!private_review_only||!b||b.index<0||b.index>3||!Number.isInteger(b.index))throw Error('E392-PRIVATE');
 const reduced=b.state['reservoir.material']==='reduced',lowered=b.state['roof.position']==='lowered',final=b.state['crater.depth']==='deeper';
 if(reduced!==(b.index>0)||lowered!==(b.index>1)||final!==(b.index===3))throw Error('E392-STATE');
 const ref=React.useRef<SVGSVGElement>(null);
 React.useLayoutEffect(()=>{if(!probe||!ref.current)return;const rows=Array.from(ref.current.querySelectorAll<SVGGraphicsElement>('[data-safe-text]')).map(e=>{const q=e.getBBox();return {text:e.textContent,x:q.x,y:q.y,w:q.width,h:q.height,fit:q.x>=32&&q.x+q.width<=454&&q.y>=145&&q.y+q.height<=690}});console.log('E392_BOARD '+JSON.stringify({index:b.index,state:b.state,focus:b.focus,rows,fit:rows.every(r=>r.fit)}));},[b,probe]);
 const text=(s:string,x:number,y:number,size:number,color=white,weight=700)=><text data-safe-text="true" x={x} y={y} fontSize={size} fill={color} fontWeight={weight}>{s}</text>;
 let lines:{w:string;hl:boolean}[][]=[[]];for(const w of b.caption){const line=lines[lines.length-1];if(line.map(v=>v.w).join(' ').length+w.w.length+1>22&&line.length)lines.push([]);lines[lines.length-1].push(w);}
 return <AbsoluteFill style={{background:'#000'}}>
 <svg ref={ref} viewBox="0 0 540 960" width="100%" height="100%" style={{fontFamily:'Inter,Arial,sans-serif'}}>
 <defs>
  <clipPath id="rockclip"><path d={shape}/></clipPath>
  <linearGradient id="rockwall" x1="0" x2=".15" y1="0" y2="1"><stop stopColor="#806C59"/><stop offset=".45" stopColor="#4F4039"/><stop offset="1" stopColor="#2C2523"/></linearGradient>
  <linearGradient id="craterdepth" x1="0" y1="0" x2=".2" y2="1"><stop stopColor="#090909"/><stop offset="1" stopColor="#342824"/></linearGradient>
 </defs>
 {text('CORINGA',33,163,14,white,800)}{text('EXPLICA',108,163,14,gold,800)}
 <rect x="33" y="173" width="70" height="2.5" fill={gold}/>
 {text(titles[b.index],33,210,25,white,900)}
 {text('CORTE ILUSTRATIVO · SEM ESCALA',33,232,11.5,gold,700)}
 <g transform={`translate(${b.camera.tx} ${b.camera.ty}) scale(${b.camera.scale})`}>
  <path d={shape} transform="translate(3 5)" fill="#171311"/>
  <path d={shape} fill="url(#rockwall)" stroke="#A38B70" strokeWidth="1.5"/>
  <g clipPath="url(#rockclip)">
    {Array.from({length:7},(_,i)=><path key={i} d={`M31 ${314+i*39} Q135 ${289+i*39} 225 ${334+i*39} T450 ${312+i*39} L450 ${326+i*39} Q340 ${357+i*39} 225 ${349+i*39} T31 ${328+i*39} Z`} fill={i%2?'#B19578':'#251F1D'} opacity={i%2?.21:.37}/>)}
    {Array.from({length:22},(_,i)=>{const x=48+(i*83)%386,y=316+(i*47)%263;return <path key={i} d={`M${x} ${y} l${8+i%9} -4 l6 6`} fill="none" stroke="#C3A78A" strokeOpacity=".20" strokeWidth="1.2"/>;})}
    {lowered&&<path d={afterCut} fill="url(#craterdepth)" stroke="#D0AC8F" strokeWidth="1.4"/>}
    {reduced&&!lowered&&<path d={initialMagma} fill="#1C1715" stroke="#B38A67" strokeWidth="1.3" strokeDasharray="5 4"/>}
    <ACutawayMaterial id="magma" d={reduced?smallMagma:initialMagma} tone="hot" offset={2}/>
    {lowered&&pieces.map((d,i)=><ACutawayMaterial key={i} id={'block-'+i} d={d} tone="rock" offset={2}/>)}
  </g>
  {!lowered&&<path d={upper} stroke="#B2A080" strokeWidth="4" fill="none" strokeLinejoin="round"/>}
  {lowered&&<path d="M40 299 L67 287 88 285 108 277 133 277 145 266 L169 289 187 327 217 352 241 367 266 350 290 321 314 269 335 274 356 270 382 283 411 287 445 299" fill="none" stroke="#C3A783" strokeWidth="3.2" strokeLinejoin="round"/>}
  {b.index===2&&<g stroke={gold} strokeWidth="2.8" fill="none"><path d="M209 281 V327 m-6 -8 l6 8 6 -8"/><path d="M267 281 V327 m-6 -8 l6 8 6 -8"/></g>}
 </g>
 <g stroke={gold} fill="none" strokeWidth="1.3"><path d={lowered?'M117 386 H149 L195 355':'M117 423 H145 L181 452'}/><circle cx={lowered?195:181} cy={lowered?355:452} r="2.5" fill={gold}/></g>
 {text(lowered?'BLOCOS':'MAGMA',36,lowered?380:417,12,gold,800)}
 {text(detail[b.index],33,628,20,white,800)}
 {text('Adaptado de USGS / HVO · esquema qualitativo',33,647,10.5,'#B9B9B9',600)}
 {Array.from({length:4},(_,i)=><rect key={i} x={33+i*106} y="655" width="101" height="2.5" fill={i<=b.index?gold:'#373737'}/>)}
 {lines.map((line,i)=><text key={i} x="33" y={681+i*27} fontSize="25" fontWeight="900" fill={white}>{line.map((w,j)=><tspan key={j} fill={w.hl?gold:white}>{w.w}{j<line.length-1?' ':''}</tspan>)}</text>)}
 <text x="33" y="900" fill="#999" fontSize="10">STORYBOARD PRIVADO · NÃO PUBLICAR</text>
 </svg></AbsoluteFill>;
};
