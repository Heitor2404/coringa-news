/** Prova 3D cinematografica multitema: um slider-crank, duas aplicacoes.
 *
 * Mudanca deliberada de linguagem: objeto 3D iluminado em CORTE,
 * em escala dominante no quadro vertical. Nada de SVG do antigo desenho.
 * A cinemática é a MESMA SliderCrankRig.ts e a cena nao contem
 * coordenadas diferentes por tema. UI segura se aplica a TEXTO.
 * Laboratorio privado: nao ha cinemática de valvulas termodinamica aqui.
 */
import React from 'react';
import {AbsoluteFill,useCurrentFrame,useVideoConfig} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {Vector3,Quaternion} from 'three';
import configs from './slider-crank-proofs.json';
import safeRoles from './editorial-safe-roles-v2.json';
import {angleAt,rigState,type RigGeometry} from './SliderCrankRig';

type Focus='piston'|'rod'|'crank'|'intake'|'outlet';
type Driver='pressure'|'shaft';
type Step={at:number;label:string;detail:string;focus:Focus};
type Model={
  id:string;title:[string,string];subtitle:string;section:string;
  driver:Driver;ports:boolean;accent:string;geometry:RigGeometry;
  steps:Step[];footer:string;
};
type Props={kind:'motor'|'compressor';private_review_only?:boolean;duracao?:number};

const P={
  blue:'#1954B4',deep:'#091D3E',cobalt:'#082B61',
  white:'#F8FFFF',aqua:'#65F8EB',gold:'#FFD21F',ice:'#C8F9FF',
};
const clamp=(v:number)=>Math.max(0,Math.min(1,v));
const ease=(v:number)=>{const x=clamp(v);return x*x*(3-2*x);};
const scene=(cfg:RigGeometry,t:number,duration:number)=>{
  // Tradução de eixo: o mesmo estado físico original, sem uma nova
  // timeline que possa descolar a biela do pistão.
  const theta=angleAt(t,duration-.38);
  const s=rigState(theta,cfg);
  const k=0.0096;
  const cr=new Vector3((s.crankPin.x-cfg.centerX)*k,
                       -(s.crankPin.y-cfg.centerY)*k-1.35,0.84);
  const pi=new Vector3(0,
                       -(s.pistonPin.y-cfg.centerY)*k-1.35,0.84);
  return {theta,cr,pi,displacement:s.displacement*k,
    wheelRadius:cfg.radius*k,rodLength:cfg.rodLength*k};
};
const Rod:React.FC<{
 a:Vector3;b:Vector3;radius:number;
 main:string;emphasis:boolean
}>=({a,b,radius,main,emphasis})=>{
  const offset=new Vector3().subVectors(b,a);
  const mid=new Vector3().addVectors(a,b).multiplyScalar(.5);
  const q=new Quaternion().setFromUnitVectors(
    new Vector3(0,1,0),offset.clone().normalize());
  return <group>
    <mesh position={[mid.x,mid.y,mid.z]} quaternion={q}>
      <cylinderGeometry args={[radius,radius,offset.length(),20]}/>
      <meshStandardMaterial color={main} metalness={.70} roughness={.24}/>
    </mesh>
    <mesh position={[mid.x-.055,mid.y+.015,mid.z+.07]} quaternion={q}>
      <cylinderGeometry args={[radius*.18,radius*.18,offset.length()*.88,12]}/>
      <meshStandardMaterial color="#FFF1C0" metalness={.55} roughness={.25}/>
    </mesh>
    {emphasis&&<mesh position={[mid.x,mid.y,mid.z]}>
      <sphereGeometry args={[radius*1.7,16,16]}/>
      <meshBasicMaterial color="#FFE172" transparent opacity={.34}/>
    </mesh>}
  </group>;
};
const Bolt:React.FC<{x:number;y:number;z:number;r?:number}>=
({x,y,z,r=.095})=><group position={[x,y,z]}>
  <mesh>
    <cylinderGeometry args={[r,r,.13,24]}/>
    <meshStandardMaterial color="#EEFFFF" metalness={.82} roughness={.19}/>
  </mesh>
  <mesh position={[0,.075,0]}>
    <cylinderGeometry args={[r*.4,r*.4,.08,6]}/>
    <meshStandardMaterial color="#2A6B8F" metalness={.64} roughness={.33}/>
  </mesh>
