import React from 'react';
import {AbsoluteFill,Audio,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
import {CalderaCutawayE392} from './CalderaCutawayE392';
import {causalAt,type Event} from './CausalTimelineE393';
import {editorialCamera} from './EditorialMotionE394';
type Board=React.ComponentProps<typeof CalderaCutawayE392>['board'];
export type Props={boards:Board[];events:Event[];transitions:number[];duracao:number;private_review_only:boolean;audio:string;captions:{start:number;end:number;words:Board['caption']}[];probe?:boolean};
export const CausalCutawayE393:React.FC<Props>=p=>{
 const t=useCurrentFrame()/useVideoConfig().fps;
 if(!p.private_review_only||p.boards.length!==4||p.events.length!==3)throw Error('E393-PRIVATE');
 const f=causalAt(p.events,p.transitions,p.boards[0].state,t),base=p.boards[f.index];
 const focuses=[{x:242,y:410},{x:230,y:490},{x:204,y:340},{x:205,y:295}],camera=editorialCamera(t,{left:34,top:234,right:453,bottom:590},{left:26,top:231,right:470,bottom:594},focuses[f.index],focuses[Math.max(0,f.index-1)],f.index?p.events[f.index-1].tempo_s:0,1.045);
 const board={...base,camera,state:f.state,time:t,caption:p.captions.find(c=>c.start<=t&&t<c.end)?.words??[]};
 return <AbsoluteFill>{p.audio&&<Audio src={staticFile(p.audio)}/>}<CalderaCutawayE392 board={board} private_review_only probe={p.probe} motion={{progress:f.progress,time:t}}/></AbsoluteFill>;
};
