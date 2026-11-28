/** E389 source-backed staged diagram. No invented physical interpolation. */
export type Box=[number,number,number,number];
export type SourceStage={schema:'coringa.causal.stage.private.v1';publish:false;group:string;stage:number;count:number;sourceSha:string;review:string;panel:Box;title:string;credit:string;scale:'illustrative_not_to_scale';highlights:{at:number;box:Box;label:string;anchorWord:string}[]};
export const validBox=(b:unknown):b is Box=>Array.isArray(b)&&b.length===4&&b.every(v=>typeof v==='number'&&Number.isFinite(v)&&v>=0&&v<=1)&&b[2]>b[0]&&b[3]>b[1];
const nonempty=(v:unknown,n:number)=>typeof v==='string'&&v.trim().length>0&&v.length<=n;
export function validateSourceStage(s:SourceStage,duration:number,asset:string,dimensions:number[]){
 if(!s||s.schema!=='coringa.causal.stage.private.v1'||s.publish!==false||!nonempty(s.group,80)||!Number.isInteger(s.stage)||!Number.isInteger(s.count)||s.count<2||s.count>5||s.stage<0||s.stage>=s.count||!nonempty(s.review,200)||!nonempty(s.title,45)||!nonempty(s.credit,100)||s.scale!=='illustrative_not_to_scale'||!validBox(s.panel)||!Number.isFinite(duration)||duration<2.4)throw Error('E389-STAGE');
 if(!/^[a-f0-9]{64}$/.test(s.sourceSha)||!['.png','.jpg','.webp'].some(x=>asset==='film_editorial/'+s.sourceSha+x)||!Array.isArray(dimensions)||dimensions.length!==2||dimensions.some(v=>!Number.isFinite(v)||v<600))throw Error('E389-SOURCE');
 if(!Array.isArray(s.highlights)||s.highlights.length<1||s.highlights.length>3||s.highlights.some((h,i)=>!validBox(h.box)||!nonempty(h.label,54)||!nonempty(h.anchorWord,30)||!Number.isFinite(h.at)||h.at<0||h.at>duration-.7||(i>0&&h.at<=s.highlights[i-1].at)))throw Error('E389-HIGHLIGHT');
 return s;
}
export function panelGeometry(panel:Box,dimensions:number[]){
 const [x,y,r,b]=panel,[w,h]=dimensions;
 const scale=Math.min(948/((r-x)*w),600/((b-y)*h));
 const width=(r-x)*w*scale,height=(b-y)*h*scale;
 return {x:(1080-width)/2,y:492+(600-height)/2,width,height,scale,offsetX:-x*w*scale,offsetY:-y*h*scale,sourceWidth:w*scale,sourceHeight:h*scale};
}
