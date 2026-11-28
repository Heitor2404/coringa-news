/** E397B private spatial benchmark. Existing ThreeCanvas/Three.js renderer.
 * Authored illustrative nominal models, no third-party meshes or exact replica.
 * World scale: 1 scene unit = 10 m. Geometry, labels and camera use same units.
 */
import React,{useMemo,useLayoutEffect,useRef} from 'react';
import {AbsoluteFill,Composition,registerRoot,useCurrentFrame,useVideoConfig} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {BufferGeometry,Float32BufferAttribute,Matrix4,Color,InstancedMesh,PerspectiveCamera,CanvasTexture,MeshStandardMaterial,SRGBColorSpace,RepeatWrapping} from 'three';
import {useThree} from '@react-three/fiber';
import {MODELS,DETAIL,shotAt,project,W,H,FPS,DURATION,type CaseId,type V3} from './formatos/SpatialDirectorE397B';
const paint={steel:'#A5A9A7',dark:'#535B61',light:'#D9D9D0',floor:'#747D82',accent:'#C18A56'};
const Block:React.FC<{p:V3;s:V3;color?:string;metal?:number}>=({p,s,color=paint.steel,metal=.22})=><mesh position={p} castShadow receiveShadow><boxGeometry args={s}/><meshStandardMaterial color={color} metalness={metal} roughness={.72}/></mesh>;
function hull(){
 // Lofted cross sections (closed surface), tapered bow and stern.
 const sections=[[-15,.16],[-14.2,1.25],[-12,2.12],[-9,2.4],[9,2.4],[12,2.14],[14,1.12],[15,.08]];
 const v:number[]=[],idx:number[]=[];
 for(const [z,w] of sections)for(const [x,y] of [[-w*.54,-1.25],[-w,-.50],[-w,1.10],[-w*.91,1.36],[w*.91,1.36],[w,1.10],[w,-.50],[w*.54,-1.25]])v.push(x,y,z);
 for(let j=0;j<sections.length-1;j++)for(let k=0;k<8;k++){const a=j*8+k,b=j*8+(k+1)%8,c=a+8,d=b+8;idx.push(a,b,c,b,d,c);}
 for(let k=1;k<7;k++){idx.push(0,k+1,k);const a=(sections.length-1)*8;idx.push(a,a+k,a+k+1);}
 const g=new BufferGeometry();g.setAttribute('position',new Float32BufferAttribute(v,3));g.setIndex(idx);g.computeVertexNormals();return g;
}
// Deterministic authored ribbed steel surface, no network texture.
function steelTexture(roof:boolean){
 const c=document.createElement('canvas');c.width=256;c.height=128;const ctx=c.getContext('2d')!;
 ctx.fillStyle='#c8c8c8';ctx.fillRect(0,0,256,128);
 for(let x=5;x<254;x+=12){ctx.fillStyle='#949494';ctx.fillRect(x,0,2,128);ctx.fillStyle='#dedede';ctx.fillRect(x+2,0,3,128);}
 ctx.strokeStyle='#777';ctx.lineWidth=4;ctx.strokeRect(2,2,252,124);
 for(let i=0;i<180;i++){const x=(i*73+19)%256,y=(i*31+7)%128;ctx.fillStyle='rgba(44,44,44,.08)';ctx.fillRect(x,y,3+(i%4),1);}
 if(roof){ctx.fillStyle='rgba(255,255,255,.09)';ctx.fillRect(0,0,256,128);}
 const t=new CanvasTexture(c);t.colorSpace=SRGBColorSpace;t.anisotropy=4;return t;
}
const Cargo:React.FC=()=>{
 const items=useMemo(()=>{const a:{p:V3;s:V3;color:string}[]=[];for(let row=0;row<16;row++)for(let col=0;col<15;col++){
 const top=(row===0||row===15)?2:3+((row*7+col*3)%5===0?1:0);
 if((row===0||row===15)&&Math.abs(col-7)>5)continue;
 for(let tier=0;tier<top;tier++)a.push({p:[(col-7)*.255,1.49+tier*.28,-10.25+row*1.25],s:[.244,.268,1.22],color:['#B7C1BF','#828F96','#A4A79D','#B5A68F','#737C80','#9B9E9E'][(row*11+col*7+tier*3)%6]});
 }return a;},[]);
 const mats=useMemo(()=>{const side=steelTexture(false),roof=steelTexture(true);return [side,side,roof,roof,side,side].map(map=>new MeshStandardMaterial({map,color:'#ffffff',roughness:.79,metalness:.11}));},[]);
 const ref=useRef<InstancedMesh>(null);
 useLayoutEffect(()=>{const m=ref.current;if(!m)return;const mat=new Matrix4();items.forEach((b,i)=>{mat.makeScale(...b.s);mat.setPosition(...b.p);m.setMatrixAt(i,mat);m.setColorAt(i,new Color(b.color));});m.instanceMatrix.needsUpdate=true;if(m.instanceColor)m.instanceColor.needsUpdate=true;m.computeBoundingSphere();},[items]);
 return <instancedMesh args={[undefined,mats,items.length]} ref={ref} castShadow receiveShadow><boxGeometry args={[1,1,1]}/></instancedMesh>;
};
// 1.75m reference figure in 10m scene units, not a specific person.
const Human:React.FC<{p:V3}>=({p})=><group position={p}>
 <mesh position={[0,.154,0]} castShadow><sphereGeometry args={[.021,12,10]}/><meshStandardMaterial color="#B87948" roughness={.85}/></mesh>
 <Block p={[0,.101,0]} s={[.044,.069,.027]} color="#C98E53" metal={0}/>
 {[-1,1].map(n=><React.Fragment key={n}><Block p={[n*.012,.031,0]} s={[.018,.062,.022]} color="#343C42" metal={0}/><Block p={[n*.032,.091,0]} s={[.016,.068,.017]} color="#C98E53" metal={0}/></React.Fragment>)}
 </group>;
