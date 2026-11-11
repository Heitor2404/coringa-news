// Simulação 3D genérica (estilo infográfico low-poly) com Three.js: qualquer objeto é montado com peças básicas,
// e as ações (mover, cair, afundar, explodir, pegar fogo, colidir, quebrar, girar, decolar) são animadas quadro a quadro,
// de forma determinística (o mesmo instante sempre gera a mesma imagem).
import * as THREE from 'three';

const rnd = (seed => () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; });
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const eio = x => { x = clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const lerp = (a, b, k) => a + (b - a) * k;

// ───────── modelos (formas simples, bem acabadas) ─────────
function navio() {
  const g = new THREE.Group();
  const L = 44, B = 5.2, H = 4.2;
  const casco = new THREE.Shape();                      // vista de cima: proa pontuda, popa arredondada
  casco.moveTo(-L / 2, -B / 2); casco.lineTo(L / 2 - 6, -B / 2); casco.quadraticCurveTo(L / 2 - 1, -B / 2 + .3, L / 2, 0);
  casco.quadraticCurveTo(L / 2 - 1, B / 2 - .3, L / 2 - 6, B / 2); casco.lineTo(-L / 2, B / 2);
  casco.absarc(-L / 2, 0, B / 2, Math.PI / 2, Math.PI * 1.5, false);
  const ext = (h, cor, y, esc = 1) => {
    const geo = new THREE.ExtrudeGeometry(casco, { depth: h, bevelEnabled: false });
    geo.rotateX(-Math.PI / 2); geo.translate(0, y, 0); geo.scale(esc, 1, esc);
    return new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: cor, roughness: .6, metalness: .2, flatShading: true }));
  };
  g.add(ext(1.6, 0x8e1c16, -1.4, .985));                // faixa vermelha (abaixo da linha d'água)
  g.add(ext(H, 0x15181f, .2));                          // casco preto
  const branco = new THREE.MeshStandardMaterial({ color: 0xeef1f6, roughness: .5, flatShading: true });
  const deck1 = new THREE.Mesh(new THREE.BoxGeometry(L * .66, 1.3, B * .82), branco); deck1.position.set(-1.5, H + .85, 0); g.add(deck1);
  const deck2 = new THREE.Mesh(new THREE.BoxGeometry(L * .48, 1.1, B * .7), branco); deck2.position.set(-2, H + 2, 0); g.add(deck2);
  const amarelo = new THREE.MeshStandardMaterial({ color: 0xf0b429, roughness: .5, flatShading: true });
  const preto = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: .7 });
  [-11, -4.5, 2, 8.5].forEach(x => {
    const f = new THREE.Mesh(new THREE.CylinderGeometry(.95, 1.05, 5.2, 14), amarelo); f.position.set(x, H + 4.9, 0); f.rotation.z = .12; g.add(f);
    const tp = new THREE.Mesh(new THREE.CylinderGeometry(.97, .97, 1.1, 14), preto); tp.position.set(x + .3, H + 7.1, 0); tp.rotation.z = .12; g.add(tp);
  });
  const mastro = new THREE.MeshStandardMaterial({ color: 0xc9d6ea });
  [[-19, 9], [17, 10]].forEach(([x, h]) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(.12, .15, h, 6), mastro); m.position.set(x, H + h / 2, 0); g.add(m); });
  // janelas acesas (noite)
  const luz = new THREE.MeshStandardMaterial({ color: 0xffe2a0, emissive: 0xffc860, emissiveIntensity: 1.4 });
  const jan = new THREE.InstancedMesh(new THREE.BoxGeometry(.35, .25, .05), luz, 120); let n = 0; const m4 = new THREE.Matrix4();
  for (const lado of [-1, 1]) for (let r = 0; r < 2; r++) for (let i = 0; i < 30; i++) {
    if (n >= 120) break; const x = -17 + i * 1.15, y = r ? H + .85 : H - 1.0, z = lado * (r ? B * .41 + .03 : B / 2 + .03);
    m4.makeTranslation(x, y, z); jan.setMatrixAt(n++, m4);
  }
  jan.count = n; g.add(jan);
  g.userData = { comprimento: L, proa: L / 2, luzes: luz };
  return g;
}

function iceberg(seed = 7) {
  const g = new THREE.Group(), r = rnd(seed);
  const fase = r() * 10;
  const deform = (geo, amp) => {        // deformação suave pela posição: faces vizinhas continuam encostadas
    const p = geo.attributes.position, v = new THREE.Vector3();
    for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i);
      const k = 1 + amp * (Math.sin(v.x * .55 + fase) * Math.cos(v.z * .6 - fase) * .6 + Math.sin(v.y * .8 + v.x * .3 + fase * 2) * .4);
      p.setXYZ(i, v.x * k, v.y * k, v.z * k); }
    geo.computeVertexNormals(); return geo;
  };
  const cima = deform(new THREE.IcosahedronGeometry(6, 2), .35); cima.scale(1.3, 1.35, 1.05); cima.translate(0, 3.6, 0);
  const gelo = new THREE.MeshStandardMaterial({ color: 0xeaf6ff, roughness: .35, metalness: .05, flatShading: true, emissive: 0x2a4a6a, emissiveIntensity: .25 });
  const topo = new THREE.Mesh(cima, gelo); g.add(topo);
  const pico = deform(new THREE.IcosahedronGeometry(4, 1), .3); pico.scale(.8, 2.3, .8); pico.translate(-2.5, 11, -1); g.add(new THREE.Mesh(pico, gelo));
  const pico2 = deform(new THREE.IcosahedronGeometry(3, 1), .3); pico2.scale(.9, 1.7, .8); pico2.translate(4, 8.5, 1); g.add(new THREE.Mesh(pico2, gelo));
  const baixo = deform(new THREE.IcosahedronGeometry(10, 2), .3); baixo.scale(1.3, 1.1, 1.15); baixo.translate(0, -9, 0);
  g.add(new THREE.Mesh(baixo, new THREE.MeshStandardMaterial({ color: 0x9fd2ff, roughness: .4, transparent: true, opacity: .55, flatShading: true })));
  return g;
}

