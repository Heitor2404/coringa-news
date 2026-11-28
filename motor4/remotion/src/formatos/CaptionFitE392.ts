// Preserve measured word objects, order and highlights; never truncate or shrink.
// An impossible group remains visible and must fail the independent SVG bbox QA.
export function fitCaptionLines<T extends {w:string}>(words:T[],measure:(s:string)=>number,maxWidth:number):T[][] {
  const width=(group:T[])=>measure(group.map(w=>w.w).join(' '));
  if(width(words)<=maxWidth||words.length<2)return [words];
  let best=Infinity,split=1;
  for(let i=1;i<words.length;i++){
    const a=width(words.slice(0,i)),b=width(words.slice(i));
    const overflow=Math.max(0,a-maxWidth)+Math.max(0,b-maxWidth);
    const cost=overflow*1000+Math.max(a,b)+Math.abs(a-b)*.35;
    if(cost<best){best=cost;split=i;}
  }
  return [words.slice(0,split),words.slice(split)];
}
