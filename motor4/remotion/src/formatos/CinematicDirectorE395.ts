// E395: editorial detail shots are explicit crops, not a relaxed full-view safety gate.
import {fitsFrame,type FrameBox,type FrameCamera} from './MechanismCamera2D';
export type Shot={id:string;start:number;end:number;roi:FrameBox};
export function detailAt(t:number,shots:Shot[],viewport:FrameBox,maxScale:number){
 const s=shots.find(x=>t>=x.start&&t<x.end);if(!s)return null;
 const r=s.roi;if(r.right<=r.left||r.bottom<=r.top||s.end<=s.start)throw Error('E395-ROI');
 const scale=Math.min(maxScale,(viewport.right-viewport.left)/(r.right-r.left),(viewport.bottom-viewport.top)/(r.bottom-r.top));
 const c:FrameCamera={scale,tx:(viewport.left+viewport.right-scale*(r.left+r.right))/2,ty:(viewport.top+viewport.bottom-scale*(r.top+r.bottom))/2,zoom:1};
 if(scale<=1||!fitsFrame(c,r,viewport))throw Error('E395-DETAIL-FIT');return {id:s.id,roi:r,camera:c};
}
export const svgCamera=(c:{scale:number;tx:number;ty:number})=>`translate(${c.tx} ${c.ty}) scale(${c.scale})`;
