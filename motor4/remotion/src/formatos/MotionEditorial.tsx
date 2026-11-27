/** Motion graphics DOCUMENTAIS; não são vídeos falsos nem criam fatos.
 * Apenas os dados fornecidos por curadoria evoluem visualmente no tempo.
 * Mesmo FilmeEditorial/Remotion, sem novo motor ou identidade paralela.
 */
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {progresso} from './TempoVisualE200';
import {selectChart,num,qualifier,valueText,type Claim} from './MotionChartCoreE3883';

export type MotionEditorialData =
  | {kind:'stat_reveal'; eyebrow:string; value:string; line1:string; line2:string; fraction?:number}
  | {kind:'causal_flow'; eyebrow:string; stages:[string,string,string]};

const GOLD='#FFD21F', INK='#091523', WHITE='#F5F2EB', MUTED='#AAC0CE';
const appear=(p:number,at:number,len:number)=>progresso(p,at,at+len,'easeOut');

export const MotionEditorial:React.FC<{data:MotionEditorialData;p:number}>=({data,p})=>{
  const bodyStart=460;
  // Informação já aparece no primeiro frame; não abrir com tela vazia.
  const eyebrow=appear(p,-.05,.10);
  return <AbsoluteFill style={{background:INK,overflow:'hidden',fontFamily:'Inter,Arial,sans-serif'}}>
    {/* Grade extremamente discreta, sem segunda moldura ou linha amarela. */}
    <AbsoluteFill style={{opacity:.12,backgroundImage:
      'linear-gradient(to right,#7291A1 1px,transparent 1px),linear-gradient(to bottom,#7291A1 1px,transparent 1px)',
      backgroundSize:'96px 96px'}}/>
    <div style={{position:'absolute',left:84,top:bodyStart,right:84,
      fontSize:31,fontWeight:800,letterSpacing:2.2,color:MUTED,
      opacity:eyebrow,transform:`translateY(${(1-eyebrow)*12}px)`}}>
      {data.eyebrow}
    </div>
    {data.kind==='stat_reveal'?(()=>{
      const reveal=appear(p,.08,.20);
      const detail=appear(p,.42,.18);
      const proportion=appear(p,.68,.19);
      return <>
        <div style={{position:'absolute',left:80,right:80,top:610,
          color:GOLD,fontSize:data.value.length>5?160:225,fontWeight:900,
          letterSpacing:-9,lineHeight:1.05,
          opacity:reveal,transform:`translateY(${(1-reveal)*46}px)`}}>
          {data.value}
        </div>
        <div style={{position:'absolute',left:88,right:88,top:946,
          opacity:detail,transform:`translateY(${(1-detail)*25}px)`}}>
          <div style={{fontWeight:900,fontSize:57,color:WHITE,lineHeight:1.12}}>{data.line1}</div>
          <div style={{marginTop:20,fontWeight:500,fontSize:38,color:MUTED,lineHeight:1.24}}>{data.line2}</div>
        </div>
        {data.fraction!==undefined&&<div style={{
          position:'absolute',left:90,right:90,top:1224,opacity:proportion
        }}>
          <div style={{fontSize:22,color:MUTED,letterSpacing:1.5,marginBottom:21}}>
            {data.value.startsWith('>') ? 'LIMITE INFERIOR DOCUMENTADO' :
             data.value.startsWith('<') ? 'LIMITE SUPERIOR DOCUMENTADO' :
             'PARCELA DO TOTAL DOCUMENTADA'}
          </div>
          <div style={{height:16,background:'#24394B',borderRadius:8,overflow:'hidden'}}>
            <div style={{height:'100%',width:`${100*data.fraction*proportion}%`,background:GOLD,borderRadius:8}}/>
          </div>
        </div>}
      </>;
    })():<>
      {/* A linha conecta FATOS sucessivos, sem transformá-los em 'cards'. */}
      <div style={{position:'absolute',left:130,top:645,width:4,height:550,
        background:'#1C4054'}}/>
      {data.stages.map((name,i)=>{
        const at=-.03+i*.30;
        const show=appear(p,at,.13);
        const y=620+i*283;
        const link=i<2?appear(p,at+.15,.19):0;
        return <React.Fragment key={i}>
          {i<2&&<div style={{
            position:'absolute',left:130,top:y+34,width:5,
            height:Math.max(0,249*link),background:GOLD,
          }}/>}
          <div style={{position:'absolute',left:104,top:y,width:57,height:57,
            borderRadius:'50%',background:show>.05?GOLD:'#264254',
            color:INK,opacity:show,fontSize:27,fontWeight:900,
            display:'flex',alignItems:'center',justifyContent:'center'}}>
            {i+1}
          </div>
          <div style={{position:'absolute',left:212,right:66,top:y-11,
            opacity:show,transform:`translateX(${(1-show)*42}px)`}}>
            <div style={{fontSize:24,color:MUTED,fontWeight:700,
              letterSpacing:1.6,marginBottom:15}}>ETAPA {i+1}</div>
            <div style={{fontSize:name.length>21?43:51,color:WHITE,
              fontWeight:900,lineHeight:1.13}}>{name}</div>
          </div>
        </React.Fragment>;
      })}
    </>}
  </AbsoluteFill>;
};

