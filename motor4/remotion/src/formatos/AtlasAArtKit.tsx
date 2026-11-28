/** A kit de desenho de materiais compartilhado, NÃO um simulador físico.
 * Uma linguagem consistente entre famílias; dados e geometrias continuam
 * específicos de cada capacidade. SVG autoral, sem pixels de terceiros.
 */
import React from 'react';
export type ATone='cobalt'|'steel'|'sand';
const MATERIAL:Record<ATone,{face:string;edge:string;light:string;shadow:string}>={
  cobalt:{face:'#11496A',edge:'#10334C',light:'#7BDDE7',shadow:'#04253B'},
  steel:{face:'#527A9B',edge:'#163F63',light:'#D8F3EC',shadow:'#102F4F'},
  sand:{face:'#A79E87',edge:'#42586A',light:'#F2DEC0',shadow:'#263E50'}
};
export const ABeveledPanel:React.FC<{
 x:number;y:number;width:number;height:number;tone?:ATone;rx?:number;opacity?:number
}>=({x,y,width,height,tone='steel',rx=12,opacity=1})=>{
 const a=MATERIAL[tone];
 return <g opacity={opacity}>
   <rect x={x+8} y={y+11} width={width} height={height}
     rx={rx} fill={a.shadow} opacity=".58"/>
   <rect x={x} y={y} width={width} height={height}
     rx={rx} fill={a.face} stroke={a.edge} strokeWidth="12"/>
   <path d={`M${x+rx+7} ${y+9} H${x+width-rx-7}`}
     fill="none" stroke={a.light} strokeWidth="7" strokeLinecap="round"
     opacity=".78"/>
   <path d={`M${x+12} ${y+height-rx} V${y+rx+14}`}
     fill="none" stroke={a.light} strokeWidth="5" opacity=".27"/>
   <path d={`M${x+rx+8} ${y+height-9} H${x+width-rx-10}`}
     fill="none" stroke={a.shadow} strokeWidth="7" opacity=".78"/>
 </g>;
};
export const ARivet:React.FC<{x:number;y:number;r?:number}>=({
 x,y,r=11
})=><g>
  <circle cx={x+2} cy={y+3} r={r+2} fill="#092B44" opacity=".7"/>
  <circle cx={x} cy={y} r={r} fill="#658BA5"
    stroke="#D5F5E9" strokeWidth="3"/>
  <path d={`M${x-r*.39} ${y-r*.3} L${x+r*.35} ${y+r*.3}`}
    stroke="#214562" strokeWidth="3.3" strokeLinecap="round"/>
</g>;
export const AJoint:React.FC<{
 x:number;y:number;r:number;active?:boolean;accent?:string
}>=({x,y,r,active=false,accent='#FFD21F'})=><g>
  {active&&<circle cx={x} cy={y} r={r+19} fill={accent} opacity=".16"/>}
  <circle cx={x+3} cy={y+5} r={r+4} fill="#061B34" opacity=".55"/>
  <circle cx={x} cy={y} r={r} fill="#185A82" stroke="#9DE4E4"
    strokeWidth="6"/>
  <circle cx={x} cy={y} r={r*.73} fill="#173A60"
    stroke={active?accent:'#A9D3DA'} strokeWidth="5"/>
  <path d={`M${x-r*.45} ${y-r*.46} Q${x} ${y-r*.78} ${x+r*.47} ${y-r*.47}`}
    stroke="#D4FAE9" strokeWidth="4" fill="none" opacity=".7"/>
</g>;

/** Shared cutaway material treatment for authored silhouettes. 2.5D shading
 * is illustrative, not measured depth. Does not change existing components. */
export const ACutawayMaterial:React.FC<{id:string;d:string;tone:'rock'|'hot'|'shadow';offset?:number}>=({id,d,tone,offset=5})=>{
 const shades={rock:['#AD9278','#6A5144','#342B29'],hot:['#FFD176','#E56B32','#9A241D'],shadow:['#51453E','#292522','#151313']}[tone];
 return <g>
  <defs><linearGradient id={id+'-surface'} x1="0" y1="0" x2=".35" y2="1" gradientUnits="objectBoundingBox"><stop offset="0" stopColor={shades[0]}/><stop offset=".48" stopColor={shades[1]}/><stop offset="1" stopColor={shades[2]}/></linearGradient></defs>
  <path d={d} transform={`translate(${offset} ${offset})`} fill={shades[2]} stroke="#191515" strokeWidth="2"/>
  <path d={d} fill={`url(#${id}-surface)`} stroke={tone==='hot'?'#F5A36C':'#BAA38F'} strokeWidth="1.4" strokeLinejoin="round"/>
 </g>;
};

/** Opt-in illustrated material overlays. Fixed-seed procedural marks are authored
 * texture, not microscopy or measured physical surface detail. */
export const ASurfaceGrain:React.FC<{id:string;d:string;kind:'rock'|'hot'|'metal';opacity?:number}>=({id,d,kind,opacity=.24})=>{
 const warm=kind==='hot',metal=kind==='metal';
 return <g pointerEvents="none"><defs>
 <pattern id={id+'-grain'} width={metal?9:29} height={metal?31:27} patternUnits="userSpaceOnUse" patternTransform={metal?'rotate(-24)':undefined}>
 {Array.from({length:metal?9:29},(_,i)=>{const x=(i*13.31)%29,y=(i*7.13)%27;return metal?<path key={i} d={`M${i} 0 V31`} stroke={i%3?'#fff':'#111'} strokeOpacity={i%3?.11:.27} strokeWidth=".55"/>:<path key={i} d={`M${x} ${y} l${1+i%4} ${(i%3)-1}`} stroke={i%3?(warm?'#FEC06C':'#D9C8AA'):'#140F0C'} strokeOpacity={i%3?.55:.8} strokeWidth={i%4===0?1.1:.5}/>;})}
 </pattern></defs><path d={d} fill={`url(#${id}-grain)`} opacity={opacity}/></g>;
};
