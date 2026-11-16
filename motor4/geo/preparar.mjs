// Preparação cartográfica determinística: Natural Earth (domínio público) recortado na região → TopoJSON
// (topojson-server), + rota a partir de geometria COM FONTE (ex.: OpenStreetMap, ODbL) medida com Turf.
// Nunca desenha rota inventada: sem geometria de fonte, a saída registra `rota: null` e o motivo.
//
// uso: node geo/preparar.mjs <pedido.json> <saida.topo.json>
//   pedido = { regiao: [oeste, sul, leste, norte], ne_dir: ".../ne", rota_geojson?: "...", rota_fonte?: "...",
//              rota_unir?: true }
import fs from 'node:fs';
import * as turf from '@turf/turf';
import { topology } from 'topojson-server';

const [, , pedidoArq, saida] = process.argv;
const P = JSON.parse(fs.readFileSync(pedidoArq, 'utf8'));
const [O, S, L, N] = P.regiao;
const caixa = turf.bboxPolygon([O, S, L, N]);
const margem = turf.bboxPolygon([O - 1, S - 1, L + 1, N + 1]);

function camada(nome, filtro = () => true) {
  const arq = `${P.ne_dir}/${nome}.json`;
  if (!fs.existsSync(arq)) return { type: 'FeatureCollection', features: [] };
  const gj = JSON.parse(fs.readFileSync(arq, 'utf8'));
  const out = [];
  for (const f of gj.features) {
    if (!f.geometry || !filtro(f.properties || {})) continue;
    const bb = turf.bbox(f);
    if (bb[2] < O - 1 || bb[0] > L + 1 || bb[3] < S - 1 || bb[1] > N + 1) continue;   // fora da região
    let g = f;
    if (f.geometry.type.includes('Polygon')) {
      try { g = turf.intersect(turf.featureCollection([f, margem])) || null; } catch { g = f; }
    } else if (f.geometry.type.includes('LineString')) {
      try { g = turf.bboxClip(f, [O - 1, S - 1, L + 1, N + 1]); } catch { g = f; }
    }
    if (g) { g.properties = f.properties; out.push(g); }
  }
  return { type: 'FeatureCollection', features: out };
}

const objetos = {
  paises: camada('paises10'),
  lagos: camada('lagos'),
  rios: camada('rios'),
  cidades: camada('cidades', p => (p.scalerank ?? 9) <= 8),
  mares: camada('mares'),
};

let rota = null, motivo = null;
if (P.rota_geojson && fs.existsSync(P.rota_geojson)) {
  const gj = JSON.parse(fs.readFileSync(P.rota_geojson, 'utf8'));
  const linhas = gj.features.filter(f => f.geometry && f.geometry.type.includes('LineString'));
  if (!linhas.length) motivo = 'geometria de rota sem LineString';
  else {
    // une os trechos (ways do OSM) numa linha ordenada: começa pelo extremo mais a NOROESTE (lado Atlântico, se for o
    // caso) e sempre liga o trecho cujo extremo está mais perto da ponta atual — sem inventar vértices
    const segs = linhas.flatMap(f => f.geometry.type === 'MultiLineString' ? f.geometry.coordinates : [f.geometry.coordinates]);
    const pontas = segs.flatMap((s, i) => [[s[0], i, false], [s[s.length - 1], i, true]]);
    const ini = P.rota_inicio ? pontas.reduce((a, b) => turf.distance(b[0], P.rota_inicio) < turf.distance(a[0], P.rota_inicio) ? b : a)
                              : pontas.reduce((a, b) => (b[0][1] - b[0][0] > a[0][1] - a[0][0] ? b : a));
    const usados = new Set([ini[1]]);
    let linha = ini[2] ? [...segs[ini[1]]].reverse() : [...segs[ini[1]]];
    let saltos = [];
    while (usados.size < segs.length) {
      const fim = linha[linha.length - 1];
      let melhor = null;
      for (const [pt, i, ehFim] of pontas) {
        if (usados.has(i)) continue;
        const d = turf.distance(fim, pt);
        if (!melhor || d < melhor[0]) melhor = [d, i, ehFim];
      }
      if (!melhor || melhor[0] > (P.salto_max_km ?? 3)) break;              // não liga trechos distantes
      saltos.push(+melhor[0].toFixed(3));
      usados.add(melhor[1]);
      const s = segs[melhor[1]];
      linha = linha.concat(melhor[2] ? [...s].reverse() : s);
    }
    rota = turf.lineString(linha, { fonte: P.rota_fonte || 'desconhecida', trechos_usados: usados.size, trechos_total: segs.length,
                                    maior_salto_km: Math.max(0, ...saltos) });
    objetos.rota = turf.featureCollection([rota]);
  }
} else motivo = 'sem geometria de rota com fonte (não se desenha linha inventada)';

const topo = topology(objetos, 1e5);
const meta = {
  regiao: P.regiao,
  rota_km: rota ? +turf.length(rota, { units: 'kilometers' }).toFixed(2) : null,
  rota_fonte: rota ? rota.properties.fonte : null,
  rota_trechos: rota ? `${rota.properties.trechos_usados}/${rota.properties.trechos_total}` : null,
  rota_maior_salto_km: rota ? rota.properties.maior_salto_km : null,
  rota_motivo_ausente: motivo,
  contagem: Object.fromEntries(Object.entries(objetos).map(([k, v]) => [k, v.features.length])),
  atribuicao: ['Natural Earth (domínio público)'].concat(rota ? [P.rota_fonte] : []),
};
fs.writeFileSync(saida, JSON.stringify({ topo, meta }));
console.log(JSON.stringify(meta));