/** E388: speech-anchored reported value in an existing reserved lane.
 * No numeric interpolation, simulated instrument, or claim of pixel measurement.
 * Keep the value stable; animate only entrance and underline. */
export const AttributedStat:React.FC<{value:string;scope:string;elapsed:number;rect:readonly number[];taiwan?:boolean;probe?:boolean}>=({value,scope,elapsed,rect,taiwan=false,probe=false})=>{
  const [x,y,r,b]=rect;
  const host=React.useRef<HTMLDivElement>(null),num=React.useRef<HTMLDivElement>(null);
  const info=React.useRef<HTMLDivElement>(null);
  React.useLayoutEffect(()=>{
    const h=host.current,e=num.current,d=info.current;if(!h||!e||!d)return;
    let fit=false,font=taiwan?84:96;
    for(;font>=54;font--){
      e.style.fontSize=font+'px';
      fit=e.scrollWidth<=h.clientWidth&&d.scrollWidth<=h.clientWidth&&h.scrollHeight<=h.clientHeight;
      if(fit)break;
    }
    if(probe)console.log('E3881_STAT '+JSON.stringify({value,scope,rect,taiwan,font,fit,width:e.scrollWidth,height:h.scrollHeight,slotWidth:h.clientWidth,slotHeight:h.clientHeight}));
  },[value,scope,x,y,r,b,taiwan,probe]);
  const p=Math.min(1,Math.max(0,elapsed/.22));
  return <div ref={host} data-reported-motion={taiwan?'E3881_TAIWAN':'E388'} style={{position:'absolute',left:x,top:y,width:r-x,height:b-y,
    fontFamily:'Inter,Arial,sans-serif',color:WHITE,pointerEvents:'none',overflow:'hidden'}}>
    <div ref={num} style={{fontSize:taiwan?84:96,fontWeight:900,letterSpacing:-3,lineHeight:1.02,color:GOLD,whiteSpace:'nowrap',
      opacity:.65+.35*p,transform:`translateY(${(1-p)*7}px)`}}>{value}</div>
    <div style={{height:4,width:`${p*100}%`,maxWidth:taiwan?320:undefined,background:GOLD,margin:'5px 0 8px'}}/>
    <div ref={info} style={{fontSize:26,fontWeight:650,lineHeight:1.12,color:WHITE}}>{scope}</div>
  </div>;
};

/** E388.3.1: editorial pacing and full-size chart geometry, same Taiwan shell.
 * Actual values remain fixed. Animation reveals known geometry, not measurements.
 */