const Ship:React.FC=()=>{const g=useMemo(hull,[]);return <group>
 <mesh geometry={g} castShadow receiveShadow><meshStandardMaterial color="#53616A" metalness={.18} roughness={.57} side={2}/></mesh>
 <Block p={[0,1.36,0]} s={[4.35,.14,23]} color="#4C5356"/>
 <Cargo/>
 <Human p={[2.02,1.44,-4.0]}/>
 {[-1,1].map(side=><React.Fragment key={'hull'+side}><Block p={[side*2.401,.78,0]} s={[.025,.11,18]} color="#A2AAA8"/>{Array.from({length:8},(_,i)=><Block key={i} p={[side*2.38,.48,-7+i*2]} s={[.025,.045,.23]} color="#303B43"/>)}</React.Fragment>)}
 <Block p={[0,2.15,-11.8]} s={[3.45,1.4,1.8]} color={paint.light}/>
 <Block p={[0,3.17,-11.8]} s={[3.85,.62,1.5]} color={paint.light}/>
 {Array.from({length:10},(_,i)=><Block key={i} p={[-1.58+i*.35,3.20,-10.99]} s={[.28,.22,.08]} color="#283A46"/>)}
 <Block p={[.85,3.8,-12.15]} s={[.68,.85,.72]} color="#7A8589"/>
 <Block p={[.85,4.25,-12.15]} s={[.73,.12,.77]} color="#3A4246"/>
 <Block p={[0,4.03,-11.7]} s={[.07,1.0,.07]} color="#C4C8C6"/>
 <Block p={[0,4.39,-11.7]} s={[1.05,.065,.08]} color="#C4C8C6"/>
 {[-1,1].map(side=><React.Fragment key={side}>{Array.from({length:16},(_,i)=><Block key={i} p={[side*2.19,1.53,-11.4+i*1.46]} s={[.055,.28,.055]} color="#B6BBB7"/>)}<Block p={[side*2.19,1.68,0]} s={[.045,.045,23.2]} color="#B6BBB7"/></React.Fragment>)}
 <Block p={[0,1.48,13.1]} s={[.8,.16,.55]} color="#B7B9B1"/>
 {[-1,1].map(x=><mesh key={x} position={[x*.5,1.64,12.8]} castShadow><cylinderGeometry args={[.16,.16,.25,12]}/><meshStandardMaterial color="#9A9B91" roughness={.76}/></mesh>)}
 </group>};