// ───────── peças básicas: o "engenheiro 3D" (IA) monta qualquer objeto com elas ─────────
const COR = c => { try { return new THREE.Color(c || '#c9d3e3'); } catch (e) { return new THREE.Color('#c9d3e3'); } };
function geoPeca(forma, t) {
  const [x, y, z] = t;
  switch (forma) {
    case 'caixa': return new THREE.BoxGeometry(x, y, z);
    case 'esfera': return new THREE.IcosahedronGeometry(Math.max(x, y, z) / 2, 2);
    case 'elipsoide': { const g = new THREE.SphereGeometry(.5, 20, 14); g.scale(x, y, z); return g; }
    case 'cilindro': { const g = new THREE.CylinderGeometry(y / 2, y / 2, x, 16); g.rotateZ(Math.PI / 2); g.scale(1, 1, z / y || 1); return g; }   // deitado no eixo X
    case 'cilindro_v': return new THREE.CylinderGeometry(x / 2, x / 2, y, 16);                                                                // em pé
    case 'cone': { const g = new THREE.ConeGeometry(y / 2, x, 16); g.rotateZ(-Math.PI / 2); g.scale(1, 1, z / y || 1); return g; }          // ponta para +X
    case 'cone_v': return new THREE.ConeGeometry(x / 2, y, 16);
    case 'capsula': { const r = Math.min(y, z) / 2; const g = new THREE.CapsuleGeometry(r, Math.max(.01, x - 2 * r), 6, 14); g.rotateZ(Math.PI / 2); return g; }
    case 'toro': { const g = new THREE.TorusGeometry(x / 2, Math.max(.1, y / 2), 10, 24); return g; }
    case 'cunha': { const sh = new THREE.Shape(); sh.moveTo(-x / 2, 0); sh.lineTo(x / 2, 0); sh.lineTo(-x / 2, y); sh.lineTo(-x / 2, 0);
      const g = new THREE.ExtrudeGeometry(sh, { depth: z, bevelEnabled: false }); g.translate(0, -y / 2, -z / 2); return g; }
    default: return new THREE.BoxGeometry(x, y, z);
  }
}
function montar(pecas) {
  // cada peça fica dentro de um "pivô" (articulação): girar o pivô gira a peça em volta desse ponto (ex.: perna no quadril)
  const g = new THREE.Group();
  (pecas || []).slice(0, 40).forEach((p, i) => {
    const t = (p.tam || [2, 2, 2]).map(v => Math.max(.05, Math.min(400, +v || 1)));
    const mat = new THREE.MeshStandardMaterial({ color: COR(p.cor), roughness: .55, metalness: .1, flatShading: true,
      emissive: p.brilho ? COR(p.cor) : 0x000000, emissiveIntensity: p.brilho ? 1.2 : 0 });
    const m = new THREE.Mesh(geoPeca(String(p.forma || 'caixa').toLowerCase(), t), mat);
    const ps = (p.pos || [0, 0, 0]).map(v => +v || 0), pv = (p.pivo || ps).map(v => +v || 0), r = p.rot || [0, 0, 0];
    const piv = new THREE.Group(); piv.position.set(...pv); piv.name = String(p.id || 'p' + i);
    m.position.set(ps[0] - pv[0], ps[1] - pv[1], ps[2] - pv[2]);
    m.rotation.set((+r[0] || 0) * Math.PI / 180, (+r[1] || 0) * Math.PI / 180, (+r[2] || 0) * Math.PI / 180);
    piv.add(m); g.add(piv);
  });
  return g;
}
// receitas prontas (usadas quando a IA não manda peças)
const RECEITA = {
  dirigivel: [{ forma: 'elipsoide', tam: [60, 13, 13], cor: '#cfc8b8' }, { forma: 'caixa', tam: [9, 2.6, 3.2], pos: [6, -7.6, 0], cor: '#5a4a3a' },
    { forma: 'cunha', tam: [9, 7, .6], pos: [-26, 5, 0], cor: '#b8b0a0' }, { forma: 'cunha', tam: [9, 7, .6], pos: [-26, -5, 0], rot: [180, 0, 0], cor: '#b8b0a0' },
    { forma: 'cunha', tam: [9, 7, .6], pos: [-26, 0, 5], rot: [90, 0, 0], cor: '#b8b0a0' }, { forma: 'cunha', tam: [9, 7, .6], pos: [-26, 0, -5], rot: [-90, 0, 0], cor: '#b8b0a0' }],
  aviao: [{ forma: 'capsula', tam: [30, 3.6, 3.6], cor: '#e9eef7' }, { forma: 'caixa', tam: [6, .5, 30], pos: [1, -.6, 0], cor: '#c9d3e3' },
    { forma: 'cunha', tam: [5, 6, .5], pos: [-13, 3.2, 0], cor: '#c9d3e3' }, { forma: 'caixa', tam: [3.5, .4, 10], pos: [-13, 1, 0], cor: '#c9d3e3' },
    { forma: 'cilindro', tam: [4, 1.8, 1.8], pos: [2, -1.8, 6], cor: '#8a96a8' }, { forma: 'cilindro', tam: [4, 1.8, 1.8], pos: [2, -1.8, -6], cor: '#8a96a8' }],
  submarino: [{ forma: 'capsula', tam: [36, 5, 5], cor: '#2d3a4f' }, { forma: 'caixa', tam: [6, 4, 2.4], pos: [3, 3.6, 0], cor: '#2d3a4f' }],
  torpedo: [{ forma: 'capsula', tam: [8, 1, 1], cor: '#9aa7b8' }, { forma: 'cone', tam: [1.2, 1, 1], pos: [-4.3, 0, 0], rot: [0, 0, 180], cor: '#6b7787' }],
  mina: [{ forma: 'esfera', tam: [4, 4, 4], cor: '#2b2f36' }, ...[0, 1, 2, 3, 4, 5].map(i => ({ forma: 'cilindro_v', tam: [.4, 5.6, .4], rot: [i * 30, 0, i * 60], cor: '#8b96a6' }))],
  bote: [{ forma: 'caixa', tam: [7, 1.4, 2.6], cor: '#ff7a1a' }, { forma: 'caixa', tam: [3, 1, 2], pos: [0, 1.1, 0], cor: '#ffb15c' }],
  predio: [{ forma: 'caixa', tam: [12, 40, 12], pos: [0, 20, 0], cor: '#3a4a66' }],
  carro: [{ forma: 'caixa', tam: [4.4, 1.2, 1.9], pos: [0, .9, 0], cor: '#d63a2f' }, { forma: 'caixa', tam: [2.4, .9, 1.7], pos: [-.2, 1.9, 0], cor: '#bcd6f5' }],
  trem: [{ forma: 'caixa', tam: [22, 4, 3.2], pos: [0, 2.6, 0], cor: '#3d7be0' }, { forma: 'caixa', tam: [22, .6, 3.3], pos: [0, 1.4, 0], cor: '#ffd21f' }],
  foguete: [{ forma: 'cilindro_v', tam: [3, 22, 3], pos: [0, 11, 0], cor: '#e9eef7' }, { forma: 'cone_v', tam: [3, 5, 3], pos: [0, 24.5, 0], cor: '#ff4d4d' }],
  meteoro: [{ forma: 'esfera', tam: [8, 8, 8], cor: '#6b4a32' }],
};