</group>;

const Mechanics:React.FC<{model:Model;focus:Focus;t:number;duration:number}>=
({model,focus,t,duration})=>{
 const {theta,cr,pi,displacement,wheelRadius:r}=scene(model.geometry,t,duration);
 const pressure=model.driver==='pressure';
 const down=theta<Math.PI;
 const machineFocus=focus==='piston'||focus==='rod'||focus==='crank';
 const cylinderCenter=1.05;
 const crown=pi.y+.4;
 const headY=2.75;
 const airHeight=Math.max(.08,headY-crown);
 const gasColor=pressure?'#FFAC35':'#7AFFF4';
 const cylinderOpacity=pressure&&down?.30:(!pressure&&!down?.22:.08);
 const ringY=2.62;
 const valveIn=model.ports&&down;
 const valveOut=model.ports&&!down&&theta>Math.PI*1.66;
 const glow=pressure?'#FFB83D':'#71FFE8';
 const isPiston=focus==='piston',isRod=focus==='rod',isCrank=focus==='crank';
 return <group>
   <ambientLight intensity={.65}/>
   <hemisphereLight color="#F9FEFF" groundColor="#04142C" intensity={1.1}/>
   <directionalLight position={[-5,8,9]} intensity={2.8} color="#FFFFFF"/>
   <directionalLight position={[6,-2,-4]} intensity={1.7} color="#77E8FF"/>
   <pointLight position={[-3,3,6]} intensity={pressure?36:28} distance={12}
     decay={2} color={glow}/>
   <pointLight position={[2,-3,4]} intensity={19} distance={11} decay={2} color="#9BEFFC"/>

   {/* Corpo industrial em volume: importante mesmo abaixo da legenda social,
       mas nenhuma informação textual obrigatória vive nesta região. */}
   <mesh position={[0,-1.54,-.66]}>
     <boxGeometry args={[4.35,3.25,1.05]}/>
     <meshStandardMaterial color="#17486E" metalness={.75} roughness={.34}/>
   </mesh>
   <mesh position={[0,-1.63,-.09]}>
     <boxGeometry args={[3.76,2.55,.18]}/>
     <meshStandardMaterial color="#0D294C" metalness={.58} roughness={.44}/>
   </mesh>
   <mesh position={[0,-3.2,-.45]}>
     <boxGeometry args={[4.55,.22,1.34]}/>
     <meshStandardMaterial color="#3D586F" metalness={.75} roughness={.32}/>
   </mesh>
   {[-1,1].map(side=><group key={side}>
     <mesh position={[side*1.65,-1.58,.32]}>
       <boxGeometry args={[.22,2.8,.28]}/>
       <meshStandardMaterial color="#5C6E80" metalness={.76} roughness={.27}/>
     </mesh>
     <mesh position={[side*1.55,1.2,-.28]}>
       <boxGeometry args={[.32,3.2,.34]}/>
       <meshStandardMaterial color="#657D8F" metalness={.72} roughness={.28}/>
     </mesh>
     {[-2.55,-1.35,.12,1.70].map(y=><mesh key={y} position={[side*1.77,y,.34]}>
       <boxGeometry args={[.14,.11,.15]}/>
       <meshStandardMaterial color="#7E9EAE" metalness={.72} roughness={.28}/>
     </mesh>)}
   </group>)}
   {/* Disco + aro 3D, geometria articulada pelo mesmo ângulo θ. */}
   <group position={[0,-1.35,.42]} rotation={[0,0,-theta]}>
     <mesh rotation={[Math.PI/2,0,0]}>
       <cylinderGeometry args={[1.23,1.23,.25,64]}/>
       <meshStandardMaterial color="#46586B" metalness={.76} roughness={.27}/>
     </mesh>
     <mesh position={[0,0,.15]}>
       <torusGeometry args={[1.20,.085,14,72]}/>
       <meshStandardMaterial color="#BAC9D3" metalness={.78} roughness={.27}/>
     </mesh>
     {[0,1,2,3,4].map(i=>{
       const a=i*2*Math.PI/5;
       return <group key={i} rotation={[0,0,a]}>
         <mesh position={[0,.64,.24]}>
           <boxGeometry args={[.24,.91,.17]}/>
           <meshStandardMaterial color="#8CA5B6" metalness={.74} roughness={.28}/>
         </mesh>
       </group>;
     })}
     <mesh position={[0,0,.3]}>
       <cylinderGeometry args={[.27,.27,.38,32]}/>
       <meshStandardMaterial color="#C3FFFF" metalness={.85} roughness={.16}/>
     </mesh>
     {/* Braço excêntrico: girado com o mesmo grupo que o volante. */}
     <mesh position={[0,r*.52,.41]}>
       <boxGeometry args={[.28,r+.14,.18]}/>
       <meshStandardMaterial color="#E9B960" metalness={.74} roughness={.23}/>
     </mesh>
   </group>

   {/* Cilindro cortado: estrutura lateral e PAREDE TRASEIRA, centro visível. */}
   <mesh position={[0,1.10,-.30]}>
     <cylinderGeometry args={[1.14,1.14,3.32,64,1,true,0,Math.PI]}/>
     <meshStandardMaterial color="#8CBED1" transparent opacity={.57}
       metalness={.65} roughness={.30} side={2}/>
   </mesh>
   <mesh position={[0,1.10,.06]}>
     <cylinderGeometry args={[1.21,1.21,3.35,64,1,true,Math.PI*.87,Math.PI*.28]}/>
     <meshStandardMaterial color="#E7FCFF" transparent opacity={.17}
       metalness={.30} roughness={.12} side={2}/>
   </mesh>
   {[-1,1].map(i=><group key={i}>
     <mesh position={[i*1.07,1.06,.28]}>
       <boxGeometry args={[.21,3.65,.23]}/>
       <meshStandardMaterial color="#A7BDC9" metalness={.79} roughness={.28}/>
     </mesh>
     {[-.6,1.85,2.63].map(y=><mesh key={y} position={[i*1.13,y,.44]}>
       <sphereGeometry args={[.10,16,12]}/>
       <meshStandardMaterial color="#FFFEF3" metalness={.87} roughness={.20}/>
     </mesh>)}
   </group>)}
   {/* Sem argolas soltas ao redor do pistao: bordas sao do bloco. */}
   {/* Cabeçote bem destacado (sem atrapalhar a zona segura do título). */}
   <mesh position={[0,2.77,-.10]}>
     <boxGeometry args={[2.92,.45,1.82]}/>
     <meshStandardMaterial color="#536E86" metalness={.77} roughness={.31}/>
   </mesh>
   <mesh position={[0,3.08,-.10]}>
     <boxGeometry args={[2.65,.22,1.55]}/>
     <meshStandardMaterial color="#C3CFD8" metalness={.78} roughness={.24}/>
   </mesh>
   {[-1.05,1.05].map(x=><Bolt key={x} x={x} y={3.24} z={.42}/>)}

   {/* Câmara de gás vinculada à altura do pistão, apenas visualização.
       Não é simulação de pressão ou termodinâmica. */}
   <mesh position={[0,crown+airHeight/2,-.24]}>
     <cylinderGeometry args={[.96,.96,airHeight,36]}/>
     <meshBasicMaterial color={gasColor} transparent opacity={cylinderOpacity}
       depthWrite={false}/>
   </mesh>
   {/* Pistão 3D e anéis de vedação. */}
   <group position={[0,pi.y+.03,.35]}>
     <mesh position={[0,.30,0]}>
       <cylinderGeometry args={[.92,.92,.82,48]}/>
       <meshStandardMaterial color={isPiston?'#FFF5C8':'#D5EDF0'}
         metalness={.68} roughness={.23} emissive={isPiston?'#FAD861':'#214D60'}
         emissiveIntensity={isPiston?.20:.06}/>
     </mesh>
     <mesh position={[0,.71,0]}>
       <cylinderGeometry args={[.94,.94,.12,48]}/>
       <meshStandardMaterial color="#EEFFFC" metalness={.80} roughness={.16}/>
     </mesh>
     {[.13,.29].map(y=><mesh key={y} position={[0,y,0]}>
       <torusGeometry args={[.95,.053,12,48]}/>
       <meshStandardMaterial color="#15506D" metalness={.85} roughness={.24}/>
     </mesh>)}
     <mesh position={[0,-.09,.64]} rotation={[Math.PI/2,0,0]}>
       <cylinderGeometry args={[.29,.29,.24,30]}/>
       <meshStandardMaterial color="#1F6B86" metalness={.78} roughness={.24}/>
     </mesh>
   </group>
   {/* Biela e articulações: cálculo da mesma origem, sem keyframes soltos. */}
   <Rod a={pi} b={cr} radius={isRod?.22:.17}
     main={isRod?'#FFD27B':'#CA853F'} emphasis={isRod}/>
   {[pi,cr].map((point,i)=><group key={i}
       position={[point.x,point.y,point.z+.11]}>
     <mesh rotation={[Math.PI/2,0,0]}>
       <cylinderGeometry args={[.28,.28,.26,32]}/>
       <meshStandardMaterial color="#0D496B" metalness={.77} roughness={.24}/>
     </mesh>
     <mesh position={[0,0,.16]}>
       <torusGeometry args={[.21,.06,10,32]}/>
       <meshStandardMaterial color="#F9F9DA" metalness={.75} roughness={.22}/>
     </mesh>
   </group>)}
   {/* Fixador de eixos; brilho só no ator ativo. */}
   {isCrank&&<mesh position={[0,-1.35,1.0]}>
     <torusGeometry args={[1.5,.05,12,72]}/>
     <meshBasicMaterial color="#FFE26B" transparent opacity={.76}/>
   </mesh>}

   {/* Compresor: dutos tridimensionais fora do eixo e setas apenas do fluxo.
       As válvulas são ilustração simples, não módulo físico aprovado. */}
   {model.ports&&<group>
     {[-1,1].map(side=><group key={side}>
       <mesh position={[side*1.9,2.93,-.22]} rotation={[0,0,Math.PI/2]}>
         <cylinderGeometry args={[.22,.22,1.52,24]}/>
         <meshStandardMaterial color={side<0?'#66F8EE':'#F8C16C'}
           metalness={.63} roughness={.27} transparent opacity={.88}/>
       </mesh>
       <mesh position={[side*1.09,2.77,.52]}>
         <boxGeometry args={[.30,.12,.45]}/>
         <meshStandardMaterial
           color={(side<0&&valveIn)||(side>0&&valveOut)?'#FFE067':'#194767'}
           metalness={.6} roughness={.25}/>
       </mesh>
     </group>)}
     <mesh position={[-2.7,2.93,.0]} rotation={[0,0,Math.PI/2]}>
       <coneGeometry args={[.23,.58,20]}/>
       <meshBasicMaterial color="#5CFBED" transparent opacity={valveIn?.95:.20}/>
     </mesh>
     <mesh position={[2.7,2.93,.0]} rotation={[0,0,-Math.PI/2]}>
       <coneGeometry args={[.23,.58,20]}/>
       <meshBasicMaterial color="#FFD35E" transparent opacity={valveOut?.95:.20}/>
     </mesh>
   </group>}
 </group>;
};

