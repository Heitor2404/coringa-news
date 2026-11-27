/** E388.3 private chart data contract. No topic heuristics or invented denominators. */
export type Item={label:string;value:number};
export type Claim={
 schema:'coringa.motion.claim.private.v1';publish:false;title:string;scope:string;
 source:{url:string;statement:string;date:string}|null;
 fixture:boolean;unit:string;
 shape:'scalar'|'interval'|'part'|'area'|'comparison'|'timeline';
 values:Item[];relation?:'exact'|'approx'|'lower'|'upper';denominator?:number;
 comparable?:true;events?:{label:string;date:string}[];
};
export type Kind='number'|'range'|'proportion'|'area'|'bars'|'timeline';
const fail=(s:string):never=>{throw new Error('E3883-'+s)};
const label=(s:unknown,max:number)=>typeof s==='string'&&s.trim().length>0&&s.length<=max;
const finite=(n:unknown):n is number=>typeof n==='number'&&Number.isFinite(n)&&n>=0&&n<=1e12;
export function selectChart(c:Claim):Kind{
 if(!c||c.schema!=='coringa.motion.claim.private.v1'||c.publish!==false||typeof c.fixture!=='boolean'||!label(c.title,48)||!label(c.scope,100)||typeof c.unit!=='string'||c.unit.length>12||!Array.isArray(c.values))fail('CONTRACT');
 if(c.fixture?c.source!==null:(!c.source||!/^https:\/\/[^\s]+$/.test(c.source.url)||!label(c.source.statement,500)||!label(c.source.date,32)))fail('SOURCE');
 if(c.values.some(v=>!v||!label(v.label,32)||!finite(v.value)))fail('VALUE');
 if(c.relation!==undefined&&!['exact','approx','lower','upper'].includes(c.relation))fail('RELATION');
 const n=c.values.length;
 if(c.shape==='timeline'){
   const e=c.events;
   if(n||c.unit||c.denominator!==undefined||c.relation||!e||e.length<2||e.length>3||e.some((v,i)=>!label(v.label,40)||!/^\d{4}-\d{2}-\d{2}$/.test(v.date)||!Number.isFinite(Date.parse(v.date))||new Date(v.date).toISOString().slice(0,10)!==v.date||(i>0&&v.date<=e[i-1].date)))fail('TIME');
   return 'timeline';
 }
 if(c.events!==undefined)fail('EVENTS');
 if(c.shape==='part'){
   if(n!==1||!finite(c.denominator)||!c.denominator||c.values[0].value>c.denominator||c.unit!=='%')fail('PART');
   return 'proportion';
 }
 if(c.denominator!==undefined)fail('DENOMINATOR');
 if(c.shape==='interval'){
   if(n!==2||c.values[0].value>=c.values[1].value||!c.unit||!['exact','approx'].includes(c.relation||'exact'))fail('RANGE');
   return 'range';
 }
 if(c.shape==='area'){
   if(n!==1||c.unit!=='km²'||c.values[0].value<=0||c.values[0].value>10000||!['exact','approx'].includes(c.relation||'exact'))fail('AREA');
   return 'area';
 }
 if(c.shape==='comparison'){
   if(n<2||n>3||c.comparable!==true||!c.unit||!c.values.some(v=>v.value>0)||!['exact','approx'].includes(c.relation||'exact'))fail('COMPARABILITY');
   return 'bars';
 }
 if(c.shape==='scalar'&&n===1)return 'number';
 return fail('SHAPE');
}
export const num=(v:number)=>new Intl.NumberFormat('pt-BR',{maximumFractionDigits:3}).format(v);
export const qualifier=(c:Claim)=>c.relation==='approx'?'≈ ':c.relation==='lower'?'> ':c.relation==='upper'?'< ':'';
export function valueText(c:Claim):string{
 const k=selectChart(c),v=c.values;
 if(k==='timeline'||k==='bars')return '';
 if(k==='proportion')return qualifier(c)+num(100*v[0].value/c.denominator!)+'%';
 if(k==='range')return qualifier(c)+num(v[0].value)+'–'+num(v[1].value)+' '+c.unit;
 return (qualifier(c)+num(v[0].value)+' '+c.unit).trim();
}
