import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {CausalSequenceView} from './formatos/CausalSequenceE391';
const Root=()=> <Composition id="Causal2D-E391" component={CausalSequenceView as any} width={1080} height={1920} fps={30} durationInFrames={428} calculateMetadata={({props}:any)=>({durationInFrames:Math.round(props.duracao*30)})} defaultProps={{duracao:428/30,private_review_only:true,captions:[]} as any}/>;
registerRoot(Root);
