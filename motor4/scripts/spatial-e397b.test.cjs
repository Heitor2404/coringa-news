const assert=require('node:assert/strict');
const {MODELS,DETAIL,corners,shotAt,project,W,H,DURATION}=require(process.argv[2]);
for(const id of Object.keys(MODELS)){
 let prev;
 for(let i=0;i<DURATION*30;i++){
  const s=shotAt(id,i/30);
  assert(s.position.every(Number.isFinite));
  if(prev)assert(Math.hypot(...s.position.map((v,j)=>v-prev[j]))<1.5,'camera jump');
  prev=s.position;
  if(s.whole)for(const p of corners(MODELS[id].bounds)){
   const q=project(s.camera,p);assert(q.x>=0&&q.x<=W&&q.y>=0&&q.y<=H,'whole object outside frame');
  }
  if(s.detailOpacity>.99)for(const p of DETAIL[id].measure){const q=project(s.camera,p);assert(q.x>=0&&q.x<=W&&q.y>=0&&q.y<=H,'detail measure off-screen');}
  if(s.measureOpacity>.99)for(const p of MODELS[id].measure){const q=project(s.camera,p);assert(q.x>=0&&q.x<=W&&q.y>=0&&q.y<=H,'measure off-screen');}
 }
}
assert.equal(MODELS.ship.measure[1][2]-MODELS.ship.measure[0][2],30);
assert.equal(MODELS.wind.measure[1][1]-MODELS.wind.measure[0][1],10);
assert(Math.abs(DETAIL.ship.measure[1][2]-DETAIL.ship.measure[0][2]-1.22)<1e-9);
assert.equal(DETAIL.wind.measure[1][1],.175);
console.log('E397B camera and nominal dimension checks PASS');
