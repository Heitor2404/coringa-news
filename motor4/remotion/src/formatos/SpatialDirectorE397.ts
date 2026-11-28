import {PerspectiveCamera,Vector3} from 'three';
import {cruise} from './GlobalMapMotionE396D';
export type V3=[number,number,number];
export type Bounds={min:V3;max:V3};
export type CaseId='ship'|'wind';
export const W=720,H=1280,FPS=30,DURATION=10;
export const MODELS:Record<CaseId,{name:string;bounds:Bounds;detail:Bounds;measure:[V3,V3];label:string;focus:V3}> = {
 ship:{name:'NAVIO PORTA-CONTÊINERES',bounds:{min:[-3.8,-1.5,-15],max:[3.8,5.5,15]},detail:{min:[-2.4,1,-7],max:[2.4,4,0]},measure:[[-3.5,.05,-15],[-3.5,.05,15]],label:'300 m',focus:[0,2.8,-3.5]},
 wind:{name:'TURBINA EÓLICA',bounds:{min:[-5.2,0,-1.4],max:[5.2,15.2,2]},detail:{min:[-1.8,8.5,-1.4],max:[1.8,11.5,2]},measure:[[5.8,0,0],[5.8,10,0]],label:'100 m',focus:[0,10,.5]}
};
export const corners=(b:Bounds):V3[]=>b.min.flatMap((_,i)=>i===0? [b.min[0],b.max[0]].flatMap(x=>[b.min[1],b.max[1]].flatMap(y=>[b.min[2],b.max[2]].map(z=>[x,y,z] as V3))):[]);
export const center=(b:Bounds):V3=>b.min.map((v,i)=>(v+b.max[i])/2) as V3;
const mix=(a:number,b:number,t:number)=>a+(b-a)*t;
const mix3=(a:V3,b:V3,t:number)=>a.map((v,i)=>mix(v,b[i],t)) as V3;
export function fitCamera(b:Bounds,yaw:number,elev:number,margin=.80){
 const target=center(b), dir=new Vector3(Math.sin(yaw)*Math.cos(elev),Math.sin(elev),Math.cos(yaw)*Math.cos(elev));
 const camera=new PerspectiveCamera(36,W/H,.05,1000);
 const set=(distance:number)=>{camera.position.copy(new Vector3(...target).addScaledVector(dir,distance));camera.lookAt(...target);camera.updateMatrixWorld();camera.updateProjectionMatrix();};
 const fits=()=>corners(b).every(p=>{const v=new Vector3(...p).project(camera);return Math.abs(v.x)<=margin&&Math.abs(v.y)<=margin&&v.z>=-1&&v.z<=1;});
 let lo=.1,hi=300;set(hi);if(!fits())throw Error('E397-FIT');
 for(let n=0;n<32;n++){const mid=(lo+hi)/2;set(mid);if(fits())hi=mid;else lo=mid;}
 set(hi+.02);return {position:camera.position.toArray() as V3,target,distance:hi+.02};
}
export function shotAt(id:CaseId,t:number){
 const m=MODELS[id],a=cruise((t-1.2)/4.7),b=cruise((t-6.1)/3.5);
 const yaw=id==='ship'?mix(.44,.62,b):mix(.34,-.22,b);
 const elev=id==='ship'?mix(.62,.74,b):mix(.18,.28,b);
 const detail=fitCamera(m.detail,yaw,elev,.78),whole=fitCamera(m.bounds,yaw,elev,.76);
 const target=mix3(detail.target,whole.target,a),distance=mix(detail.distance,whole.distance,a);
 const dir=new Vector3(Math.sin(yaw)*Math.cos(elev),Math.sin(elev),Math.cos(yaw)*Math.cos(elev));
 const position=new Vector3(...target).addScaledVector(dir,distance).toArray() as V3;
 const camera=new PerspectiveCamera(36,W/H,.05,1000);camera.position.set(...position);camera.lookAt(...target);camera.updateMatrixWorld();camera.updateProjectionMatrix();
 return {camera,position,target,whole:a>=.999,phase:a<.999?'detail':'overview',measureOpacity:cruise((t-6.1)/.8)};
}
export function project(cam:PerspectiveCamera,p:V3){const v=new Vector3(...p).project(cam);return {x:(v.x+1)*W/2,y:(1-v.y)*H/2,z:v.z};}
