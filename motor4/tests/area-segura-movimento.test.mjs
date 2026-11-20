import test from 'node:test';
import assert from 'node:assert/strict';
import {
  planejarAreaSegura,limitarDestinoSeguro,limitesDoAtor,integralmenteVisivel,areaInterna,
} from '../remotion/src/formatos/AreaSeguraMovimento.ts';

const subject={left:344,top:904,right:621,bottom:1143};
const pivot={x:480,y:1110};
const safe={left:72,top:622,right:1002,bottom:1470};
const low=1110,high=817;
const visible=[{x:180,y:low},{x:489,y:low},{x:489,y:high}];

test('Ciclo completo: mastros e casco dentro da area em TODAS as fases',()=>{
  const plan=planejarAreaSegura(subject,pivot,safe,visible,{minScale:.72});
  assert.ok(plan.scale>.72 && plan.scale<.95);
  const exit=limitarDestinoSeguro(subject,pivot,safe,plan.scale,{x:931,y:high});
  assert.ok(exit.x+(subject.left-pivot.x)*plan.scale>748+16,
    'A saida nao pode ser trocada por simples crop do navio');
  for(let i=0;i<=50;i++){
    const p=i/50;
    // Entrada, permanencia, subida e saida; todos os pontos intermediarios
    // de segmentos monotônicos sao cobertos pelo envelope.
    const poses=[
      {x:180+(489-180)*p,y:low},
      {x:489,y:low+(high-low)*p},
      {x:489+(exit.x-489)*p,y:high},
    ];
    for(const xy of poses){
      const bounds=limitesDoAtor(subject,pivot,xy,plan.scale);
      assert.ok(integralmenteVisivel(bounds,safe),
        'Ator cortado: '+JSON.stringify({xy,bounds,scale:plan.scale}));
    }
  }
});

test('Mesma regra funciona com objeto completamente diferente (balao)',()=>{
  const balloon={left:-95,top:-180,right:95,bottom:55};
  const area={left:80,top:100,right:950,bottom:1510};
  const anchor={x:0,y:0};
  const frames=[{x:300,y:450},{x:600,y:250},{x:800,y:300}];
  const plan=planejarAreaSegura(balloon,anchor,area,frames,{minScale:.7});
  assert.ok(plan.scale>=.7);
  for(const pos of frames){
    assert.ok(integralmenteVisivel(limitesDoAtor(balloon,anchor,pos,plan.scale),area));
  }
});

test('Se objeto gigante nao couber, bloquear em vez de cortar imagem',()=>{
  const gigantic={left:-2000,top:-1200,right:2000,bottom:1200};
  assert.throws(()=>planejarAreaSegura(gigantic,{x:0,y:0},safe,[{x:500,y:920}],
    {minScale:.7}),/AREA-SEGURA-INVIAVEL/);
});

test('Destino pedido fora do quadro e limitado sem esconder atores',()=>{
  const plan=planejarAreaSegura(subject,pivot,safe,visible,{minScale:.72});
  const target=limitarDestinoSeguro(subject,pivot,safe,plan.scale,{x:2000,y:-600});
  assert.ok(target.x<1002 && target.y>622);
  assert.ok(integralmenteVisivel(limitesDoAtor(subject,pivot,target,plan.scale),safe));
});

test('Bloquear area impossivel e dados invalidos',()=>{
  assert.throws(()=>planejarAreaSegura(subject,pivot,
    {left:100,top:200,right:100,bottom:300},visible),/AREA-SEGURA-DADOS/);
  assert.throws(()=>planejarAreaSegura(subject,pivot,safe,[],{}),/AREA-SEGURA-DADOS/);
  assert.throws(()=>planejarAreaSegura(subject,pivot,safe,[{x:NaN,y:100}]),/AREA-SEGURA-DADOS/);
});


test('Area de atores deriva do MESMO recorte SVG, nao de numero independente',()=>{
  const clip={left:61,top:608,right:1018,bottom:1500};
  const derived=areaInterna(clip,{left:11,top:14,right:16,bottom:30});
  assert.deepEqual(derived,safe);
  assert.throws(()=>areaInterna(clip,{left:0,top:0,right:2000,bottom:0}),
    /AREA-SEGURA-MARGEM/);
});
