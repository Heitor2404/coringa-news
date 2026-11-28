/** E397 private spatial benchmark. Existing ThreeCanvas/Three.js renderer.
 * Authored illustrative nominal models, no third-party meshes or exact replica.
 * World scale: 1 scene unit = 10 m. Geometry, labels and camera use same units.
 */
import React,{useMemo} from 'react';
import {AbsoluteFill,Composition,registerRoot,useCurrentFrame,useVideoConfig} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {BufferGeometry,Float32BufferAttribute,Matrix4,Color,InstancedMesh,PerspectiveCamera} from 'three';
import {useThree} from '@react-three/fiber';
import {MODELS,shotAt,project,W,H,FPS,DURATION,type CaseId,type V3} from './formatos/SpatialDirectorE397';
const paint={steel:'#A5A9A7',dark:'#535B61',light:'#D9D9D0',floor:'#54585C',accent:'#C18A56'};
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
const Cargo:React.FC=()=>{
 const items=useMemo(()=>{const a:{p:V3;s:V3;color:string}[]=[];for(let row=0;row<13;row++)for(let col=0;col<7;col++)for(let tier=0;tier<(row===0||row===12?2:3);tier++){if(row===0&&Math.abs(col-3)>1)continue;if(row===12&&Math.abs(col-3)>2)continue;a.push({p:[(col-3)*.49,1.64+tier*.31,-9.5+row*1.48],s:[.455,.29,1.39],color:['#C5C4BC','#919FA1','#A8ADA7','#B6B2A3','#858D91'][(row*11+col*7+tier*3)%5]});}return a;},[]);
 return <instancedMesh args={[undefined,undefined,items.length]} castShadow receiveShadow ref={(m:InstancedMesh|null)=>{if(!m)return;const mat=new Matrix4();items.forEach((b,i)=>{mat.makeScale(...b.s);mat.setPosition(...b.p);m.setMatrixAt(i,mat);m.setColorAt(i,new Color(b.color));});m.instanceMatrix.needsUpdate=true;if(m.instanceColor)m.instanceColor.needsUpdate=true;}}><boxGeometry args={[1,1,1]}/><meshStandardMaterial color="#ffffff" roughness={.83} metalness={.15}/></instancedMesh>;
};
const Ship:React.FC=()=>{const g=useMemo(hull,[]);return <group>
 <mesh geometry={g} castShadow receiveShadow><meshStandardMaterial color="#777F81" metalness={.28} roughness={.66} side={2}/></mesh>
 <Block p={[0,1.36,0]} s={[4.35,.14,23]} color="#4C5356"/>
 <Cargo/>
 <Block p={[0,2.15,-11.8]} s={[3.45,1.4,1.8]} color={paint.light}/>
 <Block p={[0,3.17,-11.8]} s={[3.85,.62,1.5]} color={paint.light}/>
 <Block p={[0,3.20,-10.99]} s={[3.55,.25,.08]} color="#323D45"/>
 <Block p={[.85,3.8,-12.15]} s={[.68,.85,.72]} color="#7A8589"/>
 <Block p={[.85,4.25,-12.15]} s={[.73,.12,.77]} color="#3A4246"/>
 <Block p={[0,4.03,-11.7]} s={[.07,1.0,.07]} color="#C4C8C6"/>
 <Block p={[0,4.39,-11.7]} s={[1.05,.065,.08]} color="#C4C8C6"/>
 {[-1,1].map(side=><React.Fragment key={side}>{Array.from({length:16},(_,i)=><Block key={i} p={[side*2.19,1.53,-11.4+i*1.46]} s={[.055,.28,.055]} color="#B6BBB7"/>)}<Block p={[side*2.19,1.68,0]} s={[.045,.045,23.2]} color="#B6BBB7"/></React.Fragment>)}
 <Block p={[0,1.48,13.1]} s={[.8,.16,.55]} color="#B7B9B1"/>
 {[-1,1].map(x=><mesh key={x} position={[x*.5,1.64,12.8]} castShadow><cylinderGeometry args={[.16,.16,.25,12]}/><meshStandardMaterial color="#9A9B91" roughness={.76}/></mesh>)}
 </group>};