const Blade:React.FC=()=>{const g=useMemo(()=>{const v:number[]=[],idx:number[]=[];const rows=[[.22,.17,.15],[.9,.45,.19],[2.2,.42,.13],[3.6,.28,.085],[4.8,.09,.025],[5,.025,.01]];for(const [r,w,d] of rows)v.push(-w/2,r,-d,w/2,r,-d,w/2,r,d,-w/2,r,d);for(let j=0;j<rows.length-1;j++)for(let k=0;k<4;k++){let a=j*4+k,b=j*4+(k+1)%4;idx.push(a,b,a+4,b,b+4,a+4);}const b=(rows.length-1)*4;idx.push(0,2,1,0,3,2,b,b+1,b+2,b,b+2,b+3);const g=new BufferGeometry();g.setAttribute('position',new Float32BufferAttribute(v,3));g.setIndex(idx);g.computeVertexNormals();return g;},[]);return <mesh geometry={g} castShadow receiveShadow><meshStandardMaterial color="#E0DFD7" roughness={.7} side={2}/></mesh>};
const Wind:React.FC<{t:number}>=({t})=> <group>
 <Human p={[.98,0,.42]}/>
 <mesh position={[0,.15,0]} receiveShadow castShadow><cylinderGeometry args={[.83,1.0,.3,40]}/><meshStandardMaterial color="#92928A" roughness={.92}/></mesh>
 <mesh position={[0,5,0]} castShadow receiveShadow><cylinderGeometry args={[.19,.40,10,40]}/><meshStandardMaterial color="#E1E1D8" metalness={.06} roughness={.52}/></mesh>
 <Block p={[0,.55,.395]} s={[.12,.26,.018]} color="#777E7F" metal={.1}/>
 <mesh position={[0,10,-.10]} rotation={[Math.PI/2,0,0]} castShadow><capsuleGeometry args={[.36,1.02,6,16]}/><meshStandardMaterial color="#D1D2CB" roughness={.62}/></mesh>
 <group position={[0,10,.91]} rotation={[0,0,.16+t*.56]}>
  {[0,1,2].map(i=><group key={i} rotation={[0,0,i*Math.PI*2/3]}><Blade/></group>)}
  <mesh rotation={[Math.PI/2,0,0]} castShadow><sphereGeometry args={[.43,24,16]}/><meshStandardMaterial color="#DCDDD6" roughness={.60}/></mesh>
 </group>
 </group>;
const Camera:React.FC<{id:CaseId;t:number}>=({id,t})=>{const {camera}=useThree();const s=shotAt(id,t);camera.position.set(...s.position);camera.lookAt(...s.target);camera.updateMatrixWorld();(camera as PerspectiveCamera).updateProjectionMatrix();return null;};
const Set:React.FC<{id:CaseId;t:number}>=({id,t})=><>
 <Camera id={id} t={t}/>
 <color attach="background" args={['#68737B']}/>
 <fog attach="fog" args={['#68737B',36,130]}/>
 <ambientLight intensity={.42}/>
 <hemisphereLight args={['#F4F3E9','#49535C',1.10]}/>
 <directionalLight position={[-24,40,20]} color="#FFF1DB" intensity={2.3} castShadow shadow-radius={4} shadow-mapSize-width={2048} shadow-mapSize-height={2048} shadow-camera-left={-25} shadow-camera-right={25} shadow-camera-top={25} shadow-camera-bottom={-25} shadow-camera-far={120} shadow-bias={-.0004}/>
 <directionalLight position={[18,16,-25]} color="#C7D7E7" intensity={.9}/>
 <mesh rotation={[-Math.PI/2,0,0]} position={[0,id==='ship'?-1.27:-.025,0]} receiveShadow><planeGeometry args={[380,380]}/><meshStandardMaterial color={paint.floor} roughness={.98}/></mesh>
 {id==='ship'?<Ship/>:<Wind t={t}/>}
 </>;
