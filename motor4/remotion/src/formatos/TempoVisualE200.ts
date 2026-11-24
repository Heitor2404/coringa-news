/** Relógio determinístico compartilhado. Marcos são editoriais, não velocidade física. */
export type MarcoProgresso={t:number;fracao:number;fonte:string};
export type Interpolacao='degrau'|'linear_ilustrativa';
export function progresso(t:number,a:number,b:number,curva:'linear'|'easeIO'|'easeOut'='linear'){
  const x=Math.min(1,Math.max(0,(t-a)/Math.max(.01,b-a)));
  if(curva==='easeIO')return x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2;
  if(curva==='easeOut')return 1-Math.pow(1-x,3);
  return x;
}
export function progressoMarcos(t:number,marcos:MarcoProgresso[],modo:Interpolacao){
  if(!['degrau','linear_ilustrativa'].includes(modo)||marcos.length<2||marcos.length>100||
    marcos.some((m,i)=>!Number.isFinite(m.t)||!Number.isFinite(m.fracao)||m.fracao<0||m.fracao>1||
      typeof m.fonte!=='string'||!m.fonte.trim()||(i>0&&(m.t<=marcos[i-1].t||m.fracao<marcos[i-1].fracao)))||
    marcos[0].fracao!==0||marcos[marcos.length-1].fracao!==1)throw new Error('E200-MARCOS');
  if(t<=marcos[0].t)return 0;
  for(let i=1;i<marcos.length;i++){
    const a=marcos[i-1],b=marcos[i];
    if(t<b.t)return modo==='degrau'?a.fracao:a.fracao+(b.fracao-a.fracao)*(t-a.t)/(b.t-a.t);
  }
  return 1;
}
