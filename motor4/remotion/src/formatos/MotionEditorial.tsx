/** Motion graphics DOCUMENTAIS; não são vídeos falsos nem criam fatos.
 * Apenas os dados fornecidos por curadoria evoluem visualmente no tempo.
 * Mesmo FilmeEditorial/Remotion, sem novo motor ou identidade paralela.
 */
import React from 'react';
import {AbsoluteFill} from 'remotion';

export type MotionEditorialData =
  | {kind:'stat_reveal'; eyebrow:string; value:string; line1:string; line2:string; fraction?:number}
  | {kind:'causal_flow'; eyebrow:string; stages:[string,string,string]};

const GOLD='#FFD21F', INK='#091523', WHITE='#F5F2EB', MUTED='#AAC0CE';
const clamp=(n:number)=>Math.max(0,Math.min(1,n));
const appear=(p:number,at:number,len:number)=>{const n=clamp((p-at)/len);return 1-Math.pow(1-n,3);};

export const MotionEditorial:React.FC<{data:MotionEditorialData;p:number}>=({data,p})=>{
  const bodyStart=460;
  const eyebrow=appear(p,.08,.17);
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
      const reveal=appear(p,.23,.23);
      const detail=appear(p,.56,.18);
      const proportion=appear(p,.71,.18);
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
            PARCELA DO TOTAL DOCUMENTADA
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
        const at=.18+i*.25;
        const show=appear(p,at,.18);
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
