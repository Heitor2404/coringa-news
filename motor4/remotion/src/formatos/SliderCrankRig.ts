/** Piston/biela/eixo: cinemática exata e independente do assunto.
 * Eixo de deslizamento vertical; pino do pistão está sempre a distância L
 * do pino de manivela. Nenhuma parte possui timeline independente.
 */
export type RigGeometry={
  centerX:number;centerY:number;radius:number;rodLength:number;
  pistonWidth:number;pistonHeight:number
};
export type RigState={
  theta:number;crankPin:{x:number;y:number};pistonPin:{x:number;y:number};
  pistonTop:number;displacement:number;rodAngle:number;
};
export const clamp01=(v:number)=>Math.max(0,Math.min(1,v));
export const angleAt=(t:number,duration:number):number=>{
  // 1 volta em duration; chamada pura e deterministica por frame.
  if(!Number.isFinite(t)||!Number.isFinite(duration)||duration<=0)
    throw new Error('Invalid timeline');
  return 2*Math.PI*clamp01(t/duration);
};
export const rigState=(theta:number,g:RigGeometry):RigState=>{
  if(!Number.isFinite(theta)||!Object.values(g).every(Number.isFinite)||
      g.radius<=0||g.rodLength<=g.radius||g.pistonWidth<=0||g.pistonHeight<=0)
    throw new Error('Invalid slider-crank geometry');
  const dx=g.radius*Math.sin(theta);
  const crankY=g.centerY-g.radius*Math.cos(theta);
  const pistonY=g.centerY-g.radius*Math.cos(theta)-
    Math.sqrt(g.rodLength*g.rodLength-dx*dx);
  const top=g.centerY-g.radius-g.rodLength;
  return {
    theta,
    crankPin:{x:g.centerX+dx,y:crankY},
    pistonPin:{x:g.centerX,y:pistonY},
    pistonTop:pistonY-g.pistonHeight*.69,
    displacement:pistonY-top,
    rodAngle:Math.atan2(dx,crankY-pistonY)
  };
};
export const rodDistance=(s:RigState):number=>
  Math.hypot(s.pistonPin.x-s.crankPin.x,
             s.pistonPin.y-s.crankPin.y);