const Blade:React.FC=()=>{const g=useMemo(()=>{const v:number[]=[],idx:number[]=[];const rows=[[.22,.17,.15],[.9,.45,.19],[2.2,.42,.13],[3.6,.28,.085],[4.8,.09,.025],[5,.025,.01]];for(const [r,w,d] of rows)v.push(-w/2,r,-d,w/2,r,-d,w/2,r,d,-w/2,r,d);for(let j=0;j<rows.length-1;j++)for(let k=0;k<4;k++){let a=j*4+k,b=j*4+(k+1)%4;idx.push(a,b,a+4,b,b+4,a+4);}const b=(rows.length-1)*4;idx.push(0,2,1,0,3,2,b,b+1,b+2,b,b+2,b+3);const g=new BufferGeometry();g.setAttribute('position',new Float32BufferAttribute(v,3));g.setIndex(idx);g.computeVertexNormals();return g;},[]);return <mesh geometry={g} castShadow receiveShadow><meshStandardMaterial color="#E0DFD7" roughness={.7} side={2}/></mesh>};
const Wind:React.FC=()=> <group>
 <mesh position={[0,.15,0]} receiveShadow castShadow><cylinderGeometry args={[.83,1.0,.3,40]}/><meshStandardMaterial color="#92928A" roughness={.92}/></mesh>
 <mesh position={[0,5,0]} castShadow receiveShadow><cylinderGeometry args={[.19,.40,10,40]}/><meshStandardMaterial color="#CFD0C9" metalness={.1} roughness={.62}/></mesh>
 <mesh position={[0,10,-.10]} rotation={[Math.PI/2,0,0]} castShadow><capsuleGeometry args={[.36,1.02,6,16]}/><meshStandardMaterial color="#D1D2CB" roughness={.62}/></mesh>
 <group position={[0,10,.91]} rotation={[0,0,.16]}>
  {[0,1,2].map(i=><group key={i} rotation={[0,0,i*Math.PI*2/3]}><Blade/></group>)}
  <mesh rotation={[Math.PI/2,0,0]} castShadow><sphereGeometry args={[.43,24,16]}/><meshStandardMaterial color="#DCDDD6" roughness={.60}/></mesh>
 </group>
 </group>;
const Camera:React.FC<{id:CaseId;t:number}>=({id,t})=>{const {camera}=useThree();const s=shotAt(id,t);camera.position.set(...s.position);camera.lookAt(...s.target);camera.updateMatrixWorld();(camera as PerspectiveCamera).updateProjectionMatrix();return null;};
const Set:React.FC<{id:CaseId;t:number}>=({id,t})=><>
 <Camera id={id} t={t}/>
 <ambientLight intensity={.55}/>
 <hemisphereLight args={['#F4F3E9','#49535C',1.45]}/>
 <directionalLight position={[-24,40,20]} color="#FFF1DB" intensity={2.8} castShadow shadow-mapSize-width={1024} shadow-mapSize-height={1024} shadow-camera-left={-25} shadow-camera-right={25} shadow-camera-top={25} shadow-camera-bottom={-25} shadow-camera-far={120} shadow-bias={-.0004}/>
 <directionalLight position={[18,16,-25]} color="#C7D7E7" intensity={1.25}/>
 <mesh rotation={[-Math.PI/2,0,0]} position={[0,id==='ship'?-1.27:-.025,0]} receiveShadow><planeGeometry args={[180,180]}/><meshStandardMaterial color={paint.floor} roughness={.98}/></mesh>
 {id==='ship'?<Ship/>:<Wind/>}
 </>;
const Preview:React.FC<{kind:CaseId}>=({kind})=>{
 const frame=useCurrentFrame(),{fps}=useVideoConfig(),t=frame/fps,m=MODELS[kind],s=shotAt(kind,t);
 const [a,b]=m.measure.map(p=>project(s.camera,p)),opacity=s.measureOpacity;
 // Measured endpoints use the same camera as the 3D mesh. Label separate
 // from the line to protect readability at mobile size.
 return <AbsoluteFill style={{background:'#53575B',fontFamily:'Inter,Arial,sans-serif',color:'#F4F4EE'}}>
 <ThreeCanvas width={W} height={H} shadows camera={{position:s.position,fov:36,near:.05,far:1000}}><Set id={kind} t={t}/></ThreeCanvas>
 <div style={{position:'absolute',inset:0,pointerEvents:'none',background:'linear-gradient(180deg,rgba(18,21,25,.52),transparent 26%,transparent 72%,rgba(18,21,25,.40))'}}/>
 <div style={{position:'absolute',left:100,top:205,width:440,fontSize:23,fontWeight:700,letterSpacing:1.2,textShadow:'0 2px 6px #222'}}>{m.name}</div>
 <svg width={W} height={H} style={{position:'absolute',inset:0,opacity,pointerEvents:'none'}}><line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#F2D0A0" strokeWidth={1.8}/>{[a,b].map((p,i)=><circle key={i} cx={p.x} cy={p.y} r={3.5} fill="#F2D0A0"/>)}</svg>
 <div style={{position:'absolute',left:100,top:770,opacity,fontSize:34,fontWeight:750,textShadow:'0 2px 5px #25282a'}}>{m.label}<div style={{fontSize:16,fontWeight:500,marginTop:4}}>{kind==='ship'?'comprimento nominal':'altura nominal do cubo'}</div></div>
 <div style={{position:'absolute',left:100,top:832,fontSize:14,color:'#F1F1EA',textShadow:'0 1px 4px #222'}}>Modelo ilustrativo · dimensões de exemplo</div>
 </AbsoluteFill>;
};
registerRoot(()=> <><Composition id="SpatialShip" component={Preview} durationInFrames={DURATION*FPS} fps={FPS} width={W} height={H} defaultProps={{kind:'ship' as CaseId}}/><Composition id="SpatialWind" component={Preview} durationInFrames={DURATION*FPS} fps={FPS} width={W} height={H} defaultProps={{kind:'wind' as CaseId}}/></>);
