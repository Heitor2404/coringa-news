// Shared editorial camera uses the already tested semantic camera and preserves the entire critical bbox.
import {semanticCamera2D,fitsFrame,type FrameBox,type FramePoint} from './MechanismCamera2D';
export function editorialCamera(t:number,machine:FrameBox,viewport:FrameBox,focus:FramePoint,previousFocus:FramePoint,changeAt:number,maxScale:number){
 const c=semanticCamera2D({t,machine,focus,previousFocus,changeAt,startViewport:viewport,detailViewport:viewport,maxScale,zoomStart:.15,zoomSeconds:2.2});
 if(!fitsFrame(c,machine,viewport))throw Error('E394-CAMERA-CLIP');return c;
}
export function solidShift(p:number,distance:number){if(!Number.isFinite(p)||p<0||p>1||!Number.isFinite(distance)||distance<0)throw Error('E394-SOLID');return -distance*(1-p);}
