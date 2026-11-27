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

/** E388.3: data-driven graphics inside FilmeEditorial's Taiwan shell.
 * Animation reveals geometry; it never changes the reported values. */
export const EditorialChart:React.FC<{claim:Claim;p:number;probe?:boolean}>=({claim:c,p,probe})=>{
 const k=selectChart(c),v=c.values,q=qualifier(c),value=valueText(c);
 const progress=Math.min(1,Math.max(0,p*3)),reveal=1-(1-progress)**3;
 const ref=React.useRef<HTMLDivElement>(null);
 React.useLayoutEffect(()=>{
   if(!probe||!ref.current)return;
   const host=ref.current;
   const rows=Array.from(host.querySelectorAll<HTMLElement>('[data-chart-text]')).map(e=>({text:e.textContent,fit:e.scrollWidth<=e.clientWidth+1&&e.scrollHeight<=e.clientHeight+1}));
   console.log('E3883_CHART '+JSON.stringify({kind:k,title:c.title,fixture:c.fixture,fit:rows.every(r=>r.fit),rows,rect:[66,454,905,1138]}));
 },[c,k,probe]);
 const line=(text:string,size:number,style:React.CSSProperties={})=><div data-chart-text style={{fontSize:size,lineHeight:1.15,fontWeight:800,overflowWrap:'break-word',...style}}>{text}</div>;
 const track=(f:number,rangeStart=0)=><div style={{height:28,position:'relative',background:'#292929',marginTop:24}}>
   <div style={{position:'absolute',left:rangeStart*100+'%',width:(f-rangeStart)*100*reveal+'%',height:'100%',background:GOLD}}/>
 </div>;
 return <div ref={ref} data-editorial-chart={k} style={{position:'absolute',left:66,top:454,width:839,height:684,color:WHITE,fontFamily:'Inter,Arial,sans-serif',overflow:'hidden'}}>
   {value&&line(value,value.length>14?68: value.length>10?90:130,{color:GOLD,letterSpacing:-3,marginBottom:28})}
   {k==='range'&&<>
     {line('INTERVALO DOCUMENTADO',30,{color:WHITE})}
     {track(1,v[0].value/v[1].value)}
     <div style={{display:'flex',justifyContent:'space-between',marginTop:18}}>{line('0',28)}{line(num(v[0].value),32,{color:GOLD})}{line(num(v[1].value)+' '+c.unit,32,{color:GOLD})}</div>
     {line('Faixa aproximada, não medição em tempo real.',30,{marginTop:45,color:WHITE})}
   </>}
   {k==='proportion'&&<>
     {line(c.relation==='lower'?'LIMITE INFERIOR':c.relation==='upper'?'LIMITE SUPERIOR':'PARCELA DO TOTAL',30)}
     {track(v[0].value/c.denominator!)}
     <div style={{display:'flex',justifyContent:'space-between',marginTop:18}}>{line('0%',28)}{line('100%',28)}</div>
     {line(v[0].label,42,{marginTop:44})}
   </>}
   {k==='area'&&(()=>{
     const a=v[0].value;
     // Square with equal sides; reference grid only when it remains readable.
     // Not an outline of the real territory.
     const side=Math.sqrt(a),scale=350/Math.max(1,side);
     const size=side*scale;
     return <>
      <svg width="839" height="370" viewBox="0 0 839 370">
       <rect x="12" y="8" width={size} height={size} fill={GOLD} fillOpacity={.18+.25*reveal} stroke={GOLD} strokeWidth="4"/>
       {side<=10&&Array.from({length:Math.floor(side)},(_,i)=><React.Fragment key={i}><path d={`M ${12+(i+1)*scale} 8 V ${8+size} M 12 ${8+(i+1)*scale} H ${12+size}`} stroke={GOLD} strokeOpacity=".65" strokeWidth="2"/></React.Fragment>)}
       <text x={Math.max(396,size+32)} y="72" fill={WHITE} fontSize="30" fontWeight="800">ÁREA EQUIVALENTE</text>
       <text x={Math.max(396,size+32)} y="122" fill={GOLD} fontSize="42" fontWeight="900">{'≈ '+num(side)+' km'}</text>
       <text x={Math.max(396,size+32)} y="160" fill={WHITE} fontSize="26">de cada lado</text>
       <text x={Math.max(396,size+32)} y="228" fill={WHITE} fontSize="24">Quadrado de referência</text>
       <text x={Math.max(396,size+32)} y="260" fill={WHITE} fontSize="24">Não é mapa geográfico</text>
      </svg>
     </>;
   })()}
   {k==='bars'&&v.map((item,i)=><div key={i} style={{marginBottom:24}}>
     <div style={{display:'flex',justifyContent:'space-between',gap:12}}>{line(item.label,32,{maxWidth:560})}{line(q+num(item.value)+' '+c.unit,36,{color:GOLD})}</div>
     {track(item.value/Math.max(...v.map(x=>x.value)))}
   </div>)}
   {k==='timeline'&&<>
     {line('ORDEM CRONOLÓGICA',28)}
     <div style={{borderLeft:'4px solid '+GOLD,margin:'36px 0 18px 14px',paddingLeft:28}}>
      {c.events!.map((e,i)=><div key={e.date} style={{marginBottom:26,opacity:.6+.4*reveal}}>
       {line(e.date.split('-').reverse().join('/'),36,{color:GOLD})}{line(e.label,40)}
      </div>)}
     </div>
     {line('Espaçamento esquemático, não proporcional ao tempo.',26)}
   </>}
   {k==='number'&&line(v[0].label,48)}
   {line(c.scope,30,{marginTop:22,color:'#D1D1D1',fontWeight:600})}
   {c.fixture&&line('DADOS FICTÍCIOS · TESTE VISUAL',24,{marginTop:12,color:GOLD})}
 </div>;
};
