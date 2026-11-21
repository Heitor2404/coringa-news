/** Contratos reutilizáveis para mecanismos 2D do compositor documental.
 * Estado é função pura do tempo + eventos + geometria. Não usa nome do tema,
 * não introduz fatos, não fragmenta a mesma cena em cartões.
 */
export type MechanismEvent<A extends string=string> = {
  at: number;
  action: A;
  label: string;
};
export type Point2D = {x:number; y:number};
export const clamp01=(v:number):number=>Math.max(0,Math.min(1,v));
export const smooth=(v:number):number=>{
  const x=clamp01(v);
  return x*x*(3-2*x);
};
export const eventAt = <A extends string>(
  t:number,events:readonly MechanismEvent<A>[],fallback:MechanismEvent<A>
):MechanismEvent<A>=>{
  // Falta de evento não gera animação aleatória; preflight da pauta
  // valida ordem/capacidades antes de habilitar modo público.
  let current=fallback;
  for(const e of events) if(e.at<=t&&e.at>=current.at) current=e;
  return current;
};
export const eventTime=<A extends string>(
  events:readonly MechanismEvent<A>[],action:A
):number|undefined=>events.find(e=>e.action===action)?.at;

/** Rotação rígida em torno de pivô. A carga e a extremidade de esforço
 * partilham ESTA relação geométrica; nunca seguem animações independentes.
 */
export const rotateAbout=(pivot:Point2D,point:Point2D,degrees:number):Point2D=>{
  const angle=degrees*Math.PI/180;
  const dx=point.x-pivot.x,dy=point.y-pivot.y;
  return {
    x:pivot.x+dx*Math.cos(angle)-dy*Math.sin(angle),
    y:pivot.y+dx*Math.sin(angle)+dy*Math.cos(angle),
  };
};
export const leverAdvantage=(pivotX:number,loadX:number,effortX:number):number=>{
  const loadArm=Math.abs(pivotX-loadX),effortArm=Math.abs(effortX-pivotX);
  return loadArm>0?effortArm/loadArm:0;
};
