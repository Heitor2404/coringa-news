import {PerspectiveCamera,Vector3} from 'three';
import {cruise} from './GlobalMapMotionE396D';
export type V3=[number,number,number];
export type Bounds={min:V3;max:V3};
export type CaseId='ship'|'wind';
export const W=720,H=1280,FPS=30,DURATION=12;
export const MODELS:Record<CaseId,{name:string;bounds:Bounds;detail:Bounds;measure:[V3,V3];label:string;focus:V3}> = {
 ship:{name:'NAVIO PORTA-CONTÊINERES',bounds:{min:[-2.5,-1.27,-15],max:[2.5,4.55,15]},detail:{min:[-.85,1.36,-4.8],max:[.85,2.6,-2.7]},measure:[[-2.8,1.45,-15],[-2.8,1.45,15]],label:'300 m',focus:[0,2.8,-3.5]},
 wind:{name:'TURBINA EÓLICA',bounds:{min:[-5.2,0,-1.4],max:[5.2,15.2,2]},detail:{min:[-.9,-.02,-.65],max:[1.25,1.65,.65]},measure:[[1.0,0,0],[1.0,10,0]],label:'100 m',focus:[0,10,.5]}
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
 const m=MODELS[id],a=cruise((t-2.6)/4.5),b=cruise((t-7.2)/4.5);
 const yaw=id==='ship'?mix(.41,.58,b):mix(.24,-.12,b);
 const elev=id==='ship'?mix(.83,.96,b):mix(.16,.22,b);
 const detail=fitCamera(m.detail,yaw,elev,.88),whole=fitCamera(m.bounds,yaw,elev,.89);
 const target=mix3(detail.target,whole.target,a),distance=mix(detail.distance,whole.distance,a);
 const dir=new Vector3(Math.sin(yaw)*Math.cos(elev),Math.sin(elev),Math.cos(yaw)*Math.cos(elev));
 const position=new Vector3(...target).addScaledVector(dir,distance).toArray() as V3;
 const camera=new PerspectiveCamera(36,W/H,.05,1000);camera.position.set(...position);camera.lookAt(...target);camera.updateMatrixWorld();camera.updateProjectionMatrix();
 return {camera,position,target,whole:a>=.999,phase:a<.999?'detail':'overview',measureOpacity:cruise((t-7.3)/.65),detailOpacity:cruise((t-.25)/.5)*(1-cruise((t-2.05)/.45))};
}
export function project(cam:PerspectiveCamera,p:V3){const v=new Vector3(...p).project(cam);return {x:(v.x+1)*W/2,y:(1-v.y)*H/2,z:v.z};}

export const DETAIL:Record<CaseId,{measure:[V3,V3];label:string;description:string}>={
 ship:{measure:[[-.20,2.34,-4.61],[-.20,2.34,-3.39]],label:'12,2 m',description:'Contêiner · comprimento nominal'},
 wind:{measure:[[.98,0,.42],[.98,.175,.42]],label:'1,75 m',description:'Pessoa · altura de referência'}
};
