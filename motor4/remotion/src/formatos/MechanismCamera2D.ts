/** Enquadramento SEMÂNTICO reutilizável de mecanismos 2D verticais.
 *
 * Não depende de assunto, aparência do ator nem palavras da narração.
 * A câmera acompanha alvos fornecidos pela física e garante que o bounding
 * box CRÍTICO permanece no viewport seguro. A câmera não altera a física.
 */
export type FramePoint={x:number;y:number};
export type FrameBox={left:number;top:number;right:number;bottom:number};
export type FrameCamera={scale:number;tx:number;ty:number;zoom:number};
export type CameraDirectorInput={
  t:number;
  machine:FrameBox;              // TODO: vindo de bounding boxes semânticas do SceneGraph
  focus:FramePoint;
  previousFocus:FramePoint;
  changeAt:number;
  startViewport:FrameBox;
  detailViewport:FrameBox;
  maxScale:number;
  zoomStart?:number;
  zoomSeconds?:number;
};
const clamp=(x:number,a:number,b:number)=>Math.max(a,Math.min(b,x));
export const ease=(x:number):number=>{
  const s=clamp(x,0,1);
  return s*s*(3-2*s);
};
export const lerp=(a:number,b:number,t:number):number=>a+(b-a)*t;
const center=(a:number,b:number)=>(a+b)/2;
export const validBox=(b:FrameBox):boolean=>
  Object.values(b).every(Number.isFinite) &&
  b.left<b.right && b.top<b.bottom;

export const semanticCamera2D=(input:CameraDirectorInput):FrameCamera=>{
  const {t,machine,focus,previousFocus,changeAt,startViewport,detailViewport,maxScale}=input;
  if(!validBox(machine)||!validBox(startViewport)||!validBox(detailViewport)
    ||!Number.isFinite(t)||!Number.isFinite(changeAt)
    ||!Number.isFinite(maxScale)||maxScale<1
    ||![focus.x,focus.y,previousFocus.x,previousFocus.y].every(Number.isFinite)){
    throw new Error('F-CAMERA-INPUT');
  }
  const z=ease((t-(input.zoomStart??1.1))/(input.zoomSeconds??1));
  const viewport:FrameBox={
    left:lerp(startViewport.left,detailViewport.left,z),
    right:lerp(startViewport.right,detailViewport.right,z),
    top:lerp(startViewport.top,detailViewport.top,z),
    bottom:lerp(startViewport.bottom,detailViewport.bottom,z),
  };
  const machineWidth=machine.right-machine.left;
  const machineHeight=machine.bottom-machine.top;
  const fits=Math.min(
    (viewport.right-viewport.left)/machineWidth,
    (viewport.bottom-viewport.top)/machineHeight
  );
  // Clamping here is geometric; no unbounded zoom that crops the mechanism.
  const scale=Math.min(lerp(1,maxScale,z),fits);
  if(scale<.999){
    throw new Error('F-CAMERA-NAO-CABE');
  }
  const xcenter=center(viewport.left,viewport.right);
  const ycenter=center(viewport.top,viewport.bottom);
  const sceneX=center(machine.left,machine.right);
  const sceneY=center(machine.top,machine.bottom);
  const focusBlend=ease((t-changeAt)/.50);
  const fx=lerp(previousFocus.x,focus.x,focusBlend);
  const fy=lerp(previousFocus.y,focus.y,focusBlend);

  const baseTx=xcenter-scale*sceneX;
  const baseTy=ycenter-scale*sceneY;
  // Only subtle semantic tracking; important parts always remain onscreen.
  const rawTx=baseTx+(sceneX-fx)*.33*z;
  const rawTy=baseTy+(sceneY-fy)*.075*z;
  const lowTx=viewport.left-scale*machine.left;
  const highTx=viewport.right-scale*machine.right;
  const lowTy=viewport.top-scale*machine.top;
  const highTy=viewport.bottom-scale*machine.bottom;
  return {
    scale,zoom:z,
    tx:clamp(rawTx,lowTx,highTx),
    ty:clamp(rawTy,lowTy,highTy),
  };
};
export const project=(c:FrameCamera,p:FramePoint):FramePoint=>
  ({x:c.scale*p.x+c.tx,y:c.scale*p.y+c.ty});
export const fitsFrame=(c:FrameCamera,box:FrameBox,v:FrameBox,eps=1e-6):boolean=>
  project(c,{x:box.left,y:box.top}).x>=v.left-eps &&
  project(c,{x:box.right,y:box.bottom}).x<=v.right+eps &&
  project(c,{x:box.left,y:box.top}).y>=v.top-eps &&
  project(c,{x:box.right,y:box.bottom}).y<=v.bottom+eps;