const Preview:React.FC<{kind:CaseId}>=({kind})=>{
 const frame=useCurrentFrame(),{fps}=useVideoConfig(),t=frame/fps,m=MODELS[kind],s=shotAt(kind,t);
 const d=DETAIL[kind],isDetail=t<2.55,measure=isDetail?d.measure:m.measure,opacity=isDetail?s.detailOpacity:s.measureOpacity;
 const [a,b]=measure.map(p=>project(s.camera,p));
 const dx=b.x-a.x,dy=b.y-a.y,len=Math.max(1,Math.hypot(dx,dy)),nx=-dy/len*6,ny=dx/len*6;
 const mx=(a.x+b.x)/2,my=(a.y+b.y)/2;
 return <AbsoluteFill style={{background:'#68737B',fontFamily:'Inter,Arial,sans-serif',color:'#F6F5EF'}}>
 <ThreeCanvas width={W} height={H} shadows camera={{position:s.position,fov:36,near:.05,far:1000}}><Set id={kind} t={t}/></ThreeCanvas>
 <div style={{position:'absolute',inset:0,pointerEvents:'none',background:'linear-gradient(180deg,rgba(14,22,28,.65),transparent 31%,transparent 66%,rgba(14,22,28,.46))'}}/>
 <div style={{position:'absolute',left:100,top:190,width:480,fontSize:19,fontWeight:700,letterSpacing:1.7,textShadow:'0 2px 5px #25282a'}}>{m.name}</div>
 <svg width={W} height={H} style={{position:'absolute',inset:0,opacity,pointerEvents:'none'}}>
 <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#18252D" strokeWidth={5}/>
 <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#F1D3A4" strokeWidth={2.5}/>
 {[a,b].map((p,i)=><line key={i} x1={p.x-nx} y1={p.y-ny} x2={p.x+nx} y2={p.y+ny} stroke="#F1D3A4" strokeWidth={3}/>)}
 <path d={`M${mx} ${my} L${Math.max(110,Math.min(490,mx))} 282 H105`} stroke="#F1D3A4" strokeOpacity=".8" strokeWidth={1.35} fill="none" strokeDasharray="4 5"/>
 </svg>
 <div style={{position:'absolute',left:100,top:222,opacity,fontSize:48,lineHeight:1.05,fontWeight:780,textShadow:'0 2px 7px #18252D'}}>{isDetail?d.label:m.label}</div>
 <div style={{position:'absolute',left:100,top:294,opacity,fontSize:19,fontWeight:600,textShadow:'0 2px 6px #18252D'}}>{isDetail?d.description:kind==='ship'?'Comprimento nominal':'Altura nominal do cubo'}</div>
 <div style={{position:'absolute',left:100,top:815,fontSize:15,color:'#F1F1EA',textShadow:'0 1px 4px #222'}}>Modelo ilustrativo · escala nominal</div>
 </AbsoluteFill>;
};
registerRoot(()=> <><Composition id="SpatialShipB" component={Preview} durationInFrames={DURATION*FPS} fps={FPS} width={W} height={H} defaultProps={{kind:'ship' as CaseId}}/><Composition id="SpatialWindB" component={Preview} durationInFrames={DURATION*FPS} fps={FPS} width={W} height={H} defaultProps={{kind:'wind' as CaseId}}/></>);
