// Objetos e bichos (desenhados virados para a DIREITA, base em y=0, centro em x=0, largura nominal 100).
// ar = altura/largura; anima(g, d) mexe as partes (d = segundos desde que o objeto apareceu).
const OBJ = {
  barata: { ar: .55, svg: () => `<ellipse cx="0" cy="-2" rx="48" ry="8" fill="url(#gSom)"/><g class="pat">${[0, 1, 2, 3, 4, 5].map(() => `<path class="pt" stroke="${L}" stroke-width="5" fill="none" stroke-linecap="round"/>`).join('')}</g>
     <ellipse cx="0" cy="-26" rx="40" ry="17" fill="#7A3B1E" stroke="${L}" stroke-width="5"/><path d="M-30 -34 Q0 -46 34 -30" stroke="#A65B30" stroke-width="5" fill="none"/>
     <circle cx="40" cy="-26" r="11" fill="#5A2A14" stroke="${L}" stroke-width="4"/><path class="ant" stroke="${L}" stroke-width="3.5" fill="none" stroke-linecap="round"/>`,
    anima: (g, d) => { g.querySelectorAll('.pt').forEach((p, j) => { const lado = j % 2 ? 1 : -1, base = [-22, 0, 22][j >> 1], f = Math.sin(d * 34 + j * Math.PI / 2 + (j >> 1)) * 14; p.setAttribute('d', `M${base} -20 L${base + f * lado * .5 - 6} -8 L${base + f - 10} 0`) });
      const w = Math.sin(d * 20) * 8; g.querySelector('.ant').setAttribute('d', `M48 -32 Q70 ${-62 + w} 96 ${-50 + w} M46 -34 Q62 ${-74 - w} 88 ${-76 - w}`) } },
  rato: { ar: .6, svg: () => `<ellipse cx="0" cy="-2" rx="50" ry="8" fill="url(#gSom)"/><path class="rabo" stroke="#E8A0A8" stroke-width="7" fill="none" stroke-linecap="round"/>
     <g class="pat">${[0, 1, 2, 3].map(() => `<path class="pt" stroke="${L}" stroke-width="6" fill="none" stroke-linecap="round"/>`).join('')}</g>
     <path d="M-46 -22 Q-48 -62 -4 -64 Q30 -64 44 -40 L62 -30 Q60 -18 40 -16 Q10 -8 -30 -10 Q-46 -10 -46 -22Z" fill="#9A9AA6" stroke="${L}" stroke-width="5"/>
     <circle cx="14" cy="-62" r="15" fill="#C8C8D2" stroke="${L}" stroke-width="4"/><circle cx="16" cy="-60" r="7" fill="#E8A0A8"/><circle cx="44" cy="-38" r="4.5" fill="${L}"/><circle cx="62" cy="-29" r="5" fill="#E8A0A8"/>
     <path d="M58 -30 L80 -36 M58 -28 L80 -26" stroke="${L}" stroke-width="2"/>`,
    anima: (g, d) => { g.querySelectorAll('.pt').forEach((p, j) => { const x = [-28, -18, 18, 28][j], f = Math.sin(d * 26 + j * Math.PI) * 10; p.setAttribute('d', `M${x} -14 L${x + f} 0`) });
      const w = Math.sin(d * 8) * 10; g.querySelector('.rabo').setAttribute('d', `M-44 -18 Q-80 ${-10 + w} -110 ${-30 - w}`) } },
  passaro: { ar: .8, svg: () => `<path d="M-6 -4 L-10 -24 M10 -4 L6 -24" stroke="#E0A030" stroke-width="5" stroke-linecap="round"/>
     <path d="M-50 -42 L-80 -50 L-74 -34Z" fill="#4A7FB8" stroke="${L}" stroke-width="4"/><ellipse cx="0" cy="-44" rx="44" ry="26" fill="#8BB8E0" stroke="${L}" stroke-width="5"/><ellipse cx="4" cy="-36" rx="26" ry="14" fill="#E9D8B4"/>
     <circle cx="34" cy="-64" r="20" fill="#8BB8E0" stroke="${L}" stroke-width="5"/><circle cx="40" cy="-68" r="4.5" fill="${L}"/><path d="M52 -64 L68 -60 L52 -56Z" fill="#E0A030" stroke="${L}" stroke-width="3"/>
     <path class="asa" fill="#4A7FB8" stroke="${L}" stroke-width="4"/>`,
    anima: (g, d) => { const a = Math.sin(d * 18) * 22; g.querySelector('.asa').setAttribute('d', `M-16 -52 Q-6 ${-80 - a} 20 -52 Q4 -46 -16 -52Z`) } },
  lixo: { ar: .7, svg: () => `<ellipse cx="0" cy="-2" rx="54" ry="8" fill="url(#gSom)"/>
     <path d="M-50 0 Q-60 -50 -30 -60 L-24 -70 L-14 -60 Q14 -50 6 0Z" fill="#3A3A44" stroke="${L}" stroke-width="5"/><path d="M-6 0 Q-10 -56 22 -64 L28 -74 L36 -62 Q58 -50 52 0Z" fill="#4A6FA8" stroke="${L}" stroke-width="5"/>
     <path d="M-40 -40 Q-30 -46 -24 -36" stroke="#6A6A74" stroke-width="4" fill="none"/><path d="M10 -40 Q22 -48 30 -38" stroke="#7A9AD0" stroke-width="4" fill="none"/>
     <ellipse cx="58" cy="-2" rx="14" ry="5" fill="#B9D6E8" stroke="${L}" stroke-width="3"/><rect x="40" y="-14" width="14" height="12" fill="#E8D6A8" stroke="${L}" stroke-width="3" transform="rotate(20 47 -8)"/>` },
  folhas: { ar: .45, svg: () => `<ellipse cx="0" cy="-2" rx="56" ry="8" fill="url(#gSom)"/>${[[-30, -10, -20, '#B5762F'], [10, -14, 15, '#C9963F'], [-6, -24, -5, '#8E5A23'], [30, -8, 30, '#A8742A'], [-40, -6, -40, '#C9963F'], [6, -34, 10, '#B5762F']].map(([x, y, r, c]) => `<path d="M${x - 22} ${y} Q${x} ${y - 20} ${x + 22} ${y} Q${x} ${y + 10} ${x - 22} ${y}Z" fill="${c}" stroke="${L}" stroke-width="4" transform="rotate(${r} ${x} ${y})"/>`).join('')}` },
  chinelo: { ar: .35, svg: () => `<path d="M-50 0 Q-54 -22 -30 -24 L40 -22 Q56 -20 52 -4 Q50 2 40 2 L-44 2Z" fill="#F4C431" stroke="${L}" stroke-width="5"/><path d="M-6 -22 Q10 -36 24 -22" stroke="#2F7DC0" stroke-width="8" fill="none" stroke-linecap="round"/>` },
  murcha: { ar: 1, svg: () => `<path d="M-40 0 L-34 -36 L34 -36 L40 0Z" fill="#B65F3D" stroke="${L}" stroke-width="5"/><rect x="-42" y="-44" width="84" height="12" rx="4" fill="#C97050" stroke="${L}" stroke-width="4"/>
     <path class="caule" d="M0 -44 Q4 -80 -6 -100 Q-14 -112 -30 -104" stroke="#7A8B3A" stroke-width="8" fill="none" stroke-linecap="round"/>
     <path d="M-30 -104 Q-50 -100 -48 -80 Q-36 -86 -30 -104Z M0 -70 Q22 -70 26 -50 Q8 -54 0 -70Z" fill="#9AA04A" stroke="${L}" stroke-width="4"/>` },
  globo: { ar: 1.05, svg: () => `<rect x="-6" y="-30" width="12" height="30" fill="#8B5A3C" stroke="${L}" stroke-width="4"/><ellipse cx="0" cy="-2" rx="34" ry="8" fill="#8B5A3C" stroke="${L}" stroke-width="4"/>
     <g class="gl"><circle cx="0" cy="-68" r="44" fill="url(#gGlobo)" stroke="${L}" stroke-width="5"/><path d="M-26 -90 Q-6 -100 6 -86 Q12 -72 -2 -66 Q-18 -62 -26 -76Z M10 -58 Q28 -64 34 -48 Q24 -34 12 -40Z" fill="#6AB04A" stroke="${L}" stroke-width="3"/></g>` },
  mosca: { ar: .7, svg: () => `<path class="asa" fill="#DDEFFF" fill-opacity=".75" stroke="${L}" stroke-width="3"/><ellipse cx="0" cy="-40" rx="30" ry="18" fill="#2F3540" stroke="${L}" stroke-width="4"/><circle cx="28" cy="-42" r="14" fill="#2F3540" stroke="${L}" stroke-width="4"/><circle cx="34" cy="-46" r="8" fill="#C0392B"/>`,
    anima: (g, d) => { const a = Math.sin(d * 60) * 14; g.querySelector('.asa').setAttribute('d', `M-6 -52 Q-30 ${-90 - a} -10 ${-92 - a} Q8 -80 -6 -52Z M4 -54 Q10 ${-92 + a} 26 ${-88 + a} Q26 -70 4 -54Z`) } },
  dinheiro: { ar: .55, svg: () => `${[0, 1, 2].map(k => `<rect x="-48" y="${-18 - k * 14}" width="96" height="16" rx="3" fill="${k % 2 ? '#7AC05A' : '#8AD06A'}" stroke="${L}" stroke-width="4"/>`).join('')}<rect x="-14" y="-52" width="28" height="50" fill="#E8D6A8" stroke="${L}" stroke-width="3"/><text x="-34" y="-36" font-family="Poppins" font-weight="800" font-size="18" fill="#2E6A2A">$</text>` },
  pao: { ar: .45, svg: () => `<path d="M-50 0 Q-56 -40 0 -44 Q56 -40 50 0Z" fill="#D9963F" stroke="${L}" stroke-width="5"/><path d="M-24 -30 L-16 -14 M-2 -34 L6 -16 M20 -30 L28 -14" stroke="#F2C27A" stroke-width="6" stroke-linecap="round"/>` },
  gota: { ar: 1.4, svg: () => `<path d="M0 -140 Q46 -70 40 -36 Q34 0 0 0 Q-34 0 -40 -36 Q-46 -70 0 -140Z" fill="#7AC4EE" stroke="${L}" stroke-width="5"/><ellipse cx="-14" cy="-50" rx="8" ry="16" fill="#fff" opacity=".7"/>` },
  fogo: { ar: 1.2, svg: () => `<g class="fg"><path d="M-40 0 Q-54 -50 -20 -90 Q-14 -60 0 -70 Q-4 -100 20 -120 Q22 -80 40 -60 Q56 -30 40 0Z" fill="#F28A2E" stroke="${L}" stroke-width="5"/><path d="M-20 0 Q-26 -30 -6 -50 Q0 -34 10 -44 Q22 -24 18 0Z" fill="#FFD25A"/></g>`,
    anima: (g, d) => { g.querySelector('.fg').setAttribute('transform', `scale(${1 + Math.sin(d * 14) * .05} ${1 + Math.sin(d * 11 + 1) * .08})`) } },
  lagarto: { ar: .4, svg: () => `<ellipse cx="0" cy="-2" rx="60" ry="7" fill="url(#gSom)"/><path class="rabo" stroke="#5EA84A" stroke-width="14" fill="none" stroke-linecap="round"/>
     <g class="pat">${[0, 1, 2, 3].map(() => `<path class="pt" stroke="#4E8A3A" stroke-width="8" fill="none" stroke-linecap="round"/>`).join('')}</g>
     <path d="M-40 -14 Q-36 -36 0 -34 Q30 -34 44 -30 Q62 -28 64 -18 Q60 -10 44 -12 Q20 -6 -20 -8 Q-40 -8 -40 -14Z" fill="#6AC05A" stroke="${L}" stroke-width="5"/><circle cx="50" cy="-24" r="4" fill="${L}"/>
     ${[-20, -4, 12].map(x => `<circle cx="${x}" cy="-24" r="4" fill="#4E8A3A"/>`).join('')}`,
    anima: (g, d) => { g.querySelectorAll('.pt').forEach((p, j) => { const x = [-24, -14, 20, 30][j], f = Math.sin(d * 20 + j * Math.PI) * 10; p.setAttribute('d', `M${x} -10 L${x + f} 0`) });
      const w = Math.sin(d * 6) * 8; g.querySelector('.rabo').setAttribute('d', `M-38 -14 Q-70 ${-6 + w} -110 ${-10 - w}`) } },
  celular: { ar: 1.7, svg: () => `<rect x="-30" y="-110" width="60" height="110" rx="12" fill="#2F3540" stroke="${L}" stroke-width="5"/><rect x="-22" y="-98" width="44" height="80" rx="4" fill="#6AA8E0"/><circle cx="0" cy="-9" r="4" fill="#9AA4AC"/>` },
  nuvem: { ar: .5, svg: () => `<path d="M-50 0 Q-60 -30 -30 -32 Q-24 -60 6 -54 Q26 -70 44 -46 Q66 -44 58 0Z" fill="#fff" stroke="${L}" stroke-width="5"/><path d="M-36 -10 Q0 -2 44 -10" stroke="#D6E6F2" stroke-width="6" fill="none"/>` },
};
