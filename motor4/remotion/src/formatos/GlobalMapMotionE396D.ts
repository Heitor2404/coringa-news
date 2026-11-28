/** Deterministic editorial motion. Integrated acceleration, constant cruise, deceleration. */
export function cruise(x:number,r=.16):number {
  x=Math.max(0,Math.min(1,x)); if(r<=0||r>=.5)throw Error('MAP-RAMP');
  return x<r?x*x/(2*r*(1-r)):x>1-r?1-(1-x)*(1-x)/(2*r*(1-r)):(x-r/2)/(1-r);
}
export function smoothAngle(angles:number[]):number{
  if(!angles.length)return 0;
  const x=angles.reduce((s,a)=>s+Math.cos(a*Math.PI/180),0),y=angles.reduce((s,a)=>s+Math.sin(a*Math.PI/180),0);
  return Math.atan2(y,x)*180/Math.PI;
}