export const CinematicCutaway3D:React.FC<Props>=({
  kind,private_review_only=true
})=>{
  const frame=useCurrentFrame();
  const {fps}=useVideoConfig();
  const t=frame/fps;
  const model=(configs.models as unknown as Record<string,Model>)[kind]
    ??(configs.models.motor as unknown as Model);
  const stage=model.steps.reduce((idx,s,i)=>t>=s.at?i:idx,0);
  const event=model.steps[stage];
  const changed=t-event.at;
  const appear=ease(changed/.28);
  const opening=1-ease((t-.42)/.52);
  const narrative=ease((t-.68)/.26)*ease((t-event.at)/.28);
  const lead=ease((t-.15)/.85);
  const screen=safeRoles.layout;
  return <AbsoluteFill style={{
     background:'#1765BB',color:'#062341',
     fontFamily:'Inter,Arial,sans-serif',overflow:'hidden',
  }}>
    {/* Fundo full-bleed, não a caixa minuscula de safe zone. */}
    <div style={{position:'absolute',inset:0,
      background:'radial-gradient(ellipse 890px 960px at 50% 52%, #A4F1F2 0%, #42BBD6 32%, #1E84BF 62%, #093D77 100%)'}}/>
    <div style={{position:'absolute',inset:0,opacity:.29,
      background:'repeating-linear-gradient(115deg,transparent 0px,transparent 94px,#EEFFFF 95px,transparent 97px)'}}/>
    <div style={{position:'absolute',left:-215,top:490,width:1500,height:1180,
      borderRadius:'50%',border:'4px solid rgba(232,255,249,.29)',
      boxShadow:'0 0 120px 20px rgba(235,255,248,.19)'}}/>
    {/* Mecanismo domina o canvas. A parte baixa é arte, não legenda. */}
    <ThreeCanvas width={1080} height={1460} orthographic={false}
      style={{position:'absolute',left:0,top:screen.mechanismTop,
        width:1080,height:1460}}
      camera={{position:[4.8,2.3,14.2],fov:29.5,near:.1,far:100}}
      onCreated={({camera})=>{
        camera.lookAt(0,-.40,0);
        camera.updateProjectionMatrix();
      }}>
      <Mechanics model={model} focus={event.focus} t={t}
        duration={configs.duration}/>
    </ThreeCanvas>

    {/* Texto permanece claro na faixa de texto útil.
        Ícones de Reels/TikTok/Shorts NÃO restringem a arte 3D. */}
    <div style={{position:'absolute',top:0,left:0,right:0,height:740,
      background:'linear-gradient(180deg,rgba(242,253,255,.97) 1%,rgba(222,251,254,.90) 58%,rgba(221,249,253,.0) 100%)',
      pointerEvents:'none'}}/>
    <div style={{position:'absolute',left:102,top:screen.brandTop,
      display:'flex',alignItems:'center',gap:12,fontWeight:920,
      fontSize:26,letterSpacing:1.0,opacity:.96,color:'#082945'}}> 
      <span>CORINGA</span>
      <span style={{padding:'5px 9px 3px',color:'#092344',borderRadius:4,
        background:P.gold}}>EXPLICA</span>
    </div>
    <div style={{position:'absolute',left:102,top:screen.headlineTop,
      fontWeight:940,fontSize:66,lineHeight:1.04,letterSpacing:-1.7,
      color:'#082945',maxWidth:825,opacity:opening}}>
      {model.title[0]}
      <div style={{color:'#AE6B02'}}>{model.title[1]}</div>
    </div>
    <div style={{position:'absolute',left:107,top:screen.subtitleTop,
      fontWeight:760,fontSize:28,color:'#236783',
      opacity:opening*lead,maxWidth:760}}>
      {model.subtitle.toUpperCase()}
    </div>

    {/* Faixa de TEXTO protegida no topo. NUNCA cobrir o volante.
        O corpo da maquina usa o restante do quadro 9:16. */}
    <div style={{position:'absolute',left:102,top:screen.eventTop,
      opacity:narrative,
      transform:'translateY('+(1-narrative)*18+'px)',
      zIndex:5,maxWidth:840}}>
      <div style={{fontSize:22,fontWeight:920,color:'#A26703',
        letterSpacing:2.0,marginBottom:15}}>
        {String(stage+1).padStart(2,'0')} / {String(model.steps.length).padStart(2,'0')}
      </div>
      <div style={{fontWeight:960,fontSize:59,lineHeight:1.01,
        maxWidth:820,letterSpacing:-1.1,color:'#092F4E',
        textShadow:'0 2px 10px rgba(249,255,255,.36)'}}>
        {event.label}
      </div>
      <div style={{marginTop:15,fontWeight:720,fontSize:29,
        lineHeight:1.12,maxWidth:810,color:'#225671',
        textShadow:'0 2px 13px rgba(249,255,255,.3)'}}>
        {event.detail}
      </div>
    </div>

    {/* Borda inferior ambiente/movimento: não desperdiçar metade da tela. */}
    <div style={{position:'absolute',left:0,right:0,bottom:0,height:440,
      background:'linear-gradient(0deg,#052D56 0%,rgba(5,55,96,.36) 40%,transparent 100%)',
      pointerEvents:'none'}}/>
    <div style={{position:'absolute',left:100,right:130,bottom:133,height:9,
      background:'rgba(179,242,255,.14)',borderRadius:9}}>
      <div style={{height:'100%',background:P.gold,
        width:(100*clamp(t/configs.duration))+'%',borderRadius:9}}/>
    </div>
    {private_review_only&&<div style={{position:'absolute',right:50,bottom:48,
      fontSize:19,letterSpacing:1.6,fontWeight:750,color:'#9CB5CC'}}>
      PRÉVIA PRIVADA · NÃO PUBLICAR
    </div>}
  </AbsoluteFill>;
};