const CW=839, CH=540;
const ease=(p:number,at:number,len:number)=>1-(1-Math.max(0,Math.min(1,(p-at)/len)))**3;
const fitFont=(s:string,n:number,w:number)=>Math.min(n,Math.floor(w/(Math.max(1,s.length)*.59)));
export const EditorialChart:React.FC<{claim:Claim;p:number;probe?:boolean}>=({claim:c,p,probe})=>{
 const k=selectChart(c),v=c.values,q=qualifier(c),value=valueText(c);
 const ref=React.useRef<HTMLDivElement>(null);
 React.useLayoutEffect(()=>{
   if(!probe||!ref.current)return;
   const host=ref.current;
   const svg=host.querySelector('svg')!;
   const bounds=svg.getBoundingClientRect(),scale=bounds.width/CW;
   const rows=Array.from(host.querySelectorAll<HTMLElement|SVGTextElement>('[data-chart-text]')).map(e=>{
     if(e instanceof SVGTextElement){
       const a=e.getBBox();
       return {text:e.textContent,fit:a.x>=-.5&&a.y>=-.5&&a.x+a.width<=CW+.5&&a.y+a.height<=CH+.5,font:parseFloat(getComputedStyle(e).fontSize)};
     }
     return {text:e.textContent,fit:e.scrollWidth<=e.clientWidth+1&&e.scrollHeight<=e.clientHeight+1,font:parseFloat(getComputedStyle(e).fontSize)};
   });
   const ink=svg.querySelector<SVGGElement>('[data-chart-ink]')!.getBBox();
   const contentHeight=host.scrollHeight;
   console.log('E3883_CHART '+JSON.stringify({kind:k,title:c.title,fixture:c.fixture,fit:rows.every(r=>r.fit)&&contentHeight<=host.clientHeight+1&&scale>0,rows,ink:{x:ink.x,y:ink.y,w:ink.width,h:ink.height},rect:[66,505,905,1170],contentHeight}));
 },[c,k,probe,p]);
 const t=(s:string,x:number,y:number,n:number,w:number,fill=WHITE,anchor:'start'|'middle'|'end'='start',weight=800)=>
   <text data-chart-text x={x} y={y} fontSize={fitFont(s,n,w)} fill={fill} textAnchor={anchor} fontWeight={weight}>{s}</text>;
 const main=(s:string,y=125,n=136)=>t(s,CW/2,y,n,CW-24,GOLD,'middle',900);
 const a=ease(p,.02,.28),b=ease(p,.14,.34);
 const track=(x:number,y:number,w:number,h:number)=> <rect x={x} y={y} width={w} height={h} rx="7" fill="#292929"/>;
 return <div ref={ref} data-editorial-chart={k} style={{position:'absolute',left:66,top:505,width:CW,height:665,color:WHITE,fontFamily:'Inter,Arial,sans-serif',overflow:'hidden'}}>
  <svg width={CW} height={CH} viewBox={`0 0 ${CW} ${CH}`} style={{display:'block'}}>
   <g data-chart-ink>
   {k==='range'&&(()=>{
     const lo=v[0].value,hi=v[1].value;
     const power=10**Math.floor(Math.log10(hi)),step=power/2;
     const max=Math.ceil((hi*1.12)/step)*step;
     const x=32,w=775,pos=(n:number)=>x+w*n/max,yy=320;
     return <>
      {main(value,132,133)}
      {t('FAIXA DOCUMENTADA',CW/2,212,37,CW-40,WHITE,'middle')}
      {track(x,yy,w,40)}
      <rect x={pos(lo)} y={yy} width={Math.max(0,(pos(hi)-pos(lo))*b)} height="40" rx="3" fill={GOLD}/>
      {[lo,hi].map((n,i)=><g key={i}><path d={`M ${pos(n)} ${yy-8} V ${yy+56}`} stroke={GOLD} strokeWidth="4"/></g>)}
      {t(num(lo),pos(lo)-10,yy-24,49,Math.max(110,pos(lo)-x),GOLD,'end')}
      {t(num(hi),Math.min(805,pos(hi)+10),yy+109,49,155,GOLD,'end')}
      {t('0',x,yy+103,32,110,WHITE)}
      {t(num(max)+' '+c.unit,807,yy+162,29,210,WHITE,'end')}
      {t('Intervalo aproximado · não é medição ao vivo',32,515,30,775,WHITE)}
     </>;
   })()}
   {k==='proportion'&&(()=>{
      const ratio=v[0].value/c.denominator!,x=32,w=775,y=270;
      const bound=c.relation==='lower'||c.relation==='upper';
      return <>
       {main(value,169,174)}
       {t(c.relation==='lower'?'LIMITE INFERIOR':c.relation==='upper'?'LIMITE SUPERIOR':'PARCELA DO TOTAL',CW/2,218,38,790,WHITE,'middle')}
       {track(x,y,w,82)}
       <defs><pattern id="e3883-bound" width="18" height="18" patternUnits="userSpaceOnUse"><path d="M-4 4L4 -4M0 18L18 0M14 22L22 14" stroke={GOLD} strokeOpacity=".48" strokeWidth="3"/></pattern></defs>
       {c.relation!=='upper'&&<rect x={x} y={y} width={w*ratio*b} height="82" rx="5" fill={GOLD}/>}
       {bound&&<rect x={c.relation==='lower'?x+w*ratio:x} y={y} width={w*(c.relation==='lower'?1-ratio:ratio)} height="82" fill="url(#e3883-bound)" opacity={a}/>}
       {bound&&<path d={`M${x+w*ratio} ${y-12}V${y+94}`} stroke={GOLD} strokeWidth="4"/>}
       {t('0%',x,397,32,110)}{t('100%',807,397,32,125,WHITE,'end')}
       {t(v[0].label, CW/2,470,48,790,WHITE,'middle')}
       {bound&&t('Hachura: parcela não determinada',CW/2,520,30,790,WHITE,'middle')}
      </>;
   })()}
   {k==='area'&&(()=>{
      const side=Math.sqrt(v[0].value),size=350,x=36,y=178,scale=size/side;
      return <>
       {main(value,137,130)}
       <rect x={x} y={y} width={size} height={size} fill={GOLD} fillOpacity={.13+.25*b} stroke={GOLD} strokeWidth="5"/>
       {side<=10&&Array.from({length:Math.floor(side)},(_,j)=><path key={j} d={`M ${x+(j+1)*scale} ${y} V ${y+size} M ${x} ${y+(j+1)*scale} H ${x+size}`} stroke={GOLD} strokeOpacity=".5" strokeWidth="2"/>)}
       {/* Leave clearance under numeric descenders; the square border already encodes its extent. */}
       {t('ÁREA EQUIVALENTE',438,244,34,380)}
       {t('≈ '+num(side)+' km',438,310,55,380,GOLD)}
       {t('de cada lado',438,358,39,380)}
       {t('Quadrado ilustrativo',438,445,31,380)}
       {t('Não é um mapa',438,486,31,380)}
      </>;
   })()}
   {k==='bars'&&v.map((item,j)=>{
     const gap=v.length===2?235:172,y=24+j*gap,w=775,ratio=item.value/Math.max(...v.map(z=>z.value));
     const draw=ease(p,.04+j*.12,.32);
     return <g key={j}>
      {t(item.label,32,y+51,53,510)}
      {t(q+num(item.value)+' '+c.unit,807,y+51,57,258,GOLD,'end',900)}
      {track(32,y+82,w,51)}
      <rect x="32" y={y+82} width={w*ratio*draw} height="51" rx="6" fill={GOLD}/>
     </g>;
   })}
   {k==='timeline'&&(()=>{
      const ev=c.events!,spacing=ev.length===2?235:164;
      return <>
       <path d={`M66 66 V${66+(ev.length-1)*spacing}`} stroke="#414141" strokeWidth="5"/>
       <path d={`M66 66 V${66+(ev.length-1)*spacing*ease(p,.06,.58)}`} stroke={GOLD} strokeWidth="7"/>
       {ev.map((e,j)=>{
        const y=66+j*spacing,show=ease(p,.02+j*.18,.22);
        return <g key={e.date} opacity={.38+.62*show}>
         <circle cx="66" cy={y} r="22" fill="#000" stroke={GOLD} strokeWidth="6"/>
         <circle cx="66" cy={y} r="10" fill={GOLD}/>
         {t(e.date.split('-').reverse().join('/'),126,y+12,58,690,GOLD)}
         {t(e.label,126,y+77,62,690)}
        </g>;
       })}
       {t('Ordem dos eventos · sem escala de duração',32,527,30,775)}
      </>;
   })()}
   {k==='number'&&<>
      <path d="M32 66H807 M32 458H807" stroke="#333" strokeWidth="2"/>
      <g opacity={.72+.28*a} transform={`translate(0 ${(1-a)*18})`}>{main(value,265,195)}</g>
      <rect x={CW/2-120*b} y="309" width={240*b} height="7" fill={GOLD}/>
      {t(v[0].label,CW/2,403,54,790,WHITE,'middle')}
   </>}
   </g>
  </svg>
  <div data-chart-text style={{fontSize:30,lineHeight:1.12,fontWeight:600,color:'#D1D1D1',marginTop:14,overflowWrap:'break-word'}}>{c.scope}</div>
  {c.fixture&&<div data-chart-text style={{fontSize:25,lineHeight:1.12,fontWeight:800,marginTop:8,color:GOLD}}>DADOS FICTÍCIOS · TESTE VISUAL</div>}
 </div>;
};