// ───────── efeitos ─────────
const hash = i => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
let _sprite = null;
function sprite() {      // bolinha suave (sem isso as partículas viram quadrados)
  if (_sprite) return _sprite;
  const c = document.createElement('canvas'); c.width = c.height = 64; const x = c.getContext('2d');
  const gr = x.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(.4, 'rgba(255,255,255,.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = gr; x.fillRect(0, 0, 64, 64); _sprite = new THREE.CanvasTexture(c); return _sprite;
}
function particulas(n, aditivo, tam) {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
  geo.setAttribute('color', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
  const p = new THREE.Points(geo, new THREE.PointsMaterial({ size: tam, map: sprite(), vertexColors: true, transparent: true, depthWrite: false,
    blending: aditivo ? THREE.AdditiveBlending : THREE.NormalBlending, opacity: aditivo ? 1 : .55 }));
  p.frustumCulled = false; return p;
}

// ───────── estilo ilustração plana (padrão): cores chapadas, contorno escuro, vista de lado, fundo claro ─────────
const PLANO = {
  dia: { ceu: 0xefe6d6, agua: 0x7fb3d9, aguaFundo: 0x3f6f99, chao: 0xb9a98c, luz: 1 },
  'por-do-sol': { ceu: 0xf3d2b3, agua: 0x6f9cc4, aguaFundo: 0x37587c, chao: 0xa98f72, luz: 1 },
  noite: { ceu: 0x2b3550, agua: 0x35577f, aguaFundo: 0x1b2c45, chao: 0x4a4a52, luz: .75 },
  tempestade: { ceu: 0x6d7480, agua: 0x4c6a86, aguaFundo: 0x26384d, chao: 0x5a5a5a, luz: .8 },
  espaco: { ceu: 0x141a2e, agua: 0x000000, aguaFundo: 0x000000, chao: 0x333333, luz: 1 },
};
let _grad = null;
function gradiente() {          // 3 tons de sombra (visual de desenho, não de foto)
  if (_grad) return _grad;
  const d = new Uint8Array([90, 90, 90, 255, 175, 175, 175, 255, 255, 255, 255, 255]);
  _grad = new THREE.DataTexture(d, 3, 1, THREE.RGBAFormat); _grad.minFilter = _grad.magFilter = THREE.NearestFilter; _grad.needsUpdate = true; return _grad;
}
function desenho(obj) {          // troca o material por "toon" e põe contorno escuro, como ilustração vetorial
  const linhas = [];
  obj.traverse(m => {
    if (!m.isMesh || m.isInstancedMesh) return;
    const c = m.material.color ? m.material.color.clone() : new THREE.Color(0xcccccc);
    const em = m.material.emissiveIntensity > .5;
    m.material = em ? new THREE.MeshBasicMaterial({ color: c }) : new THREE.MeshToonMaterial({ color: c, gradientMap: gradiente(),
      transparent: m.material.transparent, opacity: m.material.opacity });
    const e = new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry, 28), new THREE.LineBasicMaterial({ color: 0x23262d }));
    linhas.push([m, e]);
  });
  linhas.forEach(([m, e]) => m.add(e));
}

// ───────── cenário ─────────
const HORA = {
  noite: { ceu: 0x07122a, nevoa: 0x0b1a36, luz: 0xcfe0ff, li: 2.2, hemi: [0xb5d0ff, 0x0a1428, 1.6], lua: true, est: true },
  dia: { ceu: 0x7fb8ef, nevoa: 0xa9cff2, luz: 0xfff3dc, li: 3, hemi: [0xdfefff, 0x5a6b4a, 1.8] },
  'por-do-sol': { ceu: 0xe9875a, nevoa: 0xd8906a, luz: 0xffc18a, li: 2.6, hemi: [0xffd2b0, 0x3a2a4a, 1.5] },
  tempestade: { ceu: 0x1c222c, nevoa: 0x2a313d, luz: 0x9fb0c8, li: 1.4, hemi: [0x8a99b0, 0x111418, 1.3], chuva: true },
  espaco: { ceu: 0x02030a, nevoa: 0x02030a, luz: 0xffffff, li: 3, hemi: [0x6a7aa0, 0x000000, .6], est: true },
};
// ───────── simulação genérica ─────────
// sc.sim = {ambiente, hora, camera, foco, objetos:[{id, nome, modelo|pecas, pos, rot, escala}], eventos:[{obj, acao, de, ate, para, com, altura, voltas}]}
export function criarSim3D(canvas, sc) {
  const S = sc.sim || {}, W = canvas.width, H = canvas.height;
  const amb = String(S.ambiente || 'mar').toLowerCase(), hora = HORA[String(S.hora || (amb === 'espaco' ? 'espaco' : 'noite')).toLowerCase()] || HORA.noite;
  const ren = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
  ren.setSize(W, H, false); ren.toneMapping = THREE.ACESFilmicToneMapping; ren.toneMappingExposure = 1.15; ren.outputColorSpace = THREE.SRGBColorSpace;
  const plano = String(S.estilo || 'plano') !== '3d';
  const PL = PLANO[String(S.hora || (amb === 'espaco' ? 'espaco' : 'dia')).toLowerCase()] || PLANO.dia;
  const cena = new THREE.Scene(); cena.background = new THREE.Color(plano ? PL.ceu : hora.ceu);
  if (!plano) cena.fog = new THREE.FogExp2(hora.nevoa, amb === 'espaco' ? .0005 : .0035);
  const cam = plano ? new THREE.OrthographicCamera(-50, 50, 50, -50, -2000, 4000) : new THREE.PerspectiveCamera(50, W / H, .5, 3000);
  cena.add(new THREE.HemisphereLight(...hora.hemi));
  const sol = new THREE.DirectionalLight(hora.luz, hora.li); sol.position.set(-60, 90, 70); cena.add(sol);
  const contra = new THREE.DirectionalLight(0x5b9bff, .9); contra.position.set(70, 25, -90); cena.add(contra);
  if (hora.lua) { const l = new THREE.Mesh(new THREE.SphereGeometry(14, 24, 16), new THREE.MeshBasicMaterial({ color: 0xf4f1e2, fog: false })); l.position.set(-200, 260, -700); cena.add(l); }
  if (hora.est) { const e = new Float32Array(1200); for (let i = 0; i < 400; i++) { const a = hash(i) * 6.283, el = .1 + hash(i + 9) * 1.2;
      e.set([Math.cos(a) * 900 * Math.cos(el), 60 + Math.sin(el) * 700, Math.sin(a) * 900 * Math.cos(el) - 300], i * 3); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(e, 3));
    cena.add(new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffffff, size: 1.7, sizeAttenuation: false, fog: false, transparent: true, opacity: .85 }))); }

  // chão / mar
  let marG = null, base = null, linhaMar = null;
  if (plano) {
    cena.children.filter(c => c.isLight).forEach(l => cena.remove(l));
    cena.add(new THREE.AmbientLight(0xffffff, 1.1 * PL.luz)); const sl = new THREE.DirectionalLight(0xffffff, 1.6 * PL.luz); sl.position.set(-30, 60, 80); cena.add(sl);
    cena.children.filter(c => c.isPoints || (c.isMesh && c.geometry.type === 'SphereGeometry')).forEach(c => cena.remove(c));   // sem estrelas/lua de 3D
    if (amb === 'mar') {
      const ag = new THREE.Mesh(new THREE.PlaneGeometry(6000, 3000), new THREE.MeshBasicMaterial({ color: PL.agua, transparent: true, opacity: .62, depthWrite: false }));
      ag.position.set(0, -1500, 60); ag.renderOrder = 5; cena.add(ag);                         // água NA FRENTE: o que afunda aparece por baixo dela
      const fundo = new THREE.Mesh(new THREE.PlaneGeometry(6000, 3000), new THREE.MeshBasicMaterial({ color: PL.aguaFundo }));
      fundo.position.set(0, -1500, -300); cena.add(fundo);
      const lg = new THREE.BufferGeometry(); lg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(3 * 200), 3));
      linhaMar = new THREE.Line(lg, new THREE.LineBasicMaterial({ color: 0x23262d })); linhaMar.position.z = 61; linhaMar.renderOrder = 6; cena.add(linhaMar);
    } else if (amb === 'terra' || amb === 'cidade') {
      const ch = new THREE.Mesh(new THREE.PlaneGeometry(6000, 3000), new THREE.MeshBasicMaterial({ color: PL.chao })); ch.position.set(0, -1500, -50); cena.add(ch);
      const lg = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-3000, 0, 0), new THREE.Vector3(3000, 0, 0)]);
      const l = new THREE.Line(lg, new THREE.LineBasicMaterial({ color: 0x23262d })); l.position.z = -49; cena.add(l);
      if (amb === 'cidade') for (let i = 0; i < 40; i++) { const h = 20 + hash(i) * 60, b = new THREE.Mesh(new THREE.BoxGeometry(16, h, 4), new THREE.MeshBasicMaterial({ color: 0xcfc3ad }));
        b.position.set((i - 20) * 22 + hash(i + 1) * 8, h / 2, -200); cena.add(b); }
    }
    for (let i = 0; i < 6; i++) { const n = new THREE.Mesh(new THREE.CircleGeometry(1, 24), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: plano && PL.luz < 1 ? .15 : .75 }));
      n.scale.set(30 + hash(i) * 30, 9 + hash(i + 2) * 5, 1); n.position.set((i - 3) * 90 + hash(i + 3) * 40, 70 + hash(i + 4) * 60, -500); cena.add(n); }
  } else if (amb === 'mar') {
    marG = new THREE.PlaneGeometry(1400, 1400, 110, 110); marG.rotateX(-Math.PI / 2); base = marG.attributes.position.array.slice();
    cena.add(new THREE.Mesh(marG, new THREE.MeshStandardMaterial({ color: amb === 'mar' && hora === HORA.dia ? 0x1f6fb5 : 0x0f3a6e, roughness: .28, metalness: .35, flatShading: true, transparent: true, opacity: .9 })));
  } else if (amb === 'terra' || amb === 'cidade') {
    const g = new THREE.PlaneGeometry(1400, 1400, 70, 70); g.rotateX(-Math.PI / 2);
    const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i), d = Math.hypot(x, z); p.setY(i, d > 120 ? (Math.sin(x * .02) + Math.cos(z * .025)) * 6 * Math.min(1, (d - 120) / 200) : 0); }
    g.computeVertexNormals();
    cena.add(new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: amb === 'cidade' ? 0x3a3f48 : (hora === HORA.dia ? 0x5d8a3c : 0x2f4a2a), roughness: .9, flatShading: true })));
    if (amb === 'cidade') for (let i = 0; i < 70; i++) { const a = hash(i) * 6.283, d = 70 + hash(i + 3) * 260, h = 15 + hash(i + 5) * 70;
      const b = new THREE.Mesh(new THREE.BoxGeometry(14, h, 14), new THREE.MeshStandardMaterial({ color: 0x4a5670, flatShading: true, emissive: 0x332200, emissiveIntensity: hora === HORA.noite ? .25 : 0 }));
      b.position.set(Math.cos(a) * d, h / 2, Math.sin(a) * d - 40); cena.add(b); }
  } else if (amb === 'ceu') {
    for (let i = 0; i < 40; i++) { const n = new THREE.Mesh(new THREE.IcosahedronGeometry(10 + hash(i) * 14, 1), new THREE.MeshStandardMaterial({ color: 0xffffff, transparent: true, opacity: .75, flatShading: true }));
      n.scale.set(2.2, .7, 1.4); n.position.set((hash(i + 1) - .5) * 700, -40 - hash(i + 2) * 60, (hash(i + 4) - .5) * 600 - 100); cena.add(n); }
  } else if (amb === 'espaco') {
    const pl = new THREE.Mesh(new THREE.IcosahedronGeometry(260, 4), new THREE.MeshStandardMaterial({ color: 0x2f6fd0, roughness: .8, flatShading: true }));
    pl.position.set(0, -330, -150); cena.add(pl);
  }
  const chao = amb === 'mar' || amb === 'terra' || amb === 'cidade' ? 0 : -9999;

  // objetos
  const objs = {};
  (S.objetos || []).slice(0, 5).forEach((o, i) => {
    const id = String(o.id || 'obj' + i), mod = String(o.modelo || '').toLowerCase();
    let g = mod === 'navio' ? navio() : mod === 'iceberg' ? iceberg() : montar(o.pecas && o.pecas.length ? o.pecas : RECEITA[mod] || RECEITA[id] || [{ forma: 'caixa', tam: [6, 6, 6] }]);
    const esc = Math.max(.05, Math.min(20, +o.escala || 1)); g.scale.setScalar(esc);
    const p = o.pos || [0, 0, 0], r = o.rot || [0, 0, 0];
    if (plano) desenho(g);
    const caixa = new THREE.Box3().setFromObject(g), tam = caixa.getSize(new THREE.Vector3());
    cena.add(g);
    objs[id] = { g, nome: o.nome || '', p0: new THREE.Vector3(+p[0] || 0, +p[1] || 0, +p[2] || 0), r0: new THREE.Euler(...r.map(v => (+v || 0) * Math.PI / 180)), tam,
      pecas: g.children.map(m => ({ m, p: m.position.clone(), r: m.rotation.clone() })), pivos: Object.fromEntries(g.children.filter(c => c.name).map(c => [c.name, { g: c, r: c.rotation.clone() }])) };
  });
  const lista = Object.values(objs);
  const D = Math.max(.5, sc.end - sc.start);
  const evs = (S.eventos || []).map(e => ({ ...e, acao: String(e.acao || '').toLowerCase(), de: clamp(+e.de || 0), ate: clamp(e.ate == null ? Math.min(1, (+e.de || 0) + .4) : +e.ate) }))
    .filter(e => objs[e.obj]).sort((a, b) => a.de - b.de);
  // emissores de fogo/fumaça e efeitos de impacto
  const fogo = particulas(500, true, 7), fumaca = particulas(260, false, 26), faisca = particulas(220, true, 2.2), bolha = particulas(140, false, 1.6), poeira = particulas(160, false, 14);
  cena.add(poeira);
  [fogo, fumaca, faisca, bolha].forEach(p => cena.add(p));
  if (plano) { fogo.material.blending = THREE.NormalBlending; fogo.material.size = 9; faisca.material.blending = THREE.NormalBlending; }   // no fundo claro, brilho aditivo some
  const bola = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 2), new THREE.MeshBasicMaterial({ color: 0xffa040, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }));
  cena.add(bola);
  const chuva = hora.chuva ? particulas(900, false, 1.2) : null; if (chuva) cena.add(chuva);
  const impactos = evs.filter(e => ['explodir', 'colidir'].includes(e.acao) || (['cair', 'arremessar'].includes(e.acao) && chao > -999)).map(e => ['cair', 'arremessar'].includes(e.acao) ? e.ate : e.de);

  function estado(o, f) {   // posição/rotação do objeto no instante f (0–1 da cena), aplicando os eventos em ordem
    const p = o.p0.clone(), r = o.r0.clone(); let quebra = 0, expl = 0, fogoK = 0, afund = 0;
    for (const e of evs) { if (objs[e.obj] !== o || f < e.de) continue; const k = clamp((f - e.de) / Math.max(.01, e.ate - e.de));
      if (e.acao === 'mover' && e.para) p.lerp(new THREE.Vector3(+e.para[0] || 0, +e.para[1] || 0, +e.para[2] || 0), eio(k));
      else if (e.acao === 'cair') { const y0 = p.y, alvo = chao > -999 ? o.tam.y * .15 : y0 - 120; p.y = lerp(y0, alvo, k * k); p.x += 12 * k; r.z -= .55 * eio(k); r.x += .15 * k; }
      else if (e.acao === 'afundar') { afund = eio(k); p.y -= o.tam.y * 1.3 * afund; r.z -= .3 * afund; }
      else if (e.acao === 'decolar') p.y += (+e.altura || 60) * eio(k);
      else if (e.acao === 'girar') { const eixo = String(e.eixo || 'y'); r[eixo] += (+e.voltas || 1) * 6.283 * eio(k); }
      else if (e.acao === 'explodir') { expl = Math.max(expl, (f - e.de) * D); quebra = 1; }
      else if (e.acao === 'quebrar') quebra = Math.max(quebra, eio(k) * .5);
      else if (e.acao === 'pegar_fogo' || e.acao === 'fogo') fogoK = Math.max(fogoK, clamp(k * 1.5));
      else if (e.acao === 'colidir' && k > 0) { const sh = clamp(1 - (f - e.de) * D / .4); p.x -= Math.sin(sh * 9) * .6 * sh; }
      else if (e.acao === 'arremessar' || e.acao === 'saltar') {          // voo em arco, girando, até o destino
        const de = p.clone(), para = e.para ? new THREE.Vector3(+e.para[0] || 0, +e.para[1] || 0, +e.para[2] || 0) : de.clone().add(new THREE.Vector3(18, 0, 0));
        p.lerpVectors(de, para, k); p.y += (+e.arco || o.tam.y * 1.5 + 4) * 4 * k * (1 - k);
        if (e.acao === 'arremessar') r.z -= (+e.voltas || .75) * 6.283 * eio(k); }
      else if (e.acao === 'andar' && e.para) p.lerp(new THREE.Vector3(+e.para[0] || 0, +e.para[1] || 0, +e.para[2] || 0), k);
      else if (e.acao === 'deitar' || e.acao === 'tombar') r.z -= (e.lado === 'tras' ? -1 : 1) * Math.PI / 2 * eio(k);
    }
    return { p, r, quebra, expl, fogoK, afund };
  }

  // enquadramento automático (vertical): caixa que contém os objetos no começo e nos destinos
  const pts = []; lista.forEach(o => { pts.push(o.p0.clone()); evs.filter(e => objs[e.obj] === o && e.para).forEach(e => pts.push(new THREE.Vector3(...e.para.map(v => +v || 0)))); });
  const cx = new THREE.Box3().setFromPoints(pts.length ? pts : [new THREE.Vector3()]);
  const centro = cx.getCenter(new THREE.Vector3()), raio = Math.max(3, cx.getSize(new THREE.Vector3()).length() / 2 + Math.max(...lista.map(o => o.tam.length() / 2), 1));
  const foco = objs[S.foco] || lista[0];

  function upd(t) {
    const f = clamp((t - sc.start) / D);
    if (linhaMar) { const p = linhaMar.geometry.attributes.position; for (let i = 0; i < 200; i++) { const x = (i - 100) * 30;
        p.setXYZ(i, x + cam.position.x, Math.sin(x * .05 + t * 2) * .6, 0); } p.needsUpdate = true; }
    if (marG) { const p = marG.attributes.position; for (let i = 0; i < p.count; i++) { const x = base[i * 3], z = base[i * 3 + 2];
        p.setY(i, Math.sin(x * .08 + t * 1.3) * .45 + Math.cos(z * .11 + t * 1.1) * .35 + Math.sin((x + z) * .05 + t * .7) * .3); } p.needsUpdate = true; marG.computeVertexNormals(); }
    let flash = 0, shake = 0; bola.visible = false; bolha.visible = false;
    const pf = fogo.geometry.attributes, pfu = fumaca.geometry.attributes; let nf = 0, nfu = 0;
    lista.forEach((o, oi) => {
      const st = estado(o, f);
      o.g.position.copy(st.p); o.g.rotation.copy(st.r);
      Object.values(o.pivos).forEach(pv => pv.g.rotation.copy(pv.r));
      for (const e of evs) { if (objs[e.obj] !== o || f < e.de) continue; const k = clamp((f - e.de) / Math.max(.01, e.ate - e.de));
        if (e.acao === 'mexer' && o.pivos[e.peca]) { const rot = (e.rot || [0, 0, 0]).map(v => (+v || 0) * Math.PI / 180);
          const w = e.ida_e_volta === false ? eio(k) : (k >= 1 ? 0 : Math.sin(Math.PI * ((k * (+e.repetir || 1)) % 1)));
          const pv = o.pivos[e.peca]; pv.g.rotation.set(pv.r.x + rot[0] * w, pv.r.y + rot[1] * w, pv.r.z + rot[2] * w); }
        if (e.acao === 'andar' && k < 1) Object.entries(o.pivos).forEach(([n, pv], j) => { if (!/perna|pata|leg/i.test(n)) return;
          const sw = Math.sin(t * 9 + (j % 2) * Math.PI) * .45; pv.g.rotation.z = pv.r.z + sw; }); }
      if (amb === 'mar' && st.p.y < 5 && !st.afund) { o.g.position.y += Math.sin(t * 1.2 + oi) * .15; o.g.rotation.x += Math.sin(t * .9 + oi) * .012; }
      // explosão / quebra: as peças se separam
      o.pecas.forEach((pc, j) => { if (!st.quebra) { pc.m.position.copy(pc.p); pc.m.rotation.copy(pc.r); pc.m.visible = true; return; }
        const s = st.expl ? Math.min(2.5, st.expl) : st.quebra * 2, v = new THREE.Vector3(hash(j) - .5, hash(j + 7) * .8, hash(j + 13) - .5).multiplyScalar(o.tam.length() * .9);
        pc.m.position.copy(pc.p).addScaledVector(v, s).add(new THREE.Vector3(0, -6 * s * s, 0)); pc.m.rotation.set(pc.r.x + s * 3 * hash(j + 2), pc.r.y + s * 2, pc.r.z + s * 4 * hash(j + 5)); });
      if (st.expl > 0) { const k = st.expl; bola.visible = true; bola.position.copy(st.p); bola.scale.setScalar(o.tam.length() * .6 * Math.min(1, k / .5) + 2);
        bola.material.opacity = k < 1.6 ? .9 * (1 - k / 1.6) : 0; flash = Math.max(flash, k < .25 ? .7 * (1 - k / .25) : 0); shake = Math.max(shake, clamp(1 - k / .8)); }
      // fogo e fumaça presos ao objeto
      const fk = Math.max(st.fogoK, st.expl > 0 ? clamp(1 - (st.expl - 1) / 3) : 0);
      if (fk > 0) for (let i = 0; i < 140 && nf < 500; i++, nf++) { const ph = (t * (.9 + hash(i) * .8) + hash(i + 11)) % 1;
        const lx = (hash(i + 3) - .5) * o.tam.x * .9, lz = (hash(i + 5) - .5) * o.tam.z * .8;
        pf.position.setXYZ(nf, st.p.x + lx, st.p.y + o.tam.y * (.1 + ph * .9 * fk) , st.p.z + lz);
        const c = plano ? 1 : (1 - ph) * fk; pf.color.setXYZ(nf, c, c * (plano ? .25 + .55 * (1 - ph) : .35 + .4 * (1 - ph)), c * .08); }
      if (fk > 0) for (let i = 0; i < 70 && nfu < 260; i++, nfu++) { const ph = (t * (.25 + hash(i + 4) * .2) + hash(i + 21)) % 1;
        pfu.position.setXYZ(nfu, st.p.x + (hash(i + 8) - .5) * o.tam.x * .7 - ph * 25, st.p.y + o.tam.y * .6 + ph * 45, st.p.z + (hash(i + 9) - .5) * 10);
        const c = .15 + .1 * hash(i); pfu.color.setXYZ(nfu, c * (1 - ph * .5), c * (1 - ph * .5), c * (1 - ph * .5)); }
      if (st.afund > .05 && amb === 'mar') { const pb = bolha.geometry.attributes; bolha.visible = true; bolha.material.opacity = .8;
        for (let i = 0; i < 140; i++) { const ph = (t * (.3 + (i % 7) * .08) + i * .37) % 1; pb.position.setXYZ(i, st.p.x + (hash(i) - .5) * o.tam.x, -6 + ph * 6.5, st.p.z + (hash(i + 1) - .5) * 8); pb.color.setXYZ(i, .8, .9, 1); } pb.position.needsUpdate = pb.color.needsUpdate = true; }
    });
    for (; nf < 500; nf++) pf.position.setXYZ(nf, 0, -9999, 0);
    for (; nfu < 260; nfu++) pfu.position.setXYZ(nfu, 0, -9999, 0);
    pf.position.needsUpdate = pf.color.needsUpdate = pfu.position.needsUpdate = pfu.color.needsUpdate = true;
    // faíscas nos impactos (colidir / chegar ao chão)
    const fa = faisca.geometry.attributes; let viz = false;
    const pd = poeira.geometry.attributes; let vizP = false;
    for (const e of evs) { const ti = (['cair', 'arremessar'].includes(e.acao) ? e.ate : e.de) * D, kk = t - sc.start - ti;
      if (['cair', 'arremessar'].includes(e.acao) && chao > -999 && kk >= 0 && kk < 1.6) { vizP = true; const o = objs[e.obj], c0 = estado(o, f).p, q = kk / 1.6;
        for (let i = 0; i < 160; i++) { const a = hash(i) * 6.283, v = (6 + hash(i + 2) * 10) * (o.tam.length() / 10 + .5);
          pd.position.setXYZ(i, c0.x + Math.cos(a) * v * q, 1 + hash(i + 4) * 4 * q + q * 3, c0.z + Math.sin(a) * v * q);
          const c = (.55 + .2 * hash(i)) * (1 - q); pd.color.setXYZ(i, c * .9, c * .8, c * .65); } }
      if (!['colidir', 'explodir', 'cair', 'arremessar'].includes(e.acao) || kk < 0 || kk > 1.1) continue;
      if (e.acao === 'cair' && chao < -999) continue;
      viz = true; const o = objs[e.obj], st = estado(o, f), alvo = objs[e.com], pc = alvo ? st.p.clone().lerp(estado(alvo, f).p, .5) : st.p, q = kk / 1.1;
      for (let i = 0; i < 220; i++) { const v = [hash(i) * 2 - 1, hash(i + 3) * 1.6, hash(i + 6) * 2 - 1].map(x => x * 16);
        fa.position.setXYZ(i, pc.x + v[0] * q, pc.y + 2 + v[1] * q * 1.2 - 10 * q * q, pc.z + v[2] * q); const c = 1 - q; fa.color.setXYZ(i, c, c * .82, c * .2); }
      flash = Math.max(flash, kk < .22 ? .55 * (1 - kk / .22) : 0); shake = Math.max(shake, clamp(1 - kk / .7)); }
    if (!viz) for (let i = 0; i < 220; i++) fa.color.setXYZ(i, 0, 0, 0);
    if (!vizP) for (let i = 0; i < 160; i++) pd.position.setXYZ(i, 0, -9999, 0);
    pd.position.needsUpdate = pd.color.needsUpdate = true;
    fa.position.needsUpdate = fa.color.needsUpdate = true;
    if (chuva) { const pc = chuva.geometry.attributes; for (let i = 0; i < 900; i++) { const ph = (t * 1.8 + hash(i)) % 1;
        pc.position.setXYZ(i, centro.x + (hash(i + 1) - .5) * 300, 140 - ph * 160, centro.z + (hash(i + 2) - .5) * 300); pc.color.setXYZ(i, .6, .65, .75); }
      pc.position.needsUpdate = pc.color.needsUpdate = true; if (Math.sin(t * 2.3) > .985) flash = Math.max(flash, .35); }
    // câmera: enquadra o que está acontecendo AGORA (mistura com o trajeto todo para não ficar nervosa)
    const agora = new THREE.Box3(); lista.forEach(o => { if (o.g.position.y > -500) agora.expandByPoint(o.g.position); });
    const cAgora = agora.isEmpty() ? centro : agora.getCenter(new THREE.Vector3());
    const rAgora = agora.isEmpty() ? raio : Math.max(3, agora.getSize(new THREE.Vector3()).length() / 2 + Math.max(...lista.map(o => o.tam.length() / 2), 1));
    const alvoC = centro.clone().lerp(S.camera === 'seguir' && foco ? foco.g.position : cAgora, .7);
    const R = lerp(raio, rAgora, .7);
    if (plano) {   // vista de lado (corte), enquadrando na vertical com folga, e zoom lento
      const meiaL = R * lerp(.82, .7, eio(f)), meiaA = meiaL * H / W;
      cam.left = -meiaL; cam.right = meiaL; cam.top = meiaA; cam.bottom = -meiaA; cam.updateProjectionMatrix();
      const cy = Math.max(alvoC.y, chao > -999 ? meiaA * .32 : alvoC.y);
      cam.position.set(alvoC.x + Math.sin(t * 57) * .02 * R * shake, cy + Math.cos(t * 43) * .02 * R * shake, 1000); cam.lookAt(alvoC.x, cy, 0);
      ren.render(cena, cam);
      const rotP = {}; lista.forEach((o, i) => { if (!o.nome) return; const v = o.g.position.clone(); v.y += o.tam.y * .6 + R * .06; const q = v.project(cam);
        rotP[i] = { nome: o.nome, x: (q.x + 1) / 2 * W, y: (1 - q.y) / 2 * H, ok: Math.abs(q.x) < 1.1 && Math.abs(q.y) < 1.1 }; });
      return { flash, rotulos: rotP };
    }
    const ang = S.camera === 'orbita' ? .5 + f * 1.1 : .62, dist = R * lerp(2.35, 1.9, eio(f)), alt = R * (S.camera === 'baixa' ? .18 : .42);
    cam.position.set(alvoC.x + Math.sin(ang) * dist + Math.sin(t * 57) * 1.4 * shake * R / 30, Math.max(chao > -999 ? 2.5 : -999, alvoC.y + alt) + Math.cos(t * 43) * 1.1 * shake * R / 30, alvoC.z + Math.cos(ang) * dist);
    cam.lookAt(alvoC.x, alvoC.y + R * .22, alvoC.z);
    ren.render(cena, cam);
    const rot = {}; lista.forEach((o, i) => { if (!o.nome) return; const v = o.g.position.clone(); v.y += o.tam.y * .95 + R * .04; const q = v.project(cam);
      rot[i] = { nome: o.nome, x: (q.x + 1) / 2 * W, y: (1 - q.y) / 2 * H, ok: q.z < 1 && Math.abs(q.x) < 1.1 && Math.abs(q.y) < 1.1 }; });
    return { flash, rotulos: rot };
  }
  return { upd, impactos: impactos.map(x => sc.start + x * D) };
}
